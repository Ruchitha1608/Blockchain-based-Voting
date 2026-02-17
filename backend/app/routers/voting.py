"""
Voting router - Voter authentication and vote casting
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
import structlog

from app.database import get_db
from app.config import settings
from app.models.voter import Voter, AuthAttempt, VoteSubmission, AuthMethod, AuthOutcome
from app.models.election import Election, Candidate, ElectionStatus
from app.models.audit import BlockchainTransaction, TxType
from app.middleware.auth import create_voting_session_token, get_current_session
from app.services.crypto import hash_biometric
from app.services.biometric import FaceService, FingerprintService, BiometricAuthError, FACE_AVAILABLE, FINGERPRINT_AVAILABLE
from app.services.blockchain import blockchain_service, BlockchainError

logger = structlog.get_logger()

router = APIRouter(prefix="/api/voting", tags=["Voting"])


# Request schemas
class FaceAuthRequest(BaseModel):
    """Face authentication request"""
    voter_id: str = Field(..., description="Voter ID")
    face_image: str = Field(..., description="Base64 encoded face image")
    election_id: Optional[str] = Field(None, description="Election ID")


class FingerprintAuthRequest(BaseModel):
    """Fingerprint authentication request"""
    voter_id: str = Field(..., description="Voter ID")
    fingerprint_template: str = Field(..., description="Fingerprint template data")
    election_id: Optional[str] = Field(None, description="Election ID")

# In-memory store for used voting session tokens (prevents reuse)
# In production, use Redis for distributed systems
used_tokens: Dict[str, datetime] = {}

# Initialize biometric services (only if available)
face_service = FaceService() if (FaceService and FACE_AVAILABLE) else None
fingerprint_service = FingerprintService() if (FingerprintService and FINGERPRINT_AVAILABLE) else None


def clean_expired_tokens():
    """Remove expired tokens from used_tokens store"""
    now = datetime.utcnow()
    expired = [token for token, exp_time in used_tokens.items() if exp_time < now]
    for token in expired:
        del used_tokens[token]


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def log_auth_attempt(
    db: Session,
    voter_id: str,
    auth_method: AuthMethod,
    outcome: AuthOutcome,
    failure_reason: str = None,
    similarity_score: float = None,
    ip_address: str = None
) -> None:
    """Log authentication attempt to database"""
    try:
        db.execute(
            text("""
                INSERT INTO auth_attempts
                (id, voter_id, auth_method, outcome, failure_reason, similarity_score, ip_address, attempted_at)
                VALUES (:id,
                        (SELECT id FROM voters WHERE voter_id = :voter_id),
                        :auth_method, :outcome, :failure_reason, :similarity_score, :ip_address, NOW())
            """),
            {
                "id": str(uuid.uuid4()),
                "voter_id": voter_id,
                "auth_method": auth_method.value,
                "outcome": outcome.value,
                "failure_reason": failure_reason,
                "similarity_score": similarity_score,
                "ip_address": ip_address
            }
        )
        db.commit()
    except Exception as e:
        logger.error("failed_to_log_auth_attempt", error=str(e))
        db.rollback()


@router.post("/authenticate/face")
async def authenticate_with_face(
    auth_request: FaceAuthRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate voter using face recognition

    Args:
        auth_request: Face authentication request with voter_id, face_image, and election_id

    Returns:
        - auth_token: Voting session JWT (5-minute expiry)
        - voter_details: Name and constituency information
    """
    voter_id = auth_request.voter_id
    face_image = auth_request.face_image
    ip_address = get_client_ip(request)

    # Log the received voter_id for debugging
    logger.info("face_auth_request_received", voter_id=voter_id, ip=ip_address)

    try:
        # Query voter from database
        result = db.execute(
            text("""
                SELECT v.id, v.voter_id, v.full_name, v.constituency_id, v.has_voted,
                       v.face_embedding_hash, v.encrypted_face_embedding, v.biometric_salt,
                       v.failed_auth_count, v.locked_out, v.lockout_at, v.blockchain_voter_id,
                       c.name as constituency_name
                FROM voters v
                JOIN constituencies c ON v.constituency_id = c.id
                WHERE v.voter_id = :voter_id
            """),
            {"voter_id": voter_id}
        )
        voter = result.fetchone()

        if not voter:
            log_auth_attempt(db, voter_id, AuthMethod.FACE, AuthOutcome.FAILURE,
                           "Voter not found", ip_address=ip_address)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voter not found. Please check your voter ID."
            )

        # Check if voter already voted
        if voter.has_voted:
            log_auth_attempt(db, voter_id, AuthMethod.FACE, AuthOutcome.FAILURE,
                           "Already voted", ip_address=ip_address)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already cast your vote in this election."
            )

        # Check if voter is locked out
        if voter.locked_out:
            lockout_time = voter.lockout_at
            lockout_duration = timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            if lockout_time and datetime.utcnow() < lockout_time + lockout_duration:
                remaining = (lockout_time + lockout_duration - datetime.utcnow()).seconds // 60
                log_auth_attempt(db, voter_id, AuthMethod.FACE, AuthOutcome.LOCKOUT,
                               f"Account locked for {remaining} more minutes", ip_address=ip_address)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account locked due to multiple failed attempts. Try again in {remaining} minutes."
                )
            else:
                # Reset lockout if duration has passed
                db.execute(
                    text("UPDATE voters SET locked_out = FALSE, failed_auth_count = 0 WHERE voter_id = :voter_id"),
                    {"voter_id": voter_id}
                )
                db.commit()

        # Check max auth attempts
        if voter.failed_auth_count >= settings.MAX_AUTH_ATTEMPTS:
            # Lock the account
            db.execute(
                text("UPDATE voters SET locked_out = TRUE, lockout_at = NOW() WHERE voter_id = :voter_id"),
                {"voter_id": voter_id}
            )
            db.commit()

            log_auth_attempt(db, voter_id, AuthMethod.FACE, AuthOutcome.LOCKOUT,
                           "Max attempts exceeded", ip_address=ip_address)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Maximum authentication attempts exceeded. Account locked for {settings.LOCKOUT_DURATION_MINUTES} minutes."
            )

        # Decode and process live face image
        try:
            image_bytes = face_service.decode_image(face_image)
            live_embedding = face_service.get_embedding(image_bytes)
        except BiometricAuthError as e:
            log_auth_attempt(db, voter_id, AuthMethod.FACE, AuthOutcome.FAILURE,
                           str(e), ip_address=ip_address)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # Compare embeddings
        matched, similarity_score = face_service.compare_embeddings(
            live_embedding,
            voter.face_embedding_hash,
            voter.encrypted_face_embedding,
            voter.biometric_salt
        )

        if not matched:
            # Increment failed attempt count
            new_count = voter.failed_auth_count + 1
            db.execute(
                text("UPDATE voters SET failed_auth_count = :count WHERE voter_id = :voter_id"),
                {"count": new_count, "voter_id": voter_id}
            )
            db.commit()

            remaining_attempts = settings.MAX_AUTH_ATTEMPTS - new_count
            log_auth_attempt(db, voter_id, AuthMethod.FACE, AuthOutcome.FAILURE,
                           f"Face not matched (similarity: {similarity_score:.4f})",
                           similarity_score, ip_address)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Face authentication failed. {remaining_attempts} attempt(s) remaining."
            )

        # Authentication successful - reset failed attempts
        db.execute(
            text("UPDATE voters SET failed_auth_count = 0 WHERE voter_id = :voter_id"),
            {"voter_id": voter_id}
        )
        db.commit()

        # Get active election
        election_result = db.execute(
            text("""
                SELECT e.id
                FROM elections e
                WHERE e.status = 'active'
                ORDER BY e.created_at DESC
                LIMIT 1
            """)
        )
        election = election_result.fetchone()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active election available."
            )

        # Create voting session token
        session_id = str(uuid.uuid4())
        auth_token = create_voting_session_token(
            voter_id=voter_id,
            election_id=str(election.id),
            constituency_id=str(voter.constituency_id),
            session_id=session_id
        )

        # Log successful authentication
        log_auth_attempt(db, voter_id, AuthMethod.FACE, AuthOutcome.SUCCESS,
                       None, similarity_score, ip_address)

        logger.info("face_authentication_success", voter_id=voter_id, similarity=similarity_score)

        return {
            "success": True,
            "auth_token": auth_token,
            "token_type": "bearer",
            "expires_in": 300,  # 5 minutes
            "constituency_id": str(voter.constituency_id),  # Add constituency_id for frontend
            "voter_details": {
                "name": voter.full_name,
                "constituency": voter.constituency_name,
                "session_id": session_id
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("face_authentication_error", error=str(e), voter_id=voter_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed. Please try again."
        )


@router.post("/authenticate/fingerprint")
async def authenticate_with_fingerprint(
    auth_request: FingerprintAuthRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate voter using fingerprint (fallback method)

    Args:
        auth_request: Fingerprint authentication request with voter_id, fingerprint_template, and election_id

    Returns:
        - auth_token: Voting session JWT (5-minute expiry)
        - voter_details: Name and constituency information
    """
    voter_id = auth_request.voter_id
    fingerprint_data = auth_request.fingerprint_template

    if not FINGERPRINT_AVAILABLE or not fingerprint_service:
        logger.error("fingerprint_service_unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fingerprint authentication is not available. Please use face authentication."
        )

    ip_address = get_client_ip(request)

    try:
        # Query voter from database
        result = db.execute(
            text("""
                SELECT v.id, v.voter_id, v.full_name, v.constituency_id, v.has_voted,
                       v.fingerprint_template_hash, v.encrypted_fingerprint_template, v.biometric_salt,
                       v.failed_auth_count, v.locked_out, v.lockout_at, v.blockchain_voter_id,
                       c.name as constituency_name
                FROM voters v
                JOIN constituencies c ON v.constituency_id = c.id
                WHERE v.voter_id = :voter_id
            """),
            {"voter_id": voter_id}
        )
        voter = result.fetchone()

        if not voter:
            log_auth_attempt(db, voter_id, AuthMethod.FINGERPRINT, AuthOutcome.FAILURE,
                           "Voter not found", ip_address=ip_address)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voter not found. Please check your voter ID."
            )

        # Check if voter already voted
        if voter.has_voted:
            log_auth_attempt(db, voter_id, AuthMethod.FINGERPRINT, AuthOutcome.FAILURE,
                           "Already voted", ip_address=ip_address)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already cast your vote in this election."
            )

        # Check if voter is locked out
        if voter.locked_out:
            lockout_time = voter.lockout_at
            lockout_duration = timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            if lockout_time and datetime.utcnow() < lockout_time + lockout_duration:
                remaining = (lockout_time + lockout_duration - datetime.utcnow()).seconds // 60
                log_auth_attempt(db, voter_id, AuthMethod.FINGERPRINT, AuthOutcome.LOCKOUT,
                               f"Account locked for {remaining} more minutes", ip_address=ip_address)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account locked due to multiple failed attempts. Try again in {remaining} minutes."
                )
            else:
                # Reset lockout if duration has passed
                db.execute(
                    text("UPDATE voters SET locked_out = FALSE, failed_auth_count = 0 WHERE voter_id = :voter_id"),
                    {"voter_id": voter_id}
                )
                db.commit()

        # Check max auth attempts
        if voter.failed_auth_count >= settings.MAX_AUTH_ATTEMPTS:
            # Lock the account
            db.execute(
                text("UPDATE voters SET locked_out = TRUE, lockout_at = NOW() WHERE voter_id = :voter_id"),
                {"voter_id": voter_id}
            )
            db.commit()

            log_auth_attempt(db, voter_id, AuthMethod.FINGERPRINT, AuthOutcome.LOCKOUT,
                           "Max attempts exceeded", ip_address=ip_address)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Maximum authentication attempts exceeded. Account locked for {settings.LOCKOUT_DURATION_MINUTES} minutes."
            )

        # Decode and process live fingerprint
        try:
            fingerprint_bytes = fingerprint_service.decode_image(fingerprint_data)
            live_template = fingerprint_service.process_fingerprint(fingerprint_bytes)
        except BiometricAuthError as e:
            log_auth_attempt(db, voter_id, AuthMethod.FINGERPRINT, AuthOutcome.FAILURE,
                           str(e), ip_address=ip_address)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # Compare templates
        matched, similarity_score = fingerprint_service.compare_fingerprints(
            live_template,
            voter.fingerprint_template_hash,
            voter.encrypted_fingerprint_template,
            voter.biometric_salt
        )

        if not matched:
            # Increment failed attempt count
            new_count = voter.failed_auth_count + 1
            db.execute(
                text("UPDATE voters SET failed_auth_count = :count WHERE voter_id = :voter_id"),
                {"count": new_count, "voter_id": voter_id}
            )
            db.commit()

            remaining_attempts = settings.MAX_AUTH_ATTEMPTS - new_count
            log_auth_attempt(db, voter_id, AuthMethod.FINGERPRINT, AuthOutcome.FAILURE,
                           f"Fingerprint not matched (similarity: {similarity_score:.4f})",
                           similarity_score, ip_address)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Fingerprint authentication failed. {remaining_attempts} attempt(s) remaining."
            )

        # Authentication successful - reset failed attempts
        db.execute(
            text("UPDATE voters SET failed_auth_count = 0 WHERE voter_id = :voter_id"),
            {"voter_id": voter_id}
        )
        db.commit()

        # Get active election
        election_result = db.execute(
            text("""
                SELECT e.id
                FROM elections e
                WHERE e.status = 'active'
                ORDER BY e.created_at DESC
                LIMIT 1
            """)
        )
        election = election_result.fetchone()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active election available."
            )

        # Create voting session token
        session_id = str(uuid.uuid4())
        auth_token = create_voting_session_token(
            voter_id=voter_id,
            election_id=str(election.id),
            constituency_id=str(voter.constituency_id),
            session_id=session_id
        )

        # Log successful authentication
        log_auth_attempt(db, voter_id, AuthMethod.FINGERPRINT, AuthOutcome.SUCCESS,
                       None, similarity_score, ip_address)

        logger.info("fingerprint_authentication_success", voter_id=voter_id, similarity=similarity_score)

        return {
            "success": True,
            "auth_token": auth_token,
            "token_type": "bearer",
            "expires_in": 300,  # 5 minutes
            "constituency_id": str(voter.constituency_id),  # Add constituency_id for frontend
            "voter_details": {
                "name": voter.full_name,
                "constituency": voter.constituency_name,
                "session_id": session_id
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("fingerprint_authentication_error", error=str(e), voter_id=voter_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed. Please try again."
        )


@router.get("/candidates/{constituency_id}")
async def get_candidates(
    constituency_id: str,
    db: Session = Depends(get_db)
):
    """
    Get list of active candidates for a constituency
    Public endpoint - no authentication required

    Args:
        constituency_id: Constituency identifier

    Returns:
        List of candidates with their details
    """
    try:
        # Get active election
        election_result = db.execute(
            text("""
                SELECT e.id
                FROM elections e
                WHERE e.status = 'active'
                ORDER BY e.created_at DESC
                LIMIT 1
            """)
        )
        election = election_result.fetchone()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active election available."
            )

        # Get candidates for constituency
        result = db.execute(
            text("""
                SELECT c.id, c.name, c.party, c.bio, c.on_chain_id,
                       const.name as constituency_name, const.code as constituency_code
                FROM candidates c
                JOIN constituencies const ON c.constituency_id = const.id
                WHERE c.constituency_id = :constituency_id
                  AND c.election_id = :election_id
                  AND c.is_active = TRUE
                ORDER BY c.name ASC
            """),
            {"constituency_id": constituency_id, "election_id": election.id}
        )
        candidates = result.fetchall()

        if not candidates:
            return {
                "constituency_id": constituency_id,
                "candidates": []
            }

        return {
            "constituency_id": constituency_id,
            "constituency_name": candidates[0].constituency_name,
            "constituency_code": candidates[0].constituency_code,
            "candidates": [
                {
                    "id": str(candidate.id),
                    "name": candidate.name,
                    "party": candidate.party,
                    "bio": candidate.bio,
                    "on_chain_id": candidate.on_chain_id
                }
                for candidate in candidates
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_candidates_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve candidates."
        )


class VoteCastRequest(BaseModel):
    """Vote cast request"""
    candidate_id: str = Field(..., description="Candidate ID to vote for")


@router.post("/cast")
async def cast_vote(
    vote_request: VoteCastRequest,
    session_data: dict = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """
    Cast a vote for a candidate
    Requires valid voting session token

    Args:
        vote_request: Vote request with candidate_id
        session_data: Voting session data from JWT token

    Returns:
        - success: Boolean
        - tx_hash: Blockchain transaction hash
        - timestamp: Vote submission timestamp
    """
    voter_id = session_data["voter_id"]
    election_id = session_data["election_id"]
    constituency_id = session_data["constituency_id"]
    session_id = session_data["session_id"]
    candidate_id = vote_request.candidate_id

    # Check if token has been used
    if session_id in used_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This session token has already been used."
        )

    try:
        # Verify voter exists and hasn't voted
        voter_result = db.execute(
            text("""
                SELECT id, voter_id, blockchain_voter_id, has_voted, locked_out
                FROM voters
                WHERE voter_id = :voter_id
            """),
            {"voter_id": voter_id}
        )
        voter = voter_result.fetchone()

        if not voter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voter not found."
            )

        if voter.has_voted:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already cast your vote."
            )

        if voter.locked_out:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is locked."
            )

        # Get candidate details
        candidate_result = db.execute(
            text("""
                SELECT id, on_chain_id, constituency_id, is_active
                FROM candidates
                WHERE id = :candidate_id AND election_id = :election_id
            """),
            {"candidate_id": candidate_id, "election_id": election_id}
        )
        candidate = candidate_result.fetchone()

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found."
            )

        if not candidate.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate is not active."
            )

        # Verify candidate is in voter's constituency
        if str(candidate.constituency_id) != constituency_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate is not in your constituency."
            )

        # Get constituency on-chain ID
        constituency_result = db.execute(
            text("SELECT on_chain_id FROM constituencies WHERE id = :id"),
            {"id": constituency_id}
        )
        constituency = constituency_result.fetchone()

        if not constituency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Constituency not found."
            )

        # Submit vote to blockchain
        try:
            blockchain_result = blockchain_service.submit_vote_on_chain(
                voter_hash=voter.blockchain_voter_id,
                candidate_on_chain_id=candidate.on_chain_id,
                constituency_on_chain_id=constituency.on_chain_id
            )

            tx_hash = blockchain_result["tx_hash"]
            # Ensure tx_hash has 0x prefix for database constraint
            if not tx_hash.startswith("0x"):
                tx_hash = "0x" + tx_hash
            block_number = blockchain_result["block_number"]
            gas_used = blockchain_result["gas_used"]

        except BlockchainError as e:
            logger.error("blockchain_vote_submission_failed", error=str(e), voter_id=voter_id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Blockchain error: {str(e)}"
            )

        # Record vote submission in database
        db.execute(
            text("""
                INSERT INTO vote_submissions
                (id, voter_id, election_id, session_id, tx_hash, block_number, gas_used, submitted_at)
                VALUES (:id, :voter_id, :election_id, :session_id, :tx_hash, :block_number, :gas_used, NOW())
            """),
            {
                "id": str(uuid.uuid4()),
                "voter_id": voter.id,
                "election_id": election_id,
                "session_id": session_id,
                "tx_hash": tx_hash,
                "block_number": block_number,
                "gas_used": gas_used
            }
        )

        # Mark voter as voted
        db.execute(
            text("""
                UPDATE voters
                SET has_voted = TRUE, voted_at = NOW(), vote_tx_hash = :tx_hash
                WHERE voter_id = :voter_id
            """),
            {"tx_hash": tx_hash, "voter_id": voter_id}
        )

        # Record blockchain transaction
        blockchain_tx = BlockchainTransaction(
            election_id=uuid.UUID(election_id),
            tx_type=TxType.CAST_VOTE,
            tx_hash=tx_hash,
            block_number=block_number,
            from_address=blockchain_service.default_account,
            to_address=blockchain_service.voting_booth.address,
            gas_used=gas_used,
            status=True,
            raw_event={
                "voter_id": voter_id,
                "candidate_id": candidate_id,
                "blockchain_voter_id": voter.blockchain_voter_id,
                "constituency_on_chain_id": constituency.on_chain_id
            }
        )
        db.add(blockchain_tx)

        db.commit()

        # Mark token as used
        used_tokens[session_id] = datetime.utcnow() + timedelta(minutes=10)
        clean_expired_tokens()

        logger.info("vote_cast_success", voter_id=voter_id, tx_hash=tx_hash)

        return {
            "success": True,
            "message": "Your vote has been recorded successfully.",
            "tx_hash": tx_hash,
            "block_number": block_number,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("cast_vote_error", error=str(e), voter_id=voter_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cast vote. Please try again."
        )


@router.get("/verify/{tx_hash}")
async def verify_vote(
    tx_hash: str,
    db: Session = Depends(get_db)
):
    """
    Verify a vote on the blockchain

    Args:
        tx_hash: Transaction hash to verify

    Returns:
        Vote verification details
    """
    try:
        # Check if transaction exists in database
        result = db.execute(
            text("""
                SELECT vs.tx_hash, vs.block_number, vs.submitted_at, vs.gas_used,
                       e.name as election_name, e.status as election_status
                FROM vote_submissions vs
                JOIN elections e ON vs.election_id = e.id
                WHERE vs.tx_hash = :tx_hash
            """),
            {"tx_hash": tx_hash}
        )
        vote = result.fetchone()

        if not vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vote transaction not found."
            )

        # Verify on blockchain
        if not blockchain_service.connected:
            return {
                "verified": True,
                "tx_hash": vote.tx_hash,
                "block_number": vote.block_number,
                "timestamp": vote.submitted_at.isoformat(),
                "election": vote.election_name,
                "blockchain_status": "unavailable",
                "note": "Blockchain verification unavailable. Database record exists."
            }

        try:
            # Get transaction receipt from blockchain
            receipt = blockchain_service.web3.eth.get_transaction_receipt(tx_hash)

            if receipt:
                return {
                    "verified": True,
                    "tx_hash": vote.tx_hash,
                    "block_number": vote.block_number,
                    "timestamp": vote.submitted_at.isoformat(),
                    "election": vote.election_name,
                    "blockchain_status": "confirmed",
                    "confirmations": blockchain_service.web3.eth.block_number - receipt["blockNumber"],
                    "gas_used": vote.gas_used
                }
            else:
                return {
                    "verified": False,
                    "tx_hash": vote.tx_hash,
                    "blockchain_status": "not_found",
                    "note": "Transaction not found on blockchain."
                }

        except Exception as blockchain_error:
            logger.error("blockchain_verification_error", error=str(blockchain_error))
            return {
                "verified": True,
                "tx_hash": vote.tx_hash,
                "block_number": vote.block_number,
                "timestamp": vote.submitted_at.isoformat(),
                "election": vote.election_name,
                "blockchain_status": "error",
                "note": "Database record exists but blockchain verification failed."
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("verify_vote_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify vote."
        )

"""
Election management and lifecycle router
Implements complete election workflow: draft -> active -> closed -> finalized
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import structlog

from app.database import get_db
from app.models.election import Election, ElectionStatus, Constituency, Candidate
from app.models.admin import Admin, AdminRole
from app.models.audit import AuditLog, LogAction, BlockchainTransaction, TxType
from app.models.voter import VoteSubmission
from app.schemas.election import (
    ElectionCreate,
    ElectionResponse,
    ElectionUpdate,
    ConstituencyCreate,
    ConstituencyResponse,
    CandidateCreate,
    CandidateResponse
)
from app.middleware.auth import get_current_admin, require_role
from app.services.blockchain import blockchain_service, BlockchainError

logger = structlog.get_logger()

router = APIRouter(prefix="/api/elections", tags=["Elections"])


# Helper function to log audit events
def log_audit(
    db: Session,
    admin: Admin,
    action: LogAction,
    target_table: str,
    target_id: UUID,
    details: dict = None
):
    """Log audit event"""
    audit_log = AuditLog(
        admin_id=admin.id,
        action=action,
        target_table=target_table,
        target_id=target_id,
        details=details
    )
    db.add(audit_log)


# Helper function to log blockchain transactions
def log_blockchain_tx(
    db: Session,
    election_id: UUID,
    tx_type: TxType,
    tx_hash: str,
    from_address: str,
    block_number: int = None,
    gas_used: int = None,
    status: bool = True
):
    """Log blockchain transaction"""
    # Normalize tx_hash: ensure 0x prefix and lowercase
    normalized_hash = None
    if tx_hash:
        try:
            h = str(tx_hash)
            h = h.lower()
            if not h.startswith('0x'):
                h = '0x' + h
            normalized_hash = h
        except Exception:
            normalized_hash = tx_hash

    tx_log = BlockchainTransaction(
        election_id=election_id,
        tx_type=tx_type,
        tx_hash=normalized_hash,
        from_address=from_address,
        block_number=block_number,
        gas_used=gas_used,
        status=status
    )
    db.add(tx_log)


@router.post("", response_model=ElectionResponse, status_code=status.HTTP_201_CREATED)
async def create_election(
    election_data: ElectionCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_role(AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN))
):
    """
    Create a new election (draft state)
    Requires election_administrator or super_admin role
    """
    try:
        # Create election
        election = Election(
            name=election_data.name,
            description=election_data.description,
            status=ElectionStatus.DRAFT.value,
            voting_start_at=election_data.voting_start_at,
            voting_end_at=election_data.voting_end_at,
            created_by=current_admin.id
        )

        db.add(election)
        db.flush()  # Get election.id before commit

        # Log audit event
        log_audit(
            db,
            current_admin,
            LogAction.ELECTION_CREATED,
            "elections",
            election.id,
            {"name": election.name, "status": election.status}
        )

        db.commit()
        db.refresh(election)

        logger.info(
            "election_created",
            election_id=str(election.id),
            name=election.name,
            admin_id=str(current_admin.id)
        )

        return election

    except Exception as e:
        db.rollback()
        logger.error("election_creation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create election: {str(e)}"
        )


@router.patch("/{election_id}", response_model=ElectionResponse)
async def update_election(
    election_id: UUID,
    election_data: ElectionUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_role(AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN))
):
    """
    Update an existing election
    Can only update elections in draft or configured state
    Requires election_administrator or super_admin role
    """
    try:
        # Find the election
        election = db.query(Election).filter(Election.id == election_id).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Election not found"
            )

        # Only allow updates for draft or configured elections
        if election.status not in [ElectionStatus.DRAFT.value, ElectionStatus.CONFIGURED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update election in {election.status} state"
            )

        # Update fields if provided
        update_data = election_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(election, field, value)

        # Log audit event
        log_audit(
            db,
            current_admin,
            LogAction.ELECTION_UPDATED,
            "elections",
            election.id,
            {"updated_fields": list(update_data.keys())}
        )

        db.commit()
        db.refresh(election)

        logger.info(
            "election_updated",
            election_id=str(election.id),
            updated_fields=list(update_data.keys()),
            admin_id=str(current_admin.id)
        )

        return election

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("election_update_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update election: {str(e)}"
        )


@router.get("", response_model=List[ElectionResponse])
async def list_elections(
    status_filter: Optional[ElectionStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    List elections with optional status filter and pagination
    Returns elections based on admin role and election status
    """
    try:
        # Build query
        query = db.query(Election)

        # Apply status filter if provided
        if status_filter:
            query = query.filter(Election.status == status_filter)

        # Apply pagination
        elections = query.order_by(Election.created_at.desc()).offset(skip).limit(limit).all()

        logger.info(
            "elections_listed",
            count=len(elections),
            status_filter=status_filter.value if status_filter else None,
            admin_id=str(current_admin.id)
        )

        return elections

    except Exception as e:
        logger.error("election_list_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list elections: {str(e)}"
        )


@router.get("/stats")
async def get_dashboard_stats(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics

    Returns:
        - total_elections: Total number of elections
        - active_elections: Number of active elections
        - registered_voters: Total number of registered voters
        - total_votes: Total number of votes cast
    """
    try:
        from app.models.voter import Voter

        # Count total elections
        total_elections = db.query(func.count(Election.id)).scalar() or 0

        # Count active elections
        active_elections = db.query(func.count(Election.id)).filter(
            Election.status == ElectionStatus.ACTIVE
        ).scalar() or 0

        # Count registered voters
        registered_voters = db.query(func.count(Voter.id)).scalar() or 0

        # Count total votes cast
        total_votes = db.query(func.count(VoteSubmission.id)).scalar() or 0

        logger.debug(
            "dashboard_stats_retrieved",
            admin_id=str(current_admin.id),
            total_elections=total_elections,
            active_elections=active_elections,
            registered_voters=registered_voters,
            total_votes=total_votes
        )

        return {
            "total_elections": total_elections,
            "active_elections": active_elections,
            "registered_voters": registered_voters,
            "total_votes": total_votes
        }

    except Exception as e:
        logger.error("dashboard_stats_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard stats: {str(e)}"
        )


@router.get("/{election_id}", response_model=ElectionResponse)
async def get_election(
    election_id: UUID,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get detailed election information including:
    - Election metadata
    - Constituencies
    - Candidates
    - Blockchain contract addresses
    """
    try:
        election = db.query(Election).filter(Election.id == election_id).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Election not found"
            )

        logger.info(
            "election_retrieved",
            election_id=str(election_id),
            admin_id=str(current_admin.id)
        )

        return election

    except HTTPException:
        raise
    except Exception as e:
        logger.error("election_retrieval_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve election: {str(e)}"
        )


@router.post("/{election_id}/constituencies", response_model=ConstituencyResponse, status_code=status.HTTP_201_CREATED)
async def add_constituency(
    election_id: UUID,
    constituency_data: ConstituencyCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_role(AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN))
):
    """
    Add constituency to election
    Election must be in draft or configured state
    """
    try:
        # Verify election exists and is in correct state
        election = db.query(Election).filter(Election.id == election_id).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Election not found"
            )

        if election.status not in [ElectionStatus.DRAFT.value, ElectionStatus.CONFIGURED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add constituency to election in {election.status} state"
            )

        # Check for duplicate constituency code
        existing = db.query(Constituency).filter(
            and_(
                Constituency.election_id == election_id,
                Constituency.code == constituency_data.code
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Constituency with this code already exists in this election"
            )

        # Auto-generate on_chain_id if not provided
        if constituency_data.on_chain_id is None:
            # Get the max on_chain_id for this election and increment
            max_on_chain_id = db.query(func.max(Constituency.on_chain_id)).filter(
                Constituency.election_id == election_id
            ).scalar()
            next_on_chain_id = (max_on_chain_id or -1) + 1
        else:
            next_on_chain_id = constituency_data.on_chain_id

        # Create constituency
        constituency = Constituency(
            election_id=election_id,
            name=constituency_data.name,
            code=constituency_data.code,
            on_chain_id=next_on_chain_id
        )

        db.add(constituency)
        db.commit()
        db.refresh(constituency)

        logger.info(
            "constituency_added",
            constituency_id=str(constituency.id),
            election_id=str(election_id),
            code=constituency.code
        )

        return constituency

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("constituency_addition_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add constituency: {str(e)}"
        )


@router.post("/{election_id}/candidates", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def add_candidate(
    election_id: UUID,
    candidate_data: CandidateCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_role(AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN))
):
    """
    Add candidate to election
    Election must be in draft or configured state
    Registers candidate on blockchain
    """
    try:
        # Verify election exists and is in correct state
        election = db.query(Election).filter(Election.id == election_id).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Election not found"
            )

        if election.status not in [ElectionStatus.DRAFT.value, ElectionStatus.CONFIGURED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add candidate to election in {election.status} state"
            )

        # Verify constituency exists and belongs to this election
        constituency = db.query(Constituency).filter(
            and_(
                Constituency.id == candidate_data.constituency_id,
                Constituency.election_id == election_id
            )
        ).first()

        if not constituency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Constituency not found in this election"
            )

        # Auto-generate on_chain_id if not provided
        if candidate_data.on_chain_id is None:
            # Get the max on_chain_id for this election and increment
            max_on_chain_id = db.query(func.max(Candidate.on_chain_id)).filter(
                Candidate.election_id == election_id
            ).scalar()
            next_on_chain_id = (max_on_chain_id or -1) + 1
        else:
            next_on_chain_id = candidate_data.on_chain_id

        # Check for duplicate on_chain_id
        existing = db.query(Candidate).filter(
            and_(
                Candidate.election_id == election_id,
                Candidate.on_chain_id == next_on_chain_id
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Candidate with this on_chain_id already exists in this election"
            )

        # Create candidate
        candidate = Candidate(
            election_id=election_id,
            constituency_id=candidate_data.constituency_id,
            name=candidate_data.name,
            party=candidate_data.party,
            bio=candidate_data.bio,
            on_chain_id=next_on_chain_id,
            created_by=current_admin.id
        )

        db.add(candidate)
        db.flush()

        # Register candidate on blockchain if blockchain is connected
        if blockchain_service.connected:
            try:
                tx_hash = blockchain_service.register_candidate(
                    next_on_chain_id,
                    constituency.on_chain_id
                )

                # Log blockchain transaction
                log_blockchain_tx(
                    db,
                    election_id,
                    TxType.REGISTER_CANDIDATE,
                    tx_hash,
                    blockchain_service.default_account
                )

                logger.info(
                    "candidate_registered_on_chain",
                    candidate_id=str(candidate.id),
                    tx_hash=tx_hash
                )

            except BlockchainError as be:
                logger.warning(
                    "candidate_blockchain_registration_failed",
                    candidate_id=str(candidate.id),
                    error=str(be)
                )
                # Continue anyway - can register on blockchain later

        # Log audit event
        log_audit(
            db,
            current_admin,
            LogAction.CANDIDATE_ADDED,
            "candidates",
            candidate.id,
            {
                "name": candidate.name,
                "party": candidate.party,
                "constituency_id": str(candidate_data.constituency_id)
            }
        )

        db.commit()
        db.refresh(candidate)

        logger.info(
            "candidate_added",
            candidate_id=str(candidate.id),
            election_id=str(election_id),
            name=candidate.name
        )

        return candidate

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("candidate_addition_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add candidate: {str(e)}"
        )


@router.post("/{election_id}/start")
async def start_election(
    election_id: UUID,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_role(AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN))
):
    """
    Start election - change status to active
    Calls blockchain ElectionController.startElection()
    Election must be in configured state
    """
    try:
        # Verify election exists and is in correct state
        election = db.query(Election).filter(Election.id == election_id).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Election not found"
            )

        # Verify election is in configured state (or draft if no blockchain)
        if election.status not in [ElectionStatus.DRAFT.value, ElectionStatus.CONFIGURED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot start election in {election.status} state. Must be configured first."
            )

        # Verify election has constituencies and candidates
        constituency_count = db.query(func.count(Constituency.id)).filter(
            Constituency.election_id == election_id
        ).scalar()

        if constituency_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start election without constituencies"
            )

        candidate_count = db.query(func.count(Candidate.id)).filter(
            Candidate.election_id == election_id
        ).scalar()

        if candidate_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start election without candidates"
            )

        # Start election on blockchain
        tx_hash = None
        if blockchain_service.connected:
            try:
                # Calculate timestamps
                start_time = int(election.voting_start_at.timestamp()) if election.voting_start_at else int(datetime.utcnow().timestamp())
                end_time = int(election.voting_end_at.timestamp()) if election.voting_end_at else int(datetime.utcnow().timestamp()) + 86400  # Default 24 hours

                tx_hash = blockchain_service.start_election(start_time, end_time)

                # Log blockchain transaction
                log_blockchain_tx(
                    db,
                    election_id,
                    TxType.OPEN_VOTING,
                    tx_hash,
                    blockchain_service.default_account
                )

                logger.info(
                    "election_started_on_chain",
                    election_id=str(election_id),
                    tx_hash=tx_hash
                )

            except BlockchainError as be:
                logger.error("election_start_blockchain_failed", error=str(be))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to start election on blockchain: {str(be)}"
                )

        # Update election status
        election.status = ElectionStatus.ACTIVE.value
        if not election.voting_start_at:
            election.voting_start_at = datetime.utcnow()

        # Log audit event
        log_audit(
            db,
            current_admin,
            LogAction.ELECTION_STARTED,
            "elections",
            election.id,
            {"tx_hash": tx_hash, "status": election.status}
        )

        db.commit()

        logger.info(
            "election_started",
            election_id=str(election_id),
            admin_id=str(current_admin.id)
        )

        return {
            "success": True,
            "message": "Election started successfully",
            "election_id": str(election_id),
            "status": election.status,
            "tx_hash": tx_hash
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("election_start_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start election: {str(e)}"
        )


@router.post("/{election_id}/close")
async def close_election(
    election_id: UUID,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_role(AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN))
):
    """
    Close election - change status to closed
    Calls blockchain ElectionController.closeElection()
    Election must be in active state
    """
    try:
        # Verify election exists and is in correct state
        election = db.query(Election).filter(Election.id == election_id).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Election not found"
            )

        if election.status != ElectionStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot close election in {election.status} state. Must be active."
            )

        # Close election on blockchain
        tx_hash = None
        if blockchain_service.connected:
            try:
                tx_hash = blockchain_service.close_election()

                # Log blockchain transaction
                log_blockchain_tx(
                    db,
                    election_id,
                    TxType.CLOSE_VOTING,
                    tx_hash,
                    blockchain_service.default_account
                )

                logger.info(
                    "election_closed_on_chain",
                    election_id=str(election_id),
                    tx_hash=tx_hash
                )

            except BlockchainError as be:
                logger.error("election_close_blockchain_failed", error=str(be))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to close election on blockchain: {str(be)}"
                )

        # Update election status
        election.status = ElectionStatus.ENDED.value
        if not election.voting_end_at:
            election.voting_end_at = datetime.utcnow()

        # Log audit event
        log_audit(
            db,
            current_admin,
            LogAction.ELECTION_CLOSED,
            "elections",
            election.id,
            {"tx_hash": tx_hash, "status": election.status}
        )

        db.commit()

        logger.info(
            "election_closed",
            election_id=str(election_id),
            admin_id=str(current_admin.id)
        )

        return {
            "success": True,
            "message": "Election closed successfully",
            "election_id": str(election_id),
            "status": election.status,
            "tx_hash": tx_hash
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("election_close_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close election: {str(e)}"
        )


@router.post("/{election_id}/finalize")
async def finalize_election(
    election_id: UUID,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_role(AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN))
):
    """
    Finalize election results
    - Tallies results from blockchain using ResultsTallier
    - Detects ties (multiple candidates with max votes)
    - Stores results in database
    - Changes status to finalized
    Election must be in ended/closed state
    """
    try:
        # Verify election exists and is in correct state
        election = db.query(Election).filter(Election.id == election_id).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Election not found"
            )

        if election.status != ElectionStatus.ENDED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot finalize election in {election.status} state. Must be closed first."
            )

        # Get all constituencies for this election
        constituencies = db.query(Constituency).filter(
            Constituency.election_id == election_id
        ).all()

        if not constituencies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No constituencies found for this election"
            )

        # Prepare data for blockchain finalization
        constituency_ids = [c.on_chain_id for c in constituencies]
        candidate_ids_per_constituency = []
        expected_votes_per_constituency = []

        for constituency in constituencies:
            # Get all candidates for this constituency
            candidates = db.query(Candidate).filter(
                and_(
                    Candidate.election_id == election_id,
                    Candidate.constituency_id == constituency.id,
                    Candidate.is_active == True
                )
            ).all()

            if not candidates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No candidates found for constituency {constituency.name}"
                )

            candidate_ids = [c.on_chain_id for c in candidates]
            candidate_ids_per_constituency.append(candidate_ids)

            # Get vote count for this constituency from database
            vote_count = db.query(func.count(VoteSubmission.id)).filter(
                VoteSubmission.election_id == election_id
            ).join(
                Candidate, VoteSubmission.voter_id == Candidate.id  # This is simplified
            ).filter(
                Candidate.constituency_id == constituency.id
            ).scalar() or 0

            expected_votes_per_constituency.append(vote_count)

        # Finalize election on blockchain
        tx_hash = None
        if blockchain_service.connected:
            try:
                tx_hash = blockchain_service.finalize_election(
                    constituency_ids,
                    candidate_ids_per_constituency,
                    expected_votes_per_constituency
                )

                # Log blockchain transaction
                log_blockchain_tx(
                    db,
                    election_id,
                    TxType.FINALIZE_ELECTION,
                    tx_hash,
                    blockchain_service.default_account
                )

                logger.info(
                    "election_finalized_on_chain",
                    election_id=str(election_id),
                    tx_hash=tx_hash
                )

            except BlockchainError as be:
                logger.error("election_finalize_blockchain_failed", error=str(be))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to finalize election on blockchain: {str(be)}"
                )

        # Update election status
        election.status = ElectionStatus.FINALIZED.value
        election.finalized_by = current_admin.id
        election.finalized_at = datetime.utcnow()

        # Log audit event
        log_audit(
            db,
            current_admin,
            LogAction.ELECTION_FINALIZED,
            "elections",
            election.id,
            {"tx_hash": tx_hash, "status": election.status}
        )

        db.commit()

        logger.info(
            "election_finalized",
            election_id=str(election_id),
            admin_id=str(current_admin.id)
        )

        return {
            "success": True,
            "message": "Election finalized successfully",
            "election_id": str(election_id),
            "status": election.status,
            "tx_hash": tx_hash,
            "constituencies_processed": len(constituencies)
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("election_finalization_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalize election: {str(e)}"
        )


@router.get("/{election_id}/results")
async def get_election_results(
    election_id: UUID,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get election results from blockchain
    Returns aggregated results including:
    - Candidates and vote counts per constituency
    - Winners per constituency
    - Tie information
    - Overall turnout
    Only available if election is finalized
    """
    try:
        # Verify election exists and is finalized
        election = db.query(Election).filter(Election.id == election_id).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Election not found"
            )

        if election.status != ElectionStatus.FINALIZED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Results not available. Election status is {election.status}. Must be finalized."
            )

        # Get results from blockchain
        results = {
            "election_id": str(election_id),
            "election_name": election.name,
            "status": election.status,
            "finalized_at": election.finalized_at.isoformat() if election.finalized_at else None,
            "constituencies": []
        }

        # Get all constituencies
        constituencies = db.query(Constituency).filter(
            Constituency.election_id == election_id
        ).all()

        total_votes = 0

        for constituency in constituencies:
            constituency_result = {
                "constituency_id": str(constituency.id),
                "constituency_name": constituency.name,
                "constituency_code": constituency.code,
                "candidates": [],
                "winner": None,
                "is_tied": False,
                "total_votes": 0
            }

            # Get candidates for this constituency
            candidates = db.query(Candidate).filter(
                and_(
                    Candidate.election_id == election_id,
                    Candidate.constituency_id == constituency.id,
                    Candidate.is_active == True
                )
            ).all()

            max_votes = 0
            winner_candidate = None

            for candidate in candidates:
                # Get vote count from blockchain
                vote_count = 0
                if blockchain_service.connected:
                    try:
                        vote_count = blockchain_service.get_candidate_vote_count(candidate.on_chain_id)
                    except BlockchainError as be:
                        logger.warning(
                            "candidate_vote_count_retrieval_failed",
                            candidate_id=str(candidate.id),
                            error=str(be)
                        )

                candidate_data = {
                    "candidate_id": str(candidate.id),
                    "candidate_name": candidate.name,
                    "party": candidate.party,
                    "vote_count": vote_count
                }

                constituency_result["candidates"].append(candidate_data)
                constituency_result["total_votes"] += vote_count

                # Track winner
                if vote_count > max_votes:
                    max_votes = vote_count
                    winner_candidate = candidate_data
                elif vote_count == max_votes and max_votes > 0:
                    # Tie detected
                    constituency_result["is_tied"] = True

            total_votes += constituency_result["total_votes"]

            # Set winner if no tie
            if winner_candidate and not constituency_result["is_tied"]:
                constituency_result["winner"] = winner_candidate

            # Get blockchain constituency result if available
            if blockchain_service.connected:
                try:
                    bc_result = blockchain_service.get_constituency_result(constituency.on_chain_id)
                    constituency_result["blockchain_data"] = {
                        "winner_candidate_id": bc_result["winner_candidate_id"],
                        "winner_vote_count": bc_result["winner_vote_count"],
                        "is_tied": bc_result["is_tied"],
                        "total_votes": bc_result["total_votes"],
                        "finalized_at": bc_result["finalized_at"]
                    }
                except BlockchainError as be:
                    logger.warning(
                        "constituency_result_retrieval_failed",
                        constituency_id=str(constituency.id),
                        error=str(be)
                    )

            results["constituencies"].append(constituency_result)

        # Add overall statistics
        results["total_votes_cast"] = total_votes
        results["total_constituencies"] = len(constituencies)

        # Get voter statistics
        total_registered = db.query(func.count(Constituency.id)).join(
            Election
        ).filter(Election.id == election_id).scalar() or 0

        results["total_registered_voters"] = total_registered
        results["turnout_percentage"] = (total_votes / total_registered * 100) if total_registered > 0 else 0

        logger.info(
            "election_results_retrieved",
            election_id=str(election_id),
            admin_id=str(current_admin.id)
        )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error("election_results_retrieval_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve election results: {str(e)}"
        )


@router.get("/{election_id}/audit")
async def get_election_audit_trail(
    election_id: UUID,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_role(AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN, AdminRole.AUDITOR))
):
    """
    Get audit trail for election
    Returns blockchain transaction log and vote timestamps
    Admin only (election_administrator, super_admin, or auditor)
    """
    try:
        # Verify election exists
        election = db.query(Election).filter(Election.id == election_id).first()

        if not election:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Election not found"
            )

        # Get blockchain transactions for this election
        blockchain_txns = db.query(BlockchainTransaction).filter(
            BlockchainTransaction.election_id == election_id
        ).order_by(BlockchainTransaction.recorded_at).all()

        # Get audit logs related to this election
        audit_logs = db.query(AuditLog).filter(
            and_(
                AuditLog.target_table == "elections",
                AuditLog.target_id == election_id
            )
        ).order_by(AuditLog.occurred_at).all()

        # Get vote submission timestamps
        vote_submissions = db.query(VoteSubmission).filter(
            VoteSubmission.election_id == election_id
        ).order_by(VoteSubmission.submitted_at).all()

        result = {
            "election_id": str(election_id),
            "election_name": election.name,
            "audit_trail": {
                "blockchain_transactions": [
                    {
                        "id": str(tx.id),
                        "tx_type": tx.tx_type.value,
                        "tx_hash": tx.tx_hash,
                        "block_number": tx.block_number,
                        "from_address": tx.from_address,
                        "to_address": tx.to_address,
                        "gas_used": tx.gas_used,
                        "status": tx.status,
                        "recorded_at": tx.recorded_at.isoformat()
                    }
                    for tx in blockchain_txns
                ],
                "audit_logs": [
                    {
                        "id": str(log.id),
                        "admin_id": str(log.admin_id) if log.admin_id else None,
                        "action": log.action.value,
                        "details": log.details,
                        "occurred_at": log.occurred_at.isoformat()
                    }
                    for log in audit_logs
                ],
                "vote_submissions": [
                    {
                        "id": str(vote.id),
                        "tx_hash": vote.tx_hash,
                        "block_number": vote.block_number,
                        "submitted_at": vote.submitted_at.isoformat()
                    }
                    for vote in vote_submissions
                ]
            },
            "statistics": {
                "total_blockchain_transactions": len(blockchain_txns),
                "total_audit_events": len(audit_logs),
                "total_votes_submitted": len(vote_submissions)
            }
        }

        logger.info(
            "election_audit_trail_retrieved",
            election_id=str(election_id),
            admin_id=str(current_admin.id)
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("election_audit_retrieval_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve election audit trail: {str(e)}"
        )


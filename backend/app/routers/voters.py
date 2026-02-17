"""
Voter registration and management router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import structlog
import base64
import uuid

from app.database import get_db
from app.middleware.auth import get_current_admin, require_role
from app.models.admin import AdminRole
from app.models.audit import AuditLog, LogAction
from app.schemas.voter import VoterCreate, VoterResponse
from app.services.crypto import hash_biometric, derive_blockchain_voter_id, generate_salt, encrypt_biometric
from app.services.blockchain import blockchain_service, BlockchainError
from app.services.biometric import FaceService, FingerprintService, FACE_AVAILABLE, FINGERPRINT_AVAILABLE

logger = structlog.get_logger()

router = APIRouter(prefix="/api/voters", tags=["Voters"])

# Initialize biometric services
face_service = FaceService() if FACE_AVAILABLE else None
fingerprint_service = FingerprintService() if FINGERPRINT_AVAILABLE else None


@router.post("/register", response_model=VoterResponse, status_code=status.HTTP_201_CREATED)
async def register_voter(
    voter_data: VoterCreate,
    current_admin = Depends(require_role(AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Register a new voter with biometric data

    Admin only endpoint. Processes face and fingerprint biometrics,
    generates blockchain voter ID, and registers on blockchain.

    Args:
        voter_data: Voter registration data including biometric images
        current_admin: Current authenticated admin
        db: Database session

    Returns:
        VoterResponse: Registered voter details with blockchain_voter_id
    """
    try:
        # Check if voter_id already exists
        result = db.execute(
            text("SELECT id FROM voters WHERE voter_id = :voter_id"),
            {"voter_id": voter_data.voter_id}
        )
        existing_voter = result.fetchone()

        if existing_voter:
            logger.warning("voter_registration_failed", voter_id=voter_data.voter_id, reason="duplicate_voter_id")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Voter with ID {voter_data.voter_id} already exists"
            )

        # Validate constituency exists
        result = db.execute(
            text("SELECT id, on_chain_id FROM constituencies WHERE id = :constituency_id"),
            {"constituency_id": str(voter_data.constituency_id)}
        )
        constituency = result.fetchone()

        if not constituency:
            logger.warning("voter_registration_failed", voter_id=voter_data.voter_id, reason="constituency_not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Constituency {voter_data.constituency_id} not found"
            )

        # Decode biometric data from base64
        try:
            # Strip data URL prefix if present (e.g., "data:image/jpeg;base64,")
            face_image_data = voter_data.face_image
            if face_image_data.startswith('data:'):
                face_image_data = face_image_data.split(',', 1)[1]

            face_image_bytes = base64.b64decode(face_image_data)

            # Fingerprint is optional
            fingerprint_bytes = None
            fingerprint_hash = None
            encrypted_fingerprint = None

            if voter_data.fingerprint_image:
                fingerprint_data = voter_data.fingerprint_image
                if fingerprint_data.startswith('data:'):
                    fingerprint_data = fingerprint_data.split(',', 1)[1]
                fingerprint_bytes = base64.b64decode(fingerprint_data)

        except Exception as e:
            logger.error("biometric_decode_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 encoded biometric data"
            )

        # Generate cryptographic salt for biometric hashing
        biometric_salt = generate_salt()

        # Process face biometric: extract embedding, hash, quantize, and encrypt
        if not face_service:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Face recognition service not available"
            )

        try:
            face_hash, encrypted_face = face_service.process_and_store_embedding(
                face_image_bytes,
                biometric_salt
            )
            logger.info("face_embedding_processed", voter_id=voter_data.voter_id)
        except Exception as e:
            logger.error("face_embedding_processing_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Face processing failed: {str(e)}"
            )

        # Process fingerprint if provided
        fingerprint_hash = None
        encrypted_fingerprint = None
        if fingerprint_bytes and fingerprint_service:
            try:
                fingerprint_hash, encrypted_fingerprint = fingerprint_service.process_and_store_template(
                    fingerprint_bytes,
                    biometric_salt
                )
                logger.info("fingerprint_template_processed", voter_id=voter_data.voter_id)
            except Exception as e:
                logger.warning("fingerprint_processing_failed", error=str(e), message="Continuing without fingerprint")
                fingerprint_hash = None
                encrypted_fingerprint = None

        # Derive blockchain voter ID
        blockchain_voter_id = derive_blockchain_voter_id(voter_data.voter_id)

        # Generate new voter UUID
        voter_uuid = uuid.uuid4()

        # Register voter on blockchain
        # Try to register on blockchain (optional for testing)
        blockchain_tx_hash = None
        try:
            if blockchain_service.connected:
                blockchain_tx_hash = blockchain_service.register_voter_on_chain(
                    blockchain_voter_id,
                    constituency.on_chain_id
                )
                logger.info("voter_registered_on_blockchain", tx_hash=blockchain_tx_hash, blockchain_voter_id=blockchain_voter_id)
            else:
                logger.warning("blockchain_not_connected", message="Skipping blockchain registration")
        except BlockchainError as e:
            # Log but don't fail - allow registration without blockchain for testing
            logger.warning("blockchain_registration_failed", error=str(e), message="Continuing with database registration only")
        except Exception as e:
            # Catch any other blockchain errors
            logger.warning("blockchain_registration_error", error=str(e), message="Continuing with database registration only")

        # Insert voter into database
        db.execute(
            text("""
                INSERT INTO voters (
                    id, voter_id, full_name, address, age, constituency_id,
                    face_embedding_hash, fingerprint_template_hash, biometric_salt,
                    encrypted_face_embedding, encrypted_fingerprint_template,
                    blockchain_voter_id, has_voted, failed_auth_count, locked_out,
                    registered_by, registered_at, updated_at
                )
                VALUES (
                    :id, :voter_id, :full_name, :address, :age, :constituency_id,
                    :face_hash, :fingerprint_hash, :biometric_salt,
                    :encrypted_face, :encrypted_fingerprint,
                    :blockchain_voter_id, FALSE, 0, FALSE,
                    :registered_by, NOW(), NOW()
                )
            """),
            {
                "id": str(voter_uuid),
                "voter_id": voter_data.voter_id,
                "full_name": voter_data.full_name,
                "address": voter_data.address,
                "age": voter_data.age,
                "constituency_id": str(voter_data.constituency_id),
                "face_hash": face_hash,
                "fingerprint_hash": fingerprint_hash,
                "biometric_salt": biometric_salt,
                "encrypted_face": encrypted_face,
                "encrypted_fingerprint": encrypted_fingerprint,
                "blockchain_voter_id": blockchain_voter_id,
                "registered_by": str(current_admin.id)
            }
        )
        db.commit()

        logger.info(
            "voter_registered",
            voter_id=voter_data.voter_id,
            blockchain_voter_id=blockchain_voter_id,
            registered_by=str(current_admin.id)
        )

        # Create audit log for voter registration
        audit_log = AuditLog(
            admin_id=current_admin.id,
            action=LogAction.VOTER_REGISTERED,
            target_table="voters",
            target_id=voter_uuid,
            details={
                "voter_id": voter_data.voter_id,
                "full_name": voter_data.full_name,
                "blockchain_voter_id": blockchain_voter_id,
                "constituency_id": str(voter_data.constituency_id)
            }
        )
        db.add(audit_log)
        db.commit()

        # Fetch and return created voter
        result = db.execute(
            text("""
                SELECT id, voter_id, full_name, address, age, constituency_id,
                       blockchain_voter_id, has_voted, voted_at, locked_out, registered_at
                FROM voters
                WHERE id = :id
            """),
            {"id": str(voter_uuid)}
        )
        voter = result.fetchone()

        return VoterResponse(
            id=voter.id,
            voter_id=voter.voter_id,
            full_name=voter.full_name,
            address=voter.address,
            age=voter.age,
            constituency_id=voter.constituency_id,
            blockchain_voter_id=voter.blockchain_voter_id,
            has_voted=voter.has_voted,
            voted_at=voter.voted_at,
            locked_out=voter.locked_out,
            registered_at=voter.registered_at
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error("voter_registration_error", error=str(e), voter_id=voter_data.voter_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voter registration failed"
        )


@router.get("/{voter_id}", response_model=VoterResponse)
async def get_voter(
    voter_id: str,
    current_admin = Depends(require_role(AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN, AdminRole.POLLING_OFFICER, AdminRole.AUDITOR)),
    db: Session = Depends(get_db)
):
    """
    Get voter details by voter_id

    Admin only. Returns voter information without biometric data.

    Args:
        voter_id: Voter identifier
        current_admin: Current authenticated admin
        db: Database session

    Returns:
        VoterResponse: Voter details without biometric data
    """
    try:
        result = db.execute(
            text("""
                SELECT id, voter_id, full_name, address, age, constituency_id,
                       blockchain_voter_id, has_voted, voted_at, locked_out, registered_at
                FROM voters
                WHERE voter_id = :voter_id
            """),
            {"voter_id": voter_id}
        )
        voter = result.fetchone()

        if not voter:
            logger.warning("voter_not_found", voter_id=voter_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Voter {voter_id} not found"
            )

        logger.info("voter_retrieved", voter_id=voter_id, admin_id=str(current_admin.id))

        return VoterResponse(
            id=voter.id,
            voter_id=voter.voter_id,
            full_name=voter.full_name,
            address=voter.address,
            age=voter.age,
            constituency_id=voter.constituency_id,
            blockchain_voter_id=voter.blockchain_voter_id,
            has_voted=voter.has_voted,
            voted_at=voter.voted_at,
            locked_out=voter.locked_out,
            registered_at=voter.registered_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("voter_retrieval_error", error=str(e), voter_id=voter_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve voter"
        )


@router.get("", response_model=List[VoterResponse])
async def list_voters(
    skip: int = 0,
    limit: int = 100,
    constituency_id: Optional[str] = None,
    current_admin = Depends(require_role(AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN, AdminRole.POLLING_OFFICER, AdminRole.AUDITOR)),
    db: Session = Depends(get_db)
):
    """
    List voters with pagination

    Admin only. Returns list of voters without biometric data.

    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)
        constituency_id: Filter by constituency UUID (optional)
        current_admin: Current authenticated admin
        db: Database session

    Returns:
        List[VoterResponse]: List of voters
    """
    try:
        # Validate limit
        if limit > 1000:
            limit = 1000

        # Build query with optional constituency filter
        if constituency_id:
            query = text("""
                SELECT id, voter_id, full_name, address, age, constituency_id,
                       blockchain_voter_id, has_voted, voted_at, locked_out, registered_at
                FROM voters
                WHERE constituency_id = :constituency_id
                ORDER BY registered_at DESC
                LIMIT :limit OFFSET :skip
            """)
            params = {"constituency_id": constituency_id, "limit": limit, "skip": skip}
        else:
            query = text("""
                SELECT id, voter_id, full_name, address, age, constituency_id,
                       blockchain_voter_id, has_voted, voted_at, locked_out, registered_at
                FROM voters
                ORDER BY registered_at DESC
                LIMIT :limit OFFSET :skip
            """)
            params = {"limit": limit, "skip": skip}

        result = db.execute(query, params)
        voters = result.fetchall()

        logger.info(
            "voters_listed",
            count=len(voters),
            constituency_id=constituency_id,
            admin_id=str(current_admin.id)
        )

        return [
            VoterResponse(
                id=voter.id,
                voter_id=voter.voter_id,
                full_name=voter.full_name,
                address=voter.address,
                age=voter.age,
                constituency_id=voter.constituency_id,
                blockchain_voter_id=voter.blockchain_voter_id,
                has_voted=voter.has_voted,
                voted_at=voter.voted_at,
                locked_out=voter.locked_out,
                registered_at=voter.registered_at
            )
            for voter in voters
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("voters_list_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve voters"
        )


@router.put("/{voter_id}", response_model=VoterResponse)
async def update_voter(
    voter_id: str,
    full_name: Optional[str] = None,
    address: Optional[str] = None,
    current_admin = Depends(require_role(AdminRole.ELECTION_ADMINISTRATOR, AdminRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update voter information

    Admin only. Can update name and address only.
    Cannot update biometric data or voter_id.

    Args:
        voter_id: Voter identifier
        full_name: New full name (optional)
        address: New address (optional)
        current_admin: Current authenticated admin
        db: Database session

    Returns:
        VoterResponse: Updated voter details
    """
    try:
        # Check if voter exists
        result = db.execute(
            text("SELECT id FROM voters WHERE voter_id = :voter_id"),
            {"voter_id": voter_id}
        )
        voter = result.fetchone()

        if not voter:
            logger.warning("voter_update_failed", voter_id=voter_id, reason="voter_not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Voter {voter_id} not found"
            )

        # Build update query dynamically based on provided fields
        update_fields = []
        params = {"voter_id": voter_id}

        if full_name is not None:
            update_fields.append("full_name = :full_name")
            params["full_name"] = full_name

        if address is not None:
            update_fields.append("address = :address")
            params["address"] = address

        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Add updated_at
        update_fields.append("updated_at = NOW()")

        # Execute update
        query = text(f"""
            UPDATE voters
            SET {', '.join(update_fields)}
            WHERE voter_id = :voter_id
        """)

        db.execute(query, params)
        db.commit()

        logger.info(
            "voter_updated",
            voter_id=voter_id,
            updated_fields=list(params.keys()),
            admin_id=str(current_admin.id)
        )

        # Fetch and return updated voter
        result = db.execute(
            text("""
                SELECT id, voter_id, full_name, address, age, constituency_id,
                       blockchain_voter_id, has_voted, voted_at, locked_out, registered_at
                FROM voters
                WHERE voter_id = :voter_id
            """),
            {"voter_id": voter_id}
        )
        updated_voter = result.fetchone()

        return VoterResponse(
            id=updated_voter.id,
            voter_id=updated_voter.voter_id,
            full_name=updated_voter.full_name,
            address=updated_voter.address,
            age=updated_voter.age,
            constituency_id=updated_voter.constituency_id,
            blockchain_voter_id=updated_voter.blockchain_voter_id,
            has_voted=updated_voter.has_voted,
            voted_at=updated_voter.voted_at,
            locked_out=updated_voter.locked_out,
            registered_at=updated_voter.registered_at
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error("voter_update_error", error=str(e), voter_id=voter_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update voter"
        )


@router.delete("/{voter_id}", status_code=status.HTTP_200_OK)
async def delete_voter(
    voter_id: str,
    current_admin = Depends(require_role(AdminRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Soft delete a voter

    Super admin only. Marks voter as locked out to prevent voting.
    Does not actually delete the record to maintain audit trail.

    Args:
        voter_id: Voter identifier
        current_admin: Current authenticated admin (must be super admin)
        db: Database session

    Returns:
        dict: Success message
    """
    try:
        # Check if voter exists
        result = db.execute(
            text("SELECT id, locked_out FROM voters WHERE voter_id = :voter_id"),
            {"voter_id": voter_id}
        )
        voter = result.fetchone()

        if not voter:
            logger.warning("voter_delete_failed", voter_id=voter_id, reason="voter_not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Voter {voter_id} not found"
            )

        if voter.locked_out:
            logger.warning("voter_delete_failed", voter_id=voter_id, reason="already_locked_out")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Voter {voter_id} is already locked out"
            )

        # Soft delete by locking out the voter
        db.execute(
            text("""
                UPDATE voters
                SET locked_out = TRUE,
                    lockout_at = NOW(),
                    updated_at = NOW()
                WHERE voter_id = :voter_id
            """),
            {"voter_id": voter_id}
        )
        db.commit()

        logger.info(
            "voter_soft_deleted",
            voter_id=voter_id,
            admin_id=str(current_admin.id)
        )

        return {
            "message": f"Voter {voter_id} has been locked out successfully",
            "voter_id": voter_id
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error("voter_delete_error", error=str(e), voter_id=voter_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete voter"
        )

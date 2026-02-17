"""
Authentication and authorization routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Optional
import structlog
import uuid

from app.database import get_db
from app.config import settings
from app.schemas.auth import LoginResponse, LoginRequest, TokenRefreshResponse, MFASetupResponse, MFAVerifyResponse, Token, TokenRefresh, MFASetup, MFAVerify
from app.services.crypto import hash_password, verify_password
from app.middleware.auth import create_access_token, create_refresh_token, get_current_admin

logger = structlog.get_logger()

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Admin login with username and password
    Returns JWT access and refresh tokens
    """
    try:
        # Query admin user
        result = db.execute(
            text("""
                SELECT id, username, email, password_hash, role, is_active, mfa_enabled
                FROM admins
                WHERE username = :username
            """),
            {"username": form_data.username}
        )
        admin = result.fetchone()

        if not admin:
            logger.warning("login_failed", username=form_data.username, reason="user_not_found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if account is active
        if not admin.is_active:
            logger.warning("login_failed", username=form_data.username, reason="account_inactive")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )

        # Verify password
        if not verify_password(form_data.password, admin.password_hash):
            logger.warning("login_failed", username=form_data.username, reason="invalid_password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if MFA is required
        if admin.mfa_enabled:
            # Return a temporary token that requires MFA verification
            temp_token = create_access_token(
                data={
                    "sub": str(admin.id),
                    "username": admin.username,
                    "role": admin.role,
                    "mfa_required": True
                },
                expires_delta=timedelta(minutes=5)
            )
            return LoginResponse(
                access_token=temp_token,
                refresh_token="",
                token_type="bearer",
                expires_in=300,
                admin_id=str(admin.id),
                username=admin.username,
                role=str(admin.role)
            )

        # Create tokens
        access_token = create_access_token(
            data={
                "sub": str(admin.id),
                "username": admin.username,
                "role": admin.role
            }
        )
        refresh_token = create_refresh_token(
            data={"sub": str(admin.id)}
        )

        # Update last login
        db.execute(
            text("UPDATE admins SET last_login_at = NOW() WHERE id = :id"),
            {"id": str(admin.id)}
        )
        db.commit()

        logger.info("login_success", admin_id=str(admin.id), username=admin.username)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800,
            admin_id=str(admin.id),
            username=admin.username,
            role=str(admin.role)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    try:
        # Verify and decode refresh token
        from app.middleware.auth import verify_token
        payload = verify_token(token_data.refresh_token)

        admin_id = payload.get("sub")
        if not admin_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Get admin details
        result = db.execute(
            text("SELECT id, username, role, is_active FROM admins WHERE id = :id"),
            {"id": admin_id}
        )
        admin = result.fetchone()

        if not admin or not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found or inactive"
            )

        # Create new access token
        access_token = create_access_token(
            data={
                "sub": str(admin.id),
                "username": admin.username,
                "role": admin.role
            }
        )

        return {
            "access_token": access_token,
            "refresh_token": token_data.refresh_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("refresh_token_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(current_admin: dict = Depends(get_current_admin)):
    """
    Logout admin user
    In a production system, this would invalidate the token in Redis
    """
    logger.info("logout", admin_id=current_admin["sub"])
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(current_admin: Admin = Depends(get_current_admin)):
    """
    Get current authenticated admin details
    """
    if not current_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    return {
        "id": str(current_admin.id),
        "username": current_admin.username,
        "email": current_admin.email,
        "role": current_admin.role,
        "created_at": current_admin.created_at.isoformat() if current_admin.created_at else None,
        "last_login_at": current_admin.last_login_at.isoformat() if current_admin.last_login_at else None
    }


@router.post("/mfa/setup", response_model=MFASetup)
async def setup_mfa(
    current_admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Setup MFA (TOTP) for admin account
    """
    try:
        import pyotp

        # Generate TOTP secret
        secret = pyotp.random_base32()

        # Generate QR code provisioning URI
        admin_username = current_admin["username"]
        uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=admin_username,
            issuer_name="Blockchain Voting System"
        )

        # Store secret in database (encrypted in production)
        db.execute(
            text("UPDATE admins SET mfa_secret = :secret WHERE id = :id"),
            {"secret": secret, "id": current_admin["sub"]}
        )
        db.commit()

        logger.info("mfa_setup_initiated", admin_id=current_admin["sub"])

        return {
            "secret": secret,
            "qr_code_uri": uri,
            "message": "Scan QR code with authenticator app"
        }

    except Exception as e:
        logger.error("mfa_setup_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA setup failed"
        )


@router.post("/mfa/verify")
async def verify_mfa(
    mfa_data: MFAVerify,
    current_admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Verify MFA code and enable MFA for account
    """
    try:
        import pyotp

        # Get MFA secret
        result = db.execute(
            text("SELECT mfa_secret FROM admins WHERE id = :id"),
            {"id": current_admin["sub"]}
        )
        admin = result.fetchone()

        if not admin or not admin.mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA not set up"
            )

        # Verify TOTP code
        totp = pyotp.TOTP(admin.mfa_secret)
        if not totp.verify(mfa_data.code, valid_window=1):
            logger.warning("mfa_verification_failed", admin_id=current_admin["sub"])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )

        # Enable MFA
        db.execute(
            text("UPDATE admins SET mfa_enabled = TRUE WHERE id = :id"),
            {"id": current_admin["sub"]}
        )
        db.commit()

        logger.info("mfa_enabled", admin_id=current_admin["sub"])

        return {"message": "MFA enabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("mfa_verify_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA verification failed"
        )


@router.post("/mfa/disable")
async def disable_mfa(
    current_admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Disable MFA for admin account
    """
    db.execute(
        text("UPDATE admins SET mfa_enabled = FALSE, mfa_secret = NULL WHERE id = :id"),
        {"id": current_admin["sub"]}
    )
    db.commit()

    logger.info("mfa_disabled", admin_id=current_admin["sub"])

    return {"message": "MFA disabled successfully"}


@router.post("/bootstrap")
async def bootstrap_test_data(db: Session = Depends(get_db)):
    """
    Bootstrap endpoint for development/testing
    Creates default admin user and test data if they don't exist
    
    WARNING: This endpoint should be disabled in production!
    """
    try:
        created = []
        
        # Check if admin already exists
        admin_check = db.execute(
            text("SELECT id FROM admins WHERE username = 'superadmin'")
        ).fetchone()
        
        if admin_check:
            # Update existing admin password
            admin_id = admin_check[0]
            hashed_pwd = hash_password("Admin@123456")
            db.execute(
                text("UPDATE admins SET password_hash = :pwd WHERE id = :id"),
                {"pwd": hashed_pwd, "id": admin_id}
            )
            db.commit()
            created.append("admin_superadmin_updated")
            logger.info("bootstrap_admin_updated")
        else:
            # Create superadmin user
            admin_id = str(uuid.uuid4())
            hashed_pwd = hash_password("Admin@123456")
            
            db.execute(
                text("""
                    INSERT INTO admins (id, username, email, password_hash, role, is_active)
                    VALUES (:id, :username, :email, :password_hash, :role, :is_active)
                """),
                {
                    "id": admin_id,
                    "username": "superadmin",
                    "email": "superadmin@voting.local",
                    "password_hash": hashed_pwd,
                    "role": "super_admin",
                    "is_active": True
                }
            )
            db.commit()
            created.append("admin_superadmin")
            logger.info("bootstrap_admin_created")
        
        # Create test election
        election_check = db.execute(
            text("SELECT id FROM elections WHERE name = 'Test Election 2026'")
        ).fetchone()
        
        if not election_check:
            election_id = str(uuid.uuid4())
            
            db.execute(
                text("""
                    INSERT INTO elections (id, name, description, status, voting_start_at, voting_end_at)
                    VALUES (:id, :name, :description, :status, :voting_start_at, :voting_end_at)
                """),
                {
                    "id": election_id,
                    "name": "Test Election 2026",
                    "description": "Test election for development",
                    "status": "draft",
                    "voting_start_at": datetime.utcnow() + timedelta(hours=1),
                    "voting_end_at": datetime.utcnow() + timedelta(hours=9)
                }
            )
            db.commit()
            created.append(f"election_{election_id[:8]}")
            logger.info("bootstrap_election_created")
        else:
            election_id = election_check[0]
        
        # Create test constituency
        constituency_check = db.execute(
            text("SELECT id FROM constituencies WHERE name = 'Test Constituency'")
        ).fetchone()
        
        if not constituency_check:
            constituency_id = str(uuid.uuid4())
            db.execute(
                text("""
                    INSERT INTO constituencies (id, election_id, name, code, on_chain_id)
                    VALUES (:id, :election_id, :name, :code, :on_chain_id)
                """),
                {
                    "id": constituency_id,
                    "election_id": election_id,
                    "name": "Test Constituency",
                    "code": "TST_001",
                    "on_chain_id": 1
                }
            )
            db.commit()
            created.append(f"constituency_{constituency_id[:8]}")
            logger.info("bootstrap_constituency_created")
        else:
            constituency_id = constituency_check[0]
        
        # Create test candidates
        candidate_check = db.execute(
            text("SELECT COUNT(*) as cnt FROM candidates WHERE election_id = :election_id"),
            {"election_id": election_id}
        ).fetchone()
        
        if candidate_check[0] == 0:
            candidate_names = ["Alice Johnson", "Bob Smith", "Charlie Brown", "Diana Prince"]
            for i, name in enumerate(candidate_names, 1):
                candidate_id = str(uuid.uuid4())
                db.execute(
                    text("""
                        INSERT INTO candidates (id, election_id, constituency_id, name, party, on_chain_id)
                        VALUES (:id, :election_id, :constituency_id, :name, :party, :on_chain_id)
                    """),
                    {
                        "id": candidate_id,
                        "election_id": election_id,
                        "constituency_id": constituency_id,
                        "name": name,
                        "party": f"Party {i}",
                        "on_chain_id": i
                    }
                )
            db.commit()
            created.append(f"candidates_4")
            logger.info("bootstrap_candidates_created")
        
        return {
            "success": True,
            "message": "Bootstrap complete",
            "created": created,
            "credentials": {
                "username": "superadmin",
                "password": "Admin@123456"
            }
        }    
    except Exception as e:
        logger.error("bootstrap_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bootstrap failed: {str(e)}"
        )
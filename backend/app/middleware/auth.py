"""
Authentication and authorization middleware
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
import structlog

from app.config import settings
from app.database import get_db
from app.models.admin import Admin, AdminRole
from app.models.voter import Voter

logger = structlog.get_logger()

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        data: Data to encode in token
        expires_delta: Token expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now})

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token

    Args:
        data: Data to encode in token

    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_voting_session_token(voter_id: str, election_id: str, constituency_id: str, session_id: str) -> str:
    """
    Create short-lived voting session token

    Args:
        voter_id: Voter identifier
        election_id: Election identifier
        constituency_id: Constituency_id: Constituency identifier
        session_id: Session identifier

    Returns:
        str: Encoded JWT voting session token
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=5)

    data = {
        "voter_id": voter_id,
        "election_id": election_id,
        "constituency_id": constituency_id,
        "session_id": session_id,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "voting_session"
    }

    encoded_jwt = jwt.encode(data, settings.VOTING_SESSION_SECRET, algorithm=settings.JWT_ALGORITHM)

    # Detailed logging for debugging
    logger.info(
        "voting_session_token_created",
        voter_id=voter_id,
        token_length=len(encoded_jwt),
        token_full=encoded_jwt,
        secret_prefix=settings.VOTING_SESSION_SECRET[:10] if settings.VOTING_SESSION_SECRET else "NONE",
        algorithm=settings.JWT_ALGORITHM,
        payload=data,
        exp_timestamp=data["exp"],
        iat_timestamp=data["iat"]
    )
    return encoded_jwt


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Admin:
    """
    Dependency to get current authenticated admin

    Args:
        credentials: HTTP bearer token
        db: Database session

    Returns:
        Admin: Current admin user

    Raises:
        HTTPException: If token is invalid or admin not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        admin_id: str = payload.get("sub")
        if admin_id is None:
            raise credentials_exception

        # Check if token is refresh token
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cannot use refresh token for authentication"
            )

    except JWTError as e:
        logger.error("jwt_decode_failed", error=str(e))
        raise credentials_exception

    # Get admin from database
    admin = db.query(Admin).filter(Admin.id == admin_id).first()

    if admin is None:
        raise credentials_exception

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive"
        )

    logger.debug("admin_authenticated", admin_id=str(admin.id), username=admin.username)
    return admin


def require_role(*roles: AdminRole):
    """
    Dependency factory to require specific admin roles

    Args:
        *roles: Required admin roles

    Returns:
        Dependency function
    """
    async def role_checker(current_admin: Admin = Depends(get_current_admin)) -> Admin:
        """Check if admin has required role"""
        if current_admin.role not in roles:
            # Check role hierarchy
            has_permission = any(current_admin.has_permission(role) for role in roles)

            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {[r.value for r in roles]}"
                )

        return current_admin

    return role_checker


async def get_current_session(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to get current voting session

    Args:
        credentials: HTTP bearer token
        db: Database session

    Returns:
        dict: Session data with voter_id, election_id, constituency_id, session_id

    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid voting session",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Log received token for debugging
    received_token = credentials.credentials
    logger.info(
        "voting_session_token_received",
        token_length=len(received_token),
        token_full=received_token,
        secret_prefix=settings.VOTING_SESSION_SECRET[:10] if settings.VOTING_SESSION_SECRET else "NONE",
        algorithm=settings.JWT_ALGORITHM
    )

    try:
        # Decode voting session token
        payload = jwt.decode(
            received_token,
            settings.VOTING_SESSION_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        logger.info("voting_session_token_decoded_successfully", payload=payload)

        # Verify token type
        if payload.get("type") != "voting_session":
            logger.error("invalid_token_type", token_type=payload.get("type"))
            raise credentials_exception

        # Extract session data
        session_data = {
            "voter_id": payload.get("voter_id"),
            "election_id": payload.get("election_id"),
            "constituency_id": payload.get("constituency_id"),
            "session_id": payload.get("session_id")
        }

        if not all(session_data.values()):
            logger.error("incomplete_session_data", session_data=session_data)
            raise credentials_exception

        # Verify voter exists and hasn't voted
        voter = db.query(Voter).filter(Voter.voter_id == session_data["voter_id"]).first()

        if not voter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voter not found"
            )

        if voter.has_voted:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Voter has already cast vote"
            )

        if voter.locked_out:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voter is locked out"
            )

        logger.info("voting_session_validated", voter_id=session_data["voter_id"])
        return session_data

    except JWTError as e:
        logger.error(
            "voting_session_decode_failed",
            error=str(e),
            error_type=type(e).__name__,
            token_preview=received_token[:50]
        )
        raise credentials_exception


def decode_refresh_token(token: str) -> dict:
    """
    Decode and validate refresh token

    Args:
        token: JWT refresh token

    Returns:
        dict: Token payload

    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

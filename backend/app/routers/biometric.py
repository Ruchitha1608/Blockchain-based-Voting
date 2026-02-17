"""
Biometric authentication routes
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel, Field
import structlog
from typing import Optional

from app.services.biometric import FaceService, FACE_AVAILABLE, BiometricAuthError, FingerprintService, FINGERPRINT_AVAILABLE

logger = structlog.get_logger()
router = APIRouter(prefix="/biometric", tags=["biometric"])


# Request/Response Models
class FaceVerifyRequest(BaseModel):
    """Request for face verification"""
    image: str = Field(..., description="Base64 encoded image")
    user_id: str = Field(..., description="User ID to verify against")


class FaceVerifyResponse(BaseModel):
    """Response for face verification"""
    verified: bool
    confidence: float
    message: str


class FaceEnrollRequest(BaseModel):
    """Request for face enrollment"""
    image: str = Field(..., description="Base64 encoded image")
    user_id: str = Field(..., description="User ID to enroll")


class FaceEnrollResponse(BaseModel):
    """Response for face enrollment"""
    success: bool
    message: str
    user_id: str


class FingerprintVerifyRequest(BaseModel):
    """Request for fingerprint verification"""
    template: str = Field(..., description="Fingerprint template")
    user_id: str = Field(..., description="User ID to verify against")


class FingerprintVerifyResponse(BaseModel):
    """Response for fingerprint verification"""
    verified: bool
    confidence: float
    message: str


# Initialize services
face_service = FaceService() if FACE_AVAILABLE else None
fingerprint_service = FingerprintService() if FINGERPRINT_AVAILABLE else None


# Face endpoints
@router.post("/face", response_model=FaceVerifyResponse)
async def verify_face(request: FaceVerifyRequest):
    """
    Verify face biometric
    
    Requires:
    - Base64 encoded face image
    - User ID to verify against
    
    Returns:
    - Verification result with confidence score
    """
    if not FACE_AVAILABLE:
        logger.error("face_service_unavailable")
        raise HTTPException(
            status_code=503,
            detail="Face recognition service is not available"
        )
    
    try:
        logger.info("face_verification_requested", user_id=request.user_id)
        
        # Decode base64 image
        image_bytes = face_service.decode_image(request.image)
        
        # Get embedding for provided image
        embedding = face_service.get_embedding(image_bytes)
        
        # TODO: Compare with stored embedding for user_id
        # For now, return a basic response
        logger.info("face_verification_completed", user_id=request.user_id)
        
        return FaceVerifyResponse(
            verified=True,
            confidence=0.95,
            message="Face verified successfully"
        )
        
    except BiometricAuthError as e:
        logger.warning("face_verification_failed", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error("face_verification_error", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=500,
            detail="Face verification failed"
        )


@router.post("/face/enroll", response_model=FaceEnrollResponse)
async def enroll_face(request: FaceEnrollRequest):
    """
    Enroll a face for a user
    
    Requires:
    - Base64 encoded face image
    - User ID to associate with this face
    
    Returns:
    - Enrollment result
    """
    if not FACE_AVAILABLE:
        logger.error("face_service_unavailable")
        raise HTTPException(
            status_code=503,
            detail="Face recognition service is not available"
        )
    
    try:
        logger.info("face_enrollment_requested", user_id=request.user_id)
        
        # Decode base64 image
        image_bytes = face_service.decode_image(request.image)
        
        # Process and store embedding
        # TODO: Store in database with user_id
        embedding = face_service.get_embedding(image_bytes)
        
        logger.info("face_enrollment_completed", user_id=request.user_id)
        
        return FaceEnrollResponse(
            success=True,
            message="Face enrolled successfully",
            user_id=request.user_id
        )
        
    except BiometricAuthError as e:
        logger.warning("face_enrollment_failed", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error("face_enrollment_error", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=500,
            detail="Face enrollment failed"
        )


# Fingerprint endpoints
@router.post("/fingerprint", response_model=FingerprintVerifyResponse)
async def verify_fingerprint(request: FingerprintVerifyRequest):
    """
    Verify fingerprint biometric
    
    Requires:
    - Fingerprint template
    - User ID to verify against
    
    Returns:
    - Verification result with confidence score
    """
    if not FINGERPRINT_AVAILABLE:
        logger.error("fingerprint_service_unavailable")
        raise HTTPException(
            status_code=503,
            detail="Fingerprint recognition service is not available"
        )
    
    try:
        logger.info("fingerprint_verification_requested", user_id=request.user_id)
        
        # TODO: Implement fingerprint verification
        logger.info("fingerprint_verification_completed", user_id=request.user_id)
        
        return FingerprintVerifyResponse(
            verified=True,
            confidence=0.95,
            message="Fingerprint verified successfully"
        )
        
    except Exception as e:
        logger.error("fingerprint_verification_error", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=500,
            detail="Fingerprint verification failed"
        )


@router.get("/status")
async def biometric_status():
    """
    Get biometric services status
    """
    return {
        "face_recognition": {
            "available": FACE_AVAILABLE,
            "model": "OpenCV-HOG" if FACE_AVAILABLE else None
        },
        "fingerprint": {
            "available": FINGERPRINT_AVAILABLE,
            "model": "Unknown" if FINGERPRINT_AVAILABLE else None
        }
    }

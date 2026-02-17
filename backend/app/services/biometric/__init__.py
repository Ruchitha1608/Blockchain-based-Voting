"""
Biometric authentication services
"""


class BiometricAuthError(Exception):
    """Custom exception for biometric authentication errors"""
    pass


# Optional imports - services only available if dependencies installed
try:
    from app.services.biometric.face import FaceService
    FACE_AVAILABLE = True
except ImportError:
    FaceService = None
    FACE_AVAILABLE = False

try:
    from app.services.biometric.fingerprint import FingerprintService
    FINGERPRINT_AVAILABLE = True
except ImportError:
    FingerprintService = None
    FINGERPRINT_AVAILABLE = False

__all__ = [
    "BiometricAuthError",
    "FaceService",
    "FingerprintService",
    "FACE_AVAILABLE",
    "FINGERPRINT_AVAILABLE",
]

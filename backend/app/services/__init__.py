"""
Service layer for business logic
"""
from app.services.crypto import (
    hash_biometric,
    generate_salt,
    derive_blockchain_voter_id,
    hash_password,
    verify_password,
    encrypt_biometric,
    decrypt_biometric
)
from app.services.blockchain import BlockchainService

# Optional imports for biometric services (require DeepFace/OpenCV)
try:
    from app.services.biometric.face import FaceService
    FACE_SERVICE_AVAILABLE = True
except ImportError:
    FaceService = None
    FACE_SERVICE_AVAILABLE = False

try:
    from app.services.biometric.fingerprint import FingerprintService
    FINGERPRINT_SERVICE_AVAILABLE = True
except ImportError:
    FingerprintService = None
    FINGERPRINT_SERVICE_AVAILABLE = False

__all__ = [
    "hash_biometric",
    "generate_salt",
    "derive_blockchain_voter_id",
    "hash_password",
    "verify_password",
    "encrypt_biometric",
    "decrypt_biometric",
    "BlockchainService",
    "FaceService",
    "FingerprintService",
    "FACE_SERVICE_AVAILABLE",
    "FINGERPRINT_SERVICE_AVAILABLE",
]

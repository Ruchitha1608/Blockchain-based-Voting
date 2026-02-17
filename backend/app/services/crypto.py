"""
Cryptographic utilities for biometric hashing, password hashing, and encryption
"""
import hashlib
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from eth_utils import keccak
import base64
import structlog

from app.config import settings

logger = structlog.get_logger()

# Initialize Argon2id password hasher
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)


def hash_biometric(template_bytes: bytes, salt: str) -> str:
    """
    Hash biometric template using SHA-256 with pepper and salt

    Args:
        template_bytes: Raw biometric template bytes
        salt: Unique salt for this biometric data

    Returns:
        str: Hexadecimal hash string
    """
    try:
        # Combine template + pepper + salt
        data = template_bytes + settings.BIOMETRIC_SALT_PEPPER.encode() + salt.encode()

        # SHA-256 hash
        hash_obj = hashlib.sha256(data)
        hash_hex = hash_obj.hexdigest()

        logger.debug("biometric_hashed", hash_length=len(hash_hex))
        return hash_hex

    except Exception as e:
        logger.error("biometric_hash_failed", error=str(e))
        raise


def generate_salt() -> str:
    """
    Generate a cryptographically secure random salt

    Returns:
        str: 32-byte hex-encoded salt
    """
    return secrets.token_hex(32)


def derive_blockchain_voter_id(voter_id: str) -> str:
    """
    Derive blockchain voter ID using keccak256 for anonymity

    Args:
        voter_id: Original voter ID

    Returns:
        str: 0x-prefixed keccak256 hash
    """
    try:
        # Combine voter_id with blockchain pepper
        data = voter_id + settings.BLOCKCHAIN_PEPPER
        data_bytes = data.encode('utf-8')

        # Keccak256 hash
        hash_bytes = keccak(data_bytes)
        hash_hex = "0x" + hash_bytes.hex()

        logger.debug("blockchain_voter_id_derived", length=len(hash_hex))
        return hash_hex

    except Exception as e:
        logger.error("blockchain_voter_id_derivation_failed", error=str(e))
        raise


def hash_password(password: str) -> str:
    """
    Hash password using Argon2id

    Args:
        password: Plain text password

    Returns:
        str: Argon2id hash
    """
    try:
        password_hash = ph.hash(password)
        logger.debug("password_hashed")
        return password_hash

    except Exception as e:
        logger.error("password_hash_failed", error=str(e))
        raise


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify password against Argon2id hash

    Args:
        password: Plain text password
        password_hash: Stored Argon2id hash

    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        ph.verify(password_hash, password)
        logger.debug("password_verified")
        return True

    except VerifyMismatchError:
        logger.debug("password_verification_failed")
        return False

    except Exception as e:
        logger.error("password_verification_error", error=str(e))
        return False


def encrypt_biometric(template_bytes: bytes) -> str:
    """
    Encrypt biometric template using AES-256-GCM

    Args:
        template_bytes: Raw biometric template bytes

    Returns:
        str: Base64-encoded encrypted data (nonce + ciphertext + tag)
    """
    try:
        # Ensure key is exactly 32 bytes
        key = settings.BIOMETRIC_ENCRYPTION_KEY.encode('utf-8')[:32]

        # Initialize AES-GCM cipher
        aesgcm = AESGCM(key)

        # Generate random nonce (12 bytes for GCM)
        nonce = secrets.token_bytes(12)

        # Encrypt
        ciphertext = aesgcm.encrypt(nonce, template_bytes, None)

        # Combine nonce + ciphertext for storage
        encrypted_data = nonce + ciphertext

        # Base64 encode for storage
        encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')

        logger.debug("biometric_encrypted", length=len(encrypted_b64))
        return encrypted_b64

    except Exception as e:
        logger.error("biometric_encryption_failed", error=str(e))
        raise


def decrypt_biometric(encrypted_b64: str) -> bytes:
    """
    Decrypt biometric template using AES-256-GCM

    Args:
        encrypted_b64: Base64-encoded encrypted data

    Returns:
        bytes: Decrypted biometric template bytes
    """
    try:
        # Ensure key is exactly 32 bytes
        key = settings.BIOMETRIC_ENCRYPTION_KEY.encode('utf-8')[:32]

        # Initialize AES-GCM cipher
        aesgcm = AESGCM(key)

        # Base64 decode
        encrypted_data = base64.b64decode(encrypted_b64.encode('utf-8'))

        # Extract nonce (first 12 bytes)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        # Decrypt
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        logger.debug("biometric_decrypted", length=len(plaintext))
        return plaintext

    except Exception as e:
        logger.error("biometric_decryption_failed", error=str(e))
        raise


def quantize_embedding(embedding_array, dtype='int8'):
    """
    Quantize floating-point embedding to int8 for compact storage

    Args:
        embedding_array: NumPy array of floats
        dtype: Target data type

    Returns:
        bytes: Quantized embedding as bytes
    """
    import numpy as np

    try:
        # Normalize to [-1, 1] range
        embedding_normalized = embedding_array / (np.abs(embedding_array).max() + 1e-8)

        # Quantize to int8 range [-128, 127]
        embedding_quantized = (embedding_normalized * 127).astype(dtype)

        # Convert to bytes
        embedding_bytes = embedding_quantized.tobytes()

        logger.debug("embedding_quantized", original_size=embedding_array.nbytes, quantized_size=len(embedding_bytes))
        return embedding_bytes

    except Exception as e:
        logger.error("embedding_quantization_failed", error=str(e))
        raise


def dequantize_embedding(embedding_bytes, shape, dtype='int8'):
    """
    Dequantize int8 embedding back to float32

    Args:
        embedding_bytes: Quantized embedding bytes
        shape: Original embedding shape
        dtype: Quantized data type

    Returns:
        numpy.ndarray: Float32 embedding array
    """
    import numpy as np

    try:
        # Convert bytes to numpy array
        embedding_quantized = np.frombuffer(embedding_bytes, dtype=dtype).reshape(shape)

        # Dequantize back to float32
        embedding_float = embedding_quantized.astype('float32') / 127.0

        logger.debug("embedding_dequantized", shape=embedding_float.shape)
        return embedding_float

    except Exception as e:
        logger.error("embedding_dequantization_failed", error=str(e))
        raise

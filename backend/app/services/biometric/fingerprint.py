"""
Fingerprint recognition service using OpenCV processing pipeline
"""
import base64
import io
import numpy as np
import cv2
from PIL import Image
import structlog

from app.config import settings
from app.services.crypto import hash_biometric, encrypt_biometric, decrypt_biometric, quantize_embedding, dequantize_embedding
from app.services.biometric.face import BiometricAuthError

logger = structlog.get_logger()


class FingerprintService:
    """
    Fingerprint recognition service using OpenCV processing pipeline
    """

    def __init__(self):
        self.threshold = settings.FINGERPRINT_THRESHOLD
        self.sdk = settings.FINGERPRINT_SDK

    def process_fingerprint(self, image_bytes: bytes) -> bytes:
        """
        Process fingerprint image using simple image comparison approach
        Similar to face recognition - resize, normalize, and flatten

        Args:
            image_bytes: Raw fingerprint image bytes

        Returns:
            bytes: Processed fingerprint template as feature vector bytes
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                raise BiometricAuthError("Invalid fingerprint image")

            # Step 1: Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Step 2: Resize to standard size for consistent comparison
            resized = cv2.resize(gray, (128, 128))

            # Step 3: Normalize pixel values to [0, 1]
            normalized = resized.astype(np.float32) / 255.0

            # Step 4: Apply histogram equalization for better feature extraction
            equalized = cv2.equalizeHist((normalized * 255).astype(np.uint8))
            final = equalized.astype(np.float32) / 255.0

            # Step 5: Flatten to create embedding vector (128*128 = 16,384 elements)
            embedding = final.flatten()

            # Convert to bytes
            feature_bytes = embedding.tobytes()

            logger.info("fingerprint_processed", feature_size=len(feature_bytes))
            return feature_bytes

        except BiometricAuthError:
            raise

        except Exception as e:
            logger.error("fingerprint_processing_failed", error=str(e))
            raise BiometricAuthError(f"Fingerprint processing failed: {str(e)}")


    def process_and_store_template(self, image_bytes: bytes, salt: str) -> tuple[str, str]:
        """
        Process fingerprint and prepare for storage

        Args:
            image_bytes: Raw fingerprint image bytes
            salt: Unique salt for this biometric data

        Returns:
            tuple: (hash_hex, encrypted_quantized_template)
        """
        try:
            # Process fingerprint
            template_bytes = self.process_fingerprint(image_bytes)

            # Create hash for integrity verification
            hash_hex = hash_biometric(template_bytes, salt)

            # Convert bytes to array for quantization
            template_array = np.frombuffer(template_bytes, dtype=np.float32)

            # Quantize and encrypt
            quantized = quantize_embedding(template_array, dtype='int8')
            encrypted = encrypt_biometric(quantized)

            logger.info("fingerprint_template_processed", hash_length=len(hash_hex))
            return hash_hex, encrypted

        except Exception as e:
            logger.error("fingerprint_template_processing_failed", error=str(e))
            raise

    def compare_fingerprints(
        self,
        live_template: bytes,
        stored_hash: str,
        stored_encrypted: str,
        salt: str
    ) -> tuple[bool, float]:
        """
        Compare live fingerprint with stored template

        Args:
            live_template: Live fingerprint template from authentication
            stored_hash: Stored SHA-256 hash
            stored_encrypted: Stored encrypted quantized template
            salt: Salt used for hashing

        Returns:
            tuple: (matched: bool, similarity_score: float)
        """
        try:
            # Decrypt stored template
            decrypted_bytes = decrypt_biometric(stored_encrypted)

            # Convert live template to array
            live_array = np.frombuffer(live_template, dtype=np.float32)

            # Dequantize stored template
            stored_array = dequantize_embedding(decrypted_bytes, shape=live_array.shape, dtype='int8')

            # Calculate similarity using normalized correlation
            similarity = self._calculate_similarity(live_array, stored_array)

            # Check threshold
            matched = similarity >= self.threshold

            logger.info("fingerprint_comparison_complete", matched=matched, similarity=round(similarity, 4))
            return matched, float(similarity)

        except Exception as e:
            logger.error("fingerprint_comparison_failed", error=str(e))
            return False, 0.0

    @staticmethod
    def _calculate_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two fingerprint embeddings
        Same approach as face recognition for consistency
        """
        if a.shape != b.shape:
            return 0.0

        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        similarity = dot_product / (norm_a * norm_b)

        # Clamp to [0, 1] range
        similarity = max(0.0, min(1.0, similarity))

        return similarity

    def decode_image(self, base64_image: str) -> bytes:
        """Decode base64 fingerprint image to bytes"""
        try:
            if ',' in base64_image:
                base64_image = base64_image.split(',')[1]

            image_bytes = base64.b64decode(base64_image)
            return image_bytes

        except Exception as e:
            logger.error("fingerprint_decode_failed", error=str(e))
            raise BiometricAuthError("Invalid fingerprint image format")

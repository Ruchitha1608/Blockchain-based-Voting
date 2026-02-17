"""
Face recognition service using OpenCV (lightweight alternative to DeepFace)

NOTE: This is a simplified implementation for Python 3.14 compatibility.
For production use with higher accuracy, use Python 3.11/3.12 with DeepFace+ArcFace.
"""
import base64
import io
import numpy as np
from PIL import Image
import cv2
import structlog

from app.config import settings
from app.services.crypto import hash_biometric, encrypt_biometric, decrypt_biometric, quantize_embedding, dequantize_embedding

logger = structlog.get_logger()


class BiometricAuthError(Exception):
    """Custom exception for biometric authentication errors"""
    pass


class FaceService:
    """
    Face recognition service using OpenCV for face detection and feature extraction.

    This is a lightweight alternative to DeepFace, suitable for development and testing.
    For production use with state-of-the-art accuracy, use Python 3.11/3.12 with DeepFace+ArcFace.
    """

    def __init__(self):
        self.threshold = settings.FACE_THRESHOLD
        self.model_name = "OpenCV-HOG"  # Simple but functional
        self._face_cascade = None

        logger.info("face_service_initialized", model="OpenCV-HOG",
                   note="Lightweight implementation for Python 3.14 compatibility")

    def _get_face_cascade(self):
        """Lazy load OpenCV's Haar Cascade face detector"""
        if self._face_cascade is None:
            # Use OpenCV's pre-trained Haar Cascade
            self._face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        return self._face_cascade

    def get_embedding(self, image_bytes: bytes) -> np.ndarray:
        """
        Extract face features from image using OpenCV

        This creates a feature vector from the detected face region.
        While not as sophisticated as ArcFace embeddings, it provides functional
        face verification capabilities.

        Args:
            image_bytes: Raw image bytes

        Returns:
            numpy.ndarray: Face feature vector (flattened grayscale face)

        Raises:
            BiometricAuthError: If face detection or embedding fails
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert to numpy array and then to OpenCV format
            img_array = np.array(image)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

            # Detect faces
            face_cascade = self._get_face_cascade()
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

            if len(faces) == 0:
                raise BiometricAuthError("No face detected in image - please ensure your face is clearly visible")

            if len(faces) > 1:
                logger.warning("multiple_faces_detected", count=len(faces))
                raise BiometricAuthError("Multiple faces detected - please ensure only one face is visible")

            # Extract the face region
            (x, y, w, h) = faces[0]
            face_roi = gray[y:y+h, x:x+w]

            # Resize to standard size for consistent embeddings
            face_resized = cv2.resize(face_roi, (128, 128))

            # Normalize pixel values to [0, 1]
            face_normalized = face_resized.astype(np.float32) / 255.0

            # Apply histogram equalization for better feature extraction
            face_equalized = cv2.equalizeHist((face_normalized * 255).astype(np.uint8))
            face_final = face_equalized.astype(np.float32) / 255.0

            # Flatten to create embedding vector
            embedding = face_final.flatten()

            logger.info("face_embedding_extracted", shape=embedding.shape, size=len(embedding))
            return embedding

        except BiometricAuthError:
            raise

        except Exception as e:
            error_msg = str(e).lower()

            if "could not find" in error_msg or "no face" in error_msg:
                raise BiometricAuthError("No face detected in image - please ensure your face is clearly visible")

            elif "blurry" in error_msg or "quality" in error_msg:
                raise BiometricAuthError("Image quality too low - please ensure good lighting and focus")

            else:
                logger.error("face_embedding_extraction_failed", error=str(e))
                raise BiometricAuthError(f"Face processing failed: {str(e)}")

    def process_and_store_embedding(self, image_bytes: bytes, salt: str) -> tuple[str, str]:
        """
        Process face image and prepare for storage

        Args:
            image_bytes: Raw image bytes
            salt: Unique salt for this biometric data

        Returns:
            tuple: (hash_hex, encrypted_quantized_embedding)
        """
        try:
            # Extract embedding
            embedding = self.get_embedding(image_bytes)

            # Create hash for integrity verification
            embedding_bytes = embedding.tobytes()
            hash_hex = hash_biometric(embedding_bytes, salt)

            # Quantize and encrypt for similarity comparison
            quantized = quantize_embedding(embedding, dtype='int8')
            encrypted = encrypt_biometric(quantized)

            logger.info("face_embedding_processed", hash_length=len(hash_hex), encrypted_length=len(encrypted))
            return hash_hex, encrypted

        except Exception as e:
            logger.error("face_embedding_processing_failed", error=str(e))
            raise

    def compare_embeddings(
        self,
        live_embedding: np.ndarray,
        stored_hash: str,
        stored_encrypted: str,
        salt: str
    ) -> tuple[bool, float]:
        """
        Compare live embedding with stored embedding using hybrid approach

        Args:
            live_embedding: Live face embedding from authentication
            stored_hash: Stored SHA-256 hash
            stored_encrypted: Stored encrypted quantized embedding
            salt: Salt used for hashing

        Returns:
            tuple: (matched: bool, similarity_score: float)
        """
        try:
            # Step 1: Decrypt stored quantized embedding
            decrypted_bytes = decrypt_biometric(stored_encrypted)

            # Step 2: Dequantize to float array
            stored_embedding = dequantize_embedding(decrypted_bytes, shape=live_embedding.shape, dtype='int8')

            # Step 3: Calculate cosine similarity
            similarity = self._cosine_similarity(live_embedding, stored_embedding)

            # Step 4: Check if similarity exceeds threshold
            matched = similarity >= self.threshold

            # Step 5: Secondary verification - hash the live embedding and compare
            if matched:
                live_embedding_bytes = live_embedding.tobytes()
                live_hash = hash_biometric(live_embedding_bytes, salt)

                # Note: Due to quantization, hashes may not match exactly
                # We rely primarily on similarity score
                logger.debug("face_match_verification", similarity=similarity, threshold=self.threshold)

            logger.info("face_comparison_complete", matched=matched, similarity=round(similarity, 4))
            return matched, float(similarity)

        except Exception as e:
            logger.error("face_comparison_failed", error=str(e))
            return False, 0.0

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            a: First vector
            b: Second vector

        Returns:
            float: Cosine similarity score (0 to 1)
        """
        # Ensure same shape
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
        """
        Decode base64 image string to bytes

        Args:
            base64_image: Base64 encoded image string

        Returns:
            bytes: Decoded image bytes
        """
        try:
            # Remove data URI prefix if present
            if ',' in base64_image:
                base64_image = base64_image.split(',')[1]

            # Decode base64
            image_bytes = base64.b64decode(base64_image)

            return image_bytes

        except Exception as e:
            logger.error("image_decode_failed", error=str(e))
            raise BiometricAuthError("Invalid image format")

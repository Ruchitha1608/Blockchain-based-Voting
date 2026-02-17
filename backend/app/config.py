"""
Application configuration using Pydantic BaseSettings
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://voting_user:voting_pass@localhost:5432/voting_db",
        description="PostgreSQL connection URL"
    )

    # Blockchain Configuration
    GANACHE_URL: str = Field(
        default="http://localhost:8545",
        description="Ganache/Ethereum node URL"
    )
    GANACHE_NETWORK_ID: int = Field(default=1337, description="Network ID")

    # JWT Configuration
    JWT_SECRET: str = Field(
        default="change-this-secret-in-production-minimum-256-bits",
        description="Secret key for JWT signing",
        min_length=32
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )

    # Voting Session Configuration
    VOTING_SESSION_SECRET: str = Field(
        default="change-this-voting-session-secret",
        description="Separate secret for voting session tokens",
        min_length=32
    )

    # Biometric Configuration
    BIOMETRIC_SALT_PEPPER: str = Field(
        default="change-this-biometric-pepper",
        description="Pepper for biometric hashing",
        min_length=16
    )
    BIOMETRIC_ENCRYPTION_KEY: str = Field(
        default="change-this-key-must-be-32-bytes",
        description="AES-256 encryption key for biometric data",
        min_length=32,
        max_length=32
    )
    FACE_MODEL: str = Field(default="ArcFace", description="Face recognition model")
    FACE_THRESHOLD: float = Field(
        default=0.68,
        ge=0.0,
        le=1.0,
        description="Face similarity threshold"
    )
    FINGERPRINT_SDK: str = Field(default="opencv", description="Fingerprint SDK")
    FINGERPRINT_THRESHOLD: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Fingerprint similarity threshold"
    )

    # Blockchain Pepper (for voter ID hashing)
    BLOCKCHAIN_PEPPER: str = Field(
        default="change-this-blockchain-pepper",
        description="Pepper for blockchain voter ID generation",
        min_length=16
    )

    # Security Configuration
    MAX_AUTH_ATTEMPTS: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum failed authentication attempts before lockout"
    )
    SESSION_TIMEOUT_SECONDS: int = Field(
        default=120,
        ge=30,
        le=600,
        description="Session timeout for polling booth"
    )
    LOCKOUT_DURATION_MINUTES: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Lockout duration after max failed attempts"
    )

    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for session management"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json or text)")

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )

    # Application
    APP_NAME: str = Field(
        default="Blockchain Voting System",
        description="Application name"
    )
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")

    @field_validator("BIOMETRIC_ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key_length(cls, v: str) -> str:
        """Ensure encryption key is exactly 32 bytes"""
        if len(v.encode()) != 32:
            raise ValueError("Encryption key must be exactly 32 bytes")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @field_validator("LOG_FORMAT")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Ensure log format is valid"""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of {valid_formats}")
        return v.lower()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

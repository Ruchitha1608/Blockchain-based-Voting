"""
Main FastAPI application entry point
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import sys

from app.config import settings
from app.database import check_db_connection, engine
from app.services.blockchain import blockchain_service, BlockchainError
from app.services.biometric import BiometricAuthError

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json"
        else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("application_starting", version=settings.APP_VERSION)

    # Check database connection
    if not check_db_connection():
        logger.warning("database_connection_failed_on_startup",
                      message="Database not available. Some features may not work.")
    else:
        logger.info("database_connected")

    # Check blockchain connection
    try:
        if blockchain_service.web3.is_connected():
            logger.info("blockchain_connected", url=settings.GANACHE_URL)
        else:
            logger.warning("blockchain_not_connected")
    except Exception as e:
        logger.warning("blockchain_check_failed", error=str(e))

    yield

    # Shutdown
    logger.info("application_shutting_down")

    # Close database connections
    engine.dispose()
    logger.info("database_connections_closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Blockchain-based voting system with biometric authentication",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(BlockchainError)
async def blockchain_error_handler(request: Request, exc: BlockchainError):
    """Handle blockchain errors"""
    logger.error("blockchain_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Blockchain operation failed",
            "code": "BLOCKCHAIN_ERROR",
            "details": {"message": str(exc)}
        }
    )


@app.exception_handler(BiometricAuthError)
async def biometric_auth_error_handler(request: Request, exc: BiometricAuthError):
    """Handle biometric authentication errors"""
    logger.warning("biometric_auth_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=400,
        content={
            "error": "Biometric authentication failed",
            "code": "BIOMETRIC_AUTH_ERROR",
            "details": {"message": str(exc)}
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error("unhandled_exception", error=str(exc), path=request.url.path, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "details": {"message": "An unexpected error occurred"}
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers
    """
    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "checks": {}
    }

    # Check database
    db_healthy = check_db_connection()
    health_status["checks"]["database"] = "healthy" if db_healthy else "unhealthy"

    # Check blockchain
    try:
        blockchain_healthy = blockchain_service.web3.is_connected()
        health_status["checks"]["blockchain"] = "healthy" if blockchain_healthy else "unhealthy"
    except:
        health_status["checks"]["blockchain"] = "unhealthy"

    # Overall status
    if not all(v == "healthy" for v in health_status["checks"].values()):
        health_status["status"] = "degraded"

    return health_status


# System info endpoint
@app.get("/api/info")
async def system_info():
    """
    Get system information
    """
    try:
        # Get blockchain info
        blockchain_info = {}
        if blockchain_service.web3.is_connected():
            blockchain_info = {
                "connected": True,
                "url": settings.GANACHE_URL,
                "network_id": settings.GANACHE_NETWORK_ID,
                "contracts_loaded": {
                    "voter_registry": blockchain_service.voter_registry is not None,
                    "voting_booth": blockchain_service.voting_booth is not None,
                    "results_tallier": blockchain_service.results_tallier is not None,
                    "election_controller": blockchain_service.election_controller is not None
                }
            }
        else:
            blockchain_info = {"connected": False}

        return {
            "application": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": "development" if settings.DEBUG else "production"
            },
            "blockchain": blockchain_info,
            "database": {
                "connected": check_db_connection()
            },
            "biometrics": {
                "face_model": settings.FACE_MODEL,
                "face_threshold": settings.FACE_THRESHOLD,
                "fingerprint_sdk": settings.FINGERPRINT_SDK,
                "fingerprint_threshold": settings.FINGERPRINT_THRESHOLD
            },
            "security": {
                "max_auth_attempts": settings.MAX_AUTH_ATTEMPTS,
                "session_timeout_seconds": settings.SESSION_TIMEOUT_SECONDS
            }
        }

    except Exception as e:
        logger.error("system_info_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve system information")


# Import and include routers
from app.routers import auth, voters, voting, elections, biometric, audit

app.include_router(auth.router)
app.include_router(voters.router)
app.include_router(voting.router)
app.include_router(elections.router)
app.include_router(biometric.router)
app.include_router(audit.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

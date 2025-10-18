"""FastAPI application entry point"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import webhook

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("🚀 Starting Notion to Slack webhook adapter")
    logger.info(f"📍 Server: {settings.host}:{settings.port}")
    logger.info(f"🔗 Slack webhook configured: {bool(settings.slack_webhook_url)}")

    yield

    logger.info("👋 Shutting down Notion to Slack webhook adapter")


# Create FastAPI application
app = FastAPI(
    title="Notion to Slack Webhook Adapter",
    description="Converts Notion webhook button payloads to Slack incoming webhook format",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhook.router, prefix="/api", tags=["webhook"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Notion to Slack Webhook Adapter",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "notion_to_slack": "/api/notion-to-slack",
            "test": "/api/test",
            "health": "/api/health",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level,
    )

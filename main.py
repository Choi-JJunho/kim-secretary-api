"""FastAPI 애플리케이션 진입점"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import webhook

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 수명 주기 관리

    서버 시작 시와 종료 시 실행되는 로직을 정의합니다.

    Args:
        app: FastAPI 애플리케이션 인스턴스

    Yields:
        애플리케이션이 실행되는 동안 제어권 반환
    """
    # 시작 로직
    logger.info("🚀 Notion to Slack 웹훅 어댑터 시작")
    logger.info(f"📍 서버: {settings.host}:{settings.port}")
    logger.info(f"🔗 Slack 웹훅 설정: {bool(settings.slack_webhook_url)}")
    logger.info(f"🔐 API 키 보호: {bool(settings.api_key)}")

    yield

    # 종료 로직
    logger.info("👋 Notion to Slack 웹훅 어댑터 종료")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="김비서 API - Notion to Slack Webhook Adapter",
    description="Notion 데이터베이스 버튼 웹훅을 Slack incoming webhook 형식으로 변환하는 API 서버",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(webhook.router, prefix="/api", tags=["webhook"])


@app.get("/")
async def root():
    """루트 엔드포인트

    API 서버의 기본 정보와 사용 가능한 엔드포인트를 반환합니다.

    Returns:
        서버 정보 및 엔드포인트 목록
    """
    return {
        "name": "김비서 API - Notion to Slack Webhook Adapter",
        "version": "0.1.0",
        "status": "running",
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "notion_to_slack": "/api/notion-to-slack",
            "test": "/api/test",
            "health": "/api/health",
        },
    }


if __name__ == "__main__":
    import uvicorn

    # 개발 서버 실행
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,  # 코드 변경 시 자동 재시작
        log_level=settings.log_level,
    )

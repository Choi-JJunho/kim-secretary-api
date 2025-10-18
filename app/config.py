"""애플리케이션 설정 관리"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정

    환경 변수(.env 파일)로부터 설정값을 로드합니다.

    Attributes:
        slack_webhook_url: Slack incoming webhook URL (필수)
        host: 서버 호스트 주소
        port: 서버 포트 번호 (1024-65535)
        log_level: 로그 레벨 (debug, info, warning, error)
        api_key: API 인증 키 (선택사항)
    """

    # Slack 설정
    slack_webhook_url: str = Field(..., description="Slack incoming webhook URL")

    # 서버 설정
    host: str = Field(default="0.0.0.0", description="서버 호스트 주소")
    port: int = Field(default=8000, ge=1024, le=65535, description="서버 포트 번호")
    log_level: str = Field(default="info", description="로그 레벨")

    # 보안 설정 (선택사항)
    api_key: str | None = Field(default=None, description="API 인증 키")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """로그 레벨 유효성 검증"""
        allowed = {"debug", "info", "warning", "error", "critical"}
        if v.lower() not in allowed:
            raise ValueError(f"log_level은 {allowed} 중 하나여야 합니다")
        return v.lower()

    @field_validator("slack_webhook_url")
    @classmethod
    def validate_slack_webhook_url(cls, v: str) -> str:
        """Slack webhook URL 유효성 검증"""
        if not v.startswith("https://hooks.slack.com/"):
            raise ValueError("유효한 Slack webhook URL이 아닙니다")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 알 수 없는 환경 변수 무시


# 전역 설정 인스턴스
settings = Settings()

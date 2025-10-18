"""애플리케이션 설정 관리"""

import json
from typing import Dict

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

    # Notion User to Database Mapping
    user_database_mapping: str = Field(
        default='{"default":"290b3645-abb5-803f-b2d6-d8577918ac2f"}',
        description="User ID와 Notion Database ID 매핑 (JSON 형식)"
    )

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

    @field_validator("user_database_mapping")
    @classmethod
    def validate_user_database_mapping(cls, v: str) -> str:
        """User-Database 매핑 JSON 유효성 검증"""
        try:
            mapping = json.loads(v)
            if not isinstance(mapping, dict):
                raise ValueError("USER_DATABASE_MAPPING은 JSON 객체여야 합니다")
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"USER_DATABASE_MAPPING JSON 파싱 실패: {e}")

    def get_all_database_ids(self) -> Dict[str, str]:
        """모든 User-Database 매핑 반환

        Returns:
            전체 매핑 딕셔너리
        """
        try:
            return json.loads(self.user_database_mapping)
        except json.JSONDecodeError:
            return {}

    def get_user_id_by_database(self, database_id: str) -> str | None:
        """Database ID로 User ID 역조회

        Args:
            database_id: Notion Database ID (하이픈 포함/미포함 모두 지원)

        Returns:
            해당하는 User ID (실제 user_id 우선, 없으면 None)
        """
        try:
            mapping: Dict[str, str] = json.loads(self.user_database_mapping)

            # 하이픈 제거한 버전으로 비교 (Notion ID는 하이픈 유무가 다를 수 있음)
            normalized_db_id = database_id.replace("-", "")

            # 'default'가 아닌 실제 user_id를 우선 반환
            matched_users = []
            for user_id, db_id in mapping.items():
                if db_id.replace("-", "") == normalized_db_id:
                    matched_users.append(user_id)

            # 'default'가 아닌 user_id가 있으면 그것을 반환
            for user_id in matched_users:
                if user_id != "default":
                    return user_id

            # 'default'만 있거나 매칭 없음 → None
            return None
        except (json.JSONDecodeError, AttributeError):
            return None

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 알 수 없는 환경 변수 무시


# 전역 설정 인스턴스
settings = Settings()

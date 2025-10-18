"""Notion 웹훅 및 Slack 페이로드를 위한 데이터 모델"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class WorkLogFeedbackRequest(BaseModel):
    """업무일지 피드백 요청 모델

    Slack webhook으로 전송될 업무일지 피드백 요청 데이터를 정의합니다.

    Attributes:
        action: 작업 타입 (고정값: "work_log_feedback")
        date: 업무일지 작성일 (YYYY-MM-DD 형식)
        ai_provider: AI 제공자 (gemini, claude, codex, ollama 중 하나)
        flavor: 피드백 스타일 (spicy, normal, mild 중 하나)
        user_id: Slack 사용자 ID (선택사항)
        database_id: Notion Database ID (하이픈 제거 형식, 선택사항)
    """

    action: str = Field(default="work_log_feedback", description="작업 타입")
    date: str = Field(..., description="업무일지 작성일 (YYYY-MM-DD)")
    ai_provider: str = Field(default="gemini", description="AI 제공자")
    flavor: str = Field(default="normal", description="피드백 스타일")
    user_id: Optional[str] = Field(default=None, description="Slack 사용자 ID")
    database_id: Optional[str] = Field(default=None, description="Notion Database ID (하이픈 제거)")

    @field_validator("ai_provider")
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        """AI 제공자 유효성 검증"""
        allowed = {"gemini", "claude", "codex", "ollama"}
        if v.lower() not in allowed:
            raise ValueError(f"ai_provider는 {allowed} 중 하나여야 합니다")
        return v.lower()

    @field_validator("flavor")
    @classmethod
    def validate_flavor(cls, v: str) -> str:
        """피드백 스타일 유효성 검증"""
        allowed = {"spicy", "normal", "mild"}
        if v.lower() not in allowed:
            raise ValueError(f"flavor는 {allowed} 중 하나여야 합니다")
        return v.lower()

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """날짜 형식 유효성 검증 (YYYY-MM-DD)"""
        from datetime import datetime
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("date는 YYYY-MM-DD 형식이어야 합니다")

    @field_validator("database_id")
    @classmethod
    def normalize_database_id(cls, v: Optional[str]) -> Optional[str]:
        """Database ID 정규화 (하이픈 제거)"""
        if v is None:
            return None
        return v.replace("-", "")


class SlackWebhookPayload(BaseModel):
    """Slack incoming webhook 페이로드

    Slack으로 메시지를 전송하기 위한 페이로드입니다.

    Attributes:
        text: 전송할 메시지 내용 (JSON 문자열 또는 일반 텍스트)
    """

    text: str = Field(..., description="전송할 메시지 내용")

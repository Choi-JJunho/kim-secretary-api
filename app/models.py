"""Data models for Notion webhook payloads"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class NotionDate(BaseModel):
    """Notion date property"""
    start: str
    end: Optional[str] = None


class NotionDateProperty(BaseModel):
    """Notion date property wrapper"""
    date: NotionDate


class NotionSelect(BaseModel):
    """Notion select property"""
    name: str
    color: Optional[str] = None


class NotionSelectProperty(BaseModel):
    """Notion select property wrapper"""
    select: NotionSelect


class NotionRichText(BaseModel):
    """Notion rich text"""
    plain_text: str


class NotionRichTextProperty(BaseModel):
    """Notion rich text property wrapper"""
    rich_text: list[NotionRichText]


class NotionProperties(BaseModel):
    """Notion database properties"""
    # Define expected properties here
    # Actual property names will be in Korean or custom names
    properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"  # Allow additional fields


class NotionWebhookPayload(BaseModel):
    """Notion webhook button payload"""
    # Notion sends nested structure
    # Exact structure TBD - need to test with actual webhook
    properties: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"  # Allow additional fields we don't know yet


class WorkLogFeedbackRequest(BaseModel):
    """Work log feedback request for Slack webhook"""
    action: str = "work_log_feedback"
    date: str
    ai_provider: str = "gemini"
    flavor: str = "normal"
    user_id: Optional[str] = None


class SlackWebhookPayload(BaseModel):
    """Slack incoming webhook payload"""
    text: str

"""Webhook endpoints for Notion to Slack conversion"""

import json
import logging
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse

from ..config import settings
from ..models import NotionWebhookPayload, WorkLogFeedbackRequest, SlackWebhookPayload

router = APIRouter()
logger = logging.getLogger(__name__)


def extract_property_value(prop: Any, prop_type: str) -> Any:
    """
    Extract value from Notion property based on type

    Args:
        prop: Notion property object
        prop_type: Property type (date, select, rich_text, etc.)

    Returns:
        Extracted value
    """
    if not prop:
        return None

    try:
        if prop_type == "date":
            return prop.get("date", {}).get("start")
        elif prop_type == "select":
            return prop.get("select", {}).get("name")
        elif prop_type == "rich_text":
            rich_text = prop.get("rich_text", [])
            return rich_text[0].get("plain_text") if rich_text else None
        elif prop_type == "title":
            title = prop.get("title", [])
            return title[0].get("plain_text") if title else None
        else:
            return str(prop)
    except Exception as e:
        logger.warning(f"Failed to extract {prop_type} property: {e}")
        return None


def convert_notion_to_work_log_request(notion_payload: Dict[str, Any]) -> WorkLogFeedbackRequest:
    """
    Convert Notion webhook payload to work log feedback request

    Args:
        notion_payload: Raw Notion webhook payload

    Returns:
        WorkLogFeedbackRequest object

    Raises:
        ValueError: If required fields are missing
    """
    logger.info(f"Converting Notion payload: {json.dumps(notion_payload, indent=2, ensure_ascii=False)}")

    properties = notion_payload.get("properties", {})

    # Extract required field: 작성일 (date)
    date_prop = properties.get("작성일") or properties.get("날짜") or properties.get("Date")
    date = extract_property_value(date_prop, "date")

    if not date:
        raise ValueError("Required field '작성일' not found in Notion payload")

    # Extract optional fields
    ai_provider_prop = properties.get("AI 제공자") or properties.get("AI") or properties.get("AI Provider")
    ai_provider = extract_property_value(ai_provider_prop, "select") or "gemini"

    flavor_prop = properties.get("맛") or properties.get("피드백 맛") or properties.get("Flavor")
    flavor = extract_property_value(flavor_prop, "select") or "normal"

    user_id_prop = properties.get("사용자 ID") or properties.get("User ID")
    user_id = extract_property_value(user_id_prop, "rich_text")

    return WorkLogFeedbackRequest(
        action="work_log_feedback",
        date=date,
        ai_provider=ai_provider.lower() if ai_provider else "gemini",
        flavor=flavor.lower() if flavor else "normal",
        user_id=user_id
    )


@router.post("/notion-to-slack")
async def handle_notion_webhook(
    request: Request,
    x_api_key: str = Header(None)
):
    """
    Handle Notion webhook and forward to Slack

    Receives Notion webhook button payload, converts it to work log feedback format,
    and forwards it to Slack incoming webhook.

    Args:
        request: FastAPI request object
        x_api_key: Optional API key for authentication

    Returns:
        Success message

    Raises:
        HTTPException: If conversion or forwarding fails
    """
    # Optional API key validation
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # Get raw payload
        notion_payload = await request.json()

        logger.info("📥 Received Notion webhook")
        logger.debug(f"Notion payload: {json.dumps(notion_payload, indent=2, ensure_ascii=False)}")

        # Convert to work log feedback request
        work_log_request = convert_notion_to_work_log_request(notion_payload)

        logger.info(f"✅ Converted to work log request: {work_log_request.model_dump()}")

        # Create Slack webhook payload
        slack_payload = SlackWebhookPayload(
            text=work_log_request.model_dump_json()
        )

        # Forward to Slack webhook
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.slack_webhook_url,
                json=slack_payload.model_dump(),
                timeout=10.0
            )
            response.raise_for_status()

        logger.info("🚀 Successfully forwarded to Slack webhook")

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Webhook forwarded to Slack",
                "work_log_request": work_log_request.model_dump()
            }
        )

    except ValueError as ve:
        logger.error(f"❌ Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except httpx.HTTPError as he:
        logger.error(f"❌ Failed to forward to Slack: {he}")
        raise HTTPException(status_code=502, detail=f"Failed to forward to Slack: {str(he)}")

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_webhook(payload: Dict[str, Any]):
    """
    Test endpoint to echo back the payload

    Use this to inspect what Notion sends when you click the webhook button.

    Args:
        payload: Any JSON payload

    Returns:
        The received payload
    """
    logger.info("📥 Test webhook received")
    logger.info(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Test webhook received",
            "received_payload": payload
        }
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

"""Notion 웹훅을 Slack 형식으로 변환하는 API 엔드포인트"""

import json
import logging
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse

from ..config import settings
from ..models import WorkLogFeedbackRequest, SlackWebhookPayload

router = APIRouter()
logger = logging.getLogger(__name__)


def extract_property_value(prop: Any, prop_type: str) -> Any:
    """Notion 속성에서 타입에 따라 값을 추출

    Args:
        prop: Notion 속성 객체
        prop_type: 속성 타입 (date, select, rich_text, title 등)

    Returns:
        추출된 값 (추출 실패 시 None)
    """
    if not prop:
        return None

    try:
        # 속성 타입별 값 추출 로직
        extractors = {
            "date": lambda p: p.get("date", {}).get("start"),
            "select": lambda p: p.get("select", {}).get("name"),
            "rich_text": lambda p: p.get("rich_text", [{}])[0].get("plain_text") if p.get("rich_text") else None,
            "title": lambda p: p.get("title", [{}])[0].get("plain_text") if p.get("title") else None,
        }

        extractor = extractors.get(prop_type)
        if extractor:
            return extractor(prop)

        # 알 수 없는 타입은 문자열로 변환
        logger.warning(f"알 수 없는 속성 타입: {prop_type}")
        return str(prop)

    except (KeyError, IndexError, AttributeError) as e:
        logger.warning(f"{prop_type} 속성 추출 실패: {e}")
        return None


def convert_notion_to_work_log_request(
    notion_payload: Dict[str, Any],
    taste_override: str = None
) -> WorkLogFeedbackRequest:
    """Notion 웹훅 페이로드를 업무일지 피드백 요청으로 변환

    Args:
        notion_payload: Notion에서 전송된 원본 웹훅 페이로드
        taste_override: Query parameter로 전달된 taste 값 (선택사항)

    Returns:
        변환된 WorkLogFeedbackRequest 객체

    Raises:
        ValueError: 필수 필드가 없거나 database_id 검증 실패
    """
    logger.info(f"Notion 페이로드 변환 중: {json.dumps(notion_payload, indent=2, ensure_ascii=False)}")

    # data.properties 객체에서 페이지 속성 추출
    data = notion_payload.get("data", {})
    properties = data.get("properties", {})

    # parent.database_id 추출
    parent = data.get("parent", {})
    database_id = parent.get("database_id")

    if database_id:
        logger.info(f"📊 Database ID: {database_id}")

    if not properties:
        raise ValueError("Notion 페이로드에 properties가 없습니다")

    # 필수 필드: 작성일 (date)
    date_prop = properties.get("작성일") or properties.get("날짜") or properties.get("Date")
    date = extract_property_value(date_prop, "date")

    if not date:
        raise ValueError("필수 필드 '작성일'을 찾을 수 없습니다")

    # 선택 필드: AI 제공자
    ai_provider_prop = properties.get("AI 제공자") or properties.get("AI") or properties.get("AI Provider")
    ai_provider = extract_property_value(ai_provider_prop, "select") or "claude"

    # 선택 필드: 피드백 맛 (taste_override가 있으면 우선 사용)
    if taste_override:
        flavor = taste_override
        logger.info(f"🌶️ Query parameter taste 사용: {flavor}")
    else:
        flavor_prop = properties.get("맛") or properties.get("피드백 맛") or properties.get("Flavor")
        flavor = extract_property_value(flavor_prop, "select") or "normal"

    # 선택 필드: 사용자 ID
    user_id_prop = properties.get("사용자 ID") or properties.get("User ID")
    user_id = extract_property_value(user_id_prop, "rich_text")

    # user_id가 없으면 database_id로부터 역조회 시도
    if not user_id and database_id:
        user_id = settings.get_user_id_by_database(database_id)
        if user_id:
            logger.info(f"📍 Database ID로부터 User ID 역조회 성공: {user_id}")
        else:
            # 등록되지 않은 Database ID
            logger.warning(f"⚠️ 등록되지 않은 Database ID: {database_id}")
            raise ValueError(
                f"등록되지 않은 Notion Database입니다. "
                f"Database ID: {database_id}\n"
                f"관리자에게 문의하여 USER_DATABASE_MAPPING에 등록해주세요."
            )

    return WorkLogFeedbackRequest(
        action="work_log_feedback",
        date=date,
        ai_provider=ai_provider,  # 모델 내부에서 validation 및 lower() 처리
        flavor=flavor,  # 모델 내부에서 validation 및 lower() 처리
        user_id=user_id,
        database_id=database_id  # 모델 내부에서 하이픈 제거 처리
    )


@router.post("/notion-to-slack")
async def handle_notion_webhook(
    request: Request,
    x_api_key: str = Header(None),
    taste: str = None
):
    """Notion 웹훅을 받아서 Slack으로 전달

    Notion database button webhook을 수신하여 업무일지 피드백 형식으로 변환한 후
    Slack incoming webhook으로 전달합니다.

    Args:
        request: FastAPI 요청 객체
        x_api_key: API 인증 키 (선택사항, Header)
        taste: 피드백 맛 (선택사항, Query Parameter: spicy, normal, mild)

    Returns:
        성공 메시지 및 변환된 요청 데이터

    Raises:
        HTTPException:
            - 401: API 키 인증 실패
            - 400: 페이로드 검증 실패
            - 502: Slack 전달 실패
            - 500: 예상치 못한 서버 오류
    """
    # API 키 검증 (설정된 경우에만)
    if settings.api_key and x_api_key != settings.api_key:
        logger.warning("⚠️ 잘못된 API 키로 접근 시도")
        raise HTTPException(status_code=401, detail="잘못된 API 키입니다")

    try:
        # Notion 페이로드 수신
        notion_payload = await request.json()

        logger.info("📥 Notion 웹훅 수신")
        logger.debug(f"페이로드: {json.dumps(notion_payload, indent=2, ensure_ascii=False)}")

        # 업무일지 피드백 요청으로 변환
        work_log_request = convert_notion_to_work_log_request(notion_payload, taste_override=taste)

        logger.info(f"✅ 업무일지 요청으로 변환 완료: {work_log_request.model_dump()}")

        # Slack webhook 페이로드 생성
        slack_payload = SlackWebhookPayload(
            text=work_log_request.model_dump_json()
        )

        # Slack webhook으로 전달
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.slack_webhook_url,
                json=slack_payload.model_dump(),
                timeout=10.0
            )
            response.raise_for_status()

        logger.info("🚀 Slack webhook 전달 성공")

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Slack으로 성공적으로 전달되었습니다",
                "work_log_request": work_log_request.model_dump()
            }
        )

    except ValueError as ve:
        logger.error(f"❌ 검증 오류: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except httpx.HTTPError as he:
        logger.error(f"❌ Slack 전달 실패: {he}")
        raise HTTPException(status_code=502, detail=f"Slack 전달 실패: {str(he)}")

    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@router.post("/test")
async def test_webhook(payload: Dict[str, Any]):
    """테스트 엔드포인트 - 수신한 페이로드를 그대로 반환

    Notion button에서 전송되는 실제 페이로드 구조를 확인하기 위한 엔드포인트입니다.
    Notion webhook URL을 이 엔드포인트로 설정한 후 버튼을 클릭하면
    로그에서 전체 페이로드를 확인할 수 있습니다.

    Args:
        payload: Notion에서 전송된 JSON 페이로드

    Returns:
        수신한 페이로드를 그대로 반환
    """
    logger.info("📥 테스트 웹훅 수신")
    logger.info(f"페이로드:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "테스트 웹훅을 성공적으로 수신했습니다",
            "received_payload": payload
        }
    )


@router.get("/health")
async def health_check():
    """헬스 체크 엔드포인트

    서버가 정상적으로 실행 중인지 확인합니다.

    Returns:
        서버 상태 정보
    """
    return {
        "status": "healthy",
        "service": "kim-secretary-api",
        "slack_configured": bool(settings.slack_webhook_url)
    }

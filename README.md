# Notion to Slack Webhook Adapter

FastAPI 기반 웹훅 변환 서버 - Notion webhook button 페이로드를 Slack incoming webhook 형식으로 변환합니다.

## 기능

- Notion database button webhook 수신
- 업무일지 피드백 요청 형식으로 변환
- Slack incoming webhook으로 전달
- 테스트 엔드포인트 제공

## 아키텍처

```
Notion Database Button
    ↓ (Webhook: Send webhook action)
FastAPI Adapter Server (이 프로젝트)
    ↓ (변환된 페이로드)
Slack Incoming Webhook
    ↓
Secretary Bot (업무일지 피드백 처리)
```

## 설치 및 실행

### 1. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일 편집:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
```

### 2. Docker로 실행 (권장)

```bash
# 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

### 3. 로컬에서 실행

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 실행
python main.py
```

서버는 `http://localhost:8000`에서 실행됩니다.

## API 엔드포인트

### 1. Notion to Slack 변환 (`POST /api/notion-to-slack`)

Notion webhook button에서 이 URL을 호출하도록 설정합니다.

**요청 예시** (Notion이 보내는 형식):
```json
{
  "properties": {
    "작성일": {
      "date": {
        "start": "2025-10-18"
      }
    },
    "AI 제공자": {
      "select": {
        "name": "claude"
      }
    },
    "맛": {
      "select": {
        "name": "spicy"
      }
    },
    "사용자 ID": {
      "rich_text": [
        {
          "plain_text": "U05258DMFEE"
        }
      ]
    }
  }
}
```

**응답:**
```json
{
  "status": "success",
  "message": "Webhook forwarded to Slack",
  "work_log_request": {
    "action": "work_log_feedback",
    "date": "2025-10-18",
    "ai_provider": "claude",
    "flavor": "spicy",
    "user_id": "U05258DMFEE"
  }
}
```

### 2. 테스트 엔드포인트 (`POST /api/test`)

Notion이 보내는 실제 페이로드를 확인하기 위한 엔드포인트입니다.

```bash
# Notion button에 이 URL 설정
http://your-server:8000/api/test

# 로그에서 페이로드 확인
docker-compose logs -f
```

### 3. Health Check (`GET /api/health`)

서버 상태 확인:
```bash
curl http://localhost:8000/api/health
```

## Notion Database 설정

### 1. Database 속성 추가

다음 속성들을 Notion database에 추가하세요:

| 속성명 | 타입 | 필수 | 기본값 |
|--------|------|------|--------|
| 작성일 | Date | ✅ | - |
| AI 제공자 | Select | ❌ | gemini |
| 맛 | Select | ❌ | normal |
| 사용자 ID | Text | ❌ | - |

**AI 제공자 옵션:**
- gemini
- claude
- codex
- ollama

**맛 옵션:**
- spicy (매운맛)
- normal (보통맛)
- mild (순한맛)

### 2. Database Button 설정

1. Notion database에서 "New" → "Button" 클릭
2. Button 이름 설정 (예: "AI 피드백 생성")
3. "Add action" → "Send webhook" 선택
4. Webhook URL 입력:
   ```
   http://your-server:8000/api/notion-to-slack
   ```
5. Properties 선택:
   - ✅ 작성일
   - ✅ AI 제공자
   - ✅ 맛
   - ✅ 사용자 ID

### 3. 테스트

1. Notion database row에서 button 클릭
2. 서버 로그 확인:
   ```bash
   docker-compose logs -f
   ```
3. Slack 채널에서 메시지 확인

## 보안

### API Key 인증 (선택사항)

API key를 설정하여 인증을 추가할 수 있습니다:

```bash
# .env
API_KEY=your-secret-api-key
```

Notion button에 custom header 추가:
- Key: `X-API-Key`
- Value: `your-secret-api-key`

## 트러블슈팅

### 1. Notion 페이로드 확인

```bash
# 테스트 엔드포인트 사용
# Notion button URL을 /api/test로 설정하고 클릭
docker-compose logs -f | grep "Test webhook"
```

### 2. Slack으로 전달 실패

```bash
# 로그 확인
docker-compose logs -f | grep "Failed to forward"

# SLACK_WEBHOOK_URL 확인
docker-compose exec webhook-adapter env | grep SLACK
```

### 3. 속성 이름이 다른 경우

`app/routers/webhook.py`의 `convert_notion_to_work_log_request()` 함수에서 속성 이름 매핑을 수정:

```python
# 예: 영어 속성 이름 사용 시
date_prop = properties.get("Date")  # "작성일" 대신
ai_provider_prop = properties.get("AI Provider")  # "AI 제공자" 대신
```

## 프로젝트 구조

```
notion-slack-adapter/
├── app/
│   ├── __init__.py
│   ├── config.py          # 설정 관리
│   ├── models.py          # Pydantic 모델
│   └── routers/
│       ├── __init__.py
│       └── webhook.py     # Webhook 엔드포인트
├── main.py                # FastAPI 앱 진입점
├── requirements.txt       # Python 의존성
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Docker 이미지 빌드 및 배포

### Docker Hub에 푸시하기

```bash
# 기본 (latest 태그)
./scripts/docker-build-push.sh

# 특정 버전 태그
./scripts/docker-build-push.sh v1.0.0

# 특정 태그 (버전이 아닌 경우)
./scripts/docker-build-push.sh production
```

스크립트는 자동으로:
1. Docker 이미지 빌드
2. 지정된 태그로 태깅
3. `latest` 태그도 함께 생성 (버전 태그 사용 시)
4. Docker Hub에 푸시

### 수동으로 빌드/푸시

```bash
# 빌드
docker build -t junho5336/kim-secretary-api:latest .

# 특정 태그로 빌드
docker build -t junho5336/kim-secretary-api:v1.0.0 .

# 푸시
docker push junho5336/kim-secretary-api:latest
docker push junho5336/kim-secretary-api:v1.0.0
```

## 개발

### 로컬 개발 서버 실행

```bash
# Auto-reload 활성화
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 로그 레벨 변경

```bash
# .env
LOG_LEVEL=debug  # debug, info, warning, error
```

## 라이선스

MIT

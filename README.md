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
USER_DATABASE_MAPPING={"USER_ID_1":"database-id-1"}
```

### 2. 로컬에서 실행

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

## 프로젝트 구조

```
kim-secretary-api/
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

### 크로스플랫폼 빌드 (Multi-Architecture)

다양한 플랫폼(AMD64, ARM64)을 지원하는 이미지를 빌드하려면 Docker Buildx를 사용합니다.

```bash
# 1. Buildx builder 생성 (최초 1회)
docker buildx create --name multiplatform-builder --use
docker buildx inspect --bootstrap

# 3. Production 태그로 빌드
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t junho5336/kim-secretary-api:prod \
  --push \
  .
```

**주의사항:**
- `--push` 플래그는 빌드 후 자동으로 레지스트리에 푸시합니다
- 로컬에 저장하려면 `--load` 사용 (단, 단일 플랫폼만 가능)
- ARM64는 Apple Silicon Mac, Raspberry Pi 등에서 사용됩니다

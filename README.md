# 🚀 Auto Vibe Coding Engine

> 키워드 또는 목적을 입력하면 웹 리서치 → 내용 정리 → 코드 자동 생성 → 실행 및 피드백까지 자동으로 처리하는 멀티 에이전트 시스템

---

## 📌 프로젝트 개요

Auto Vibe Coding Engine은 사용자의 키워드나 목적을 입력받아 리서치와 코드 생성을 자동으로 수행하는 파이프라인 기반 멀티 에이전트 시스템입니다.

- 최신 웹 정보를 기반으로 리서치하고 문서를 자동 정리
- 리서치 결과를 컨텍스트로 활용한 코드 자동 생성
- Docker 샌드박스에서 코드를 실행하고 오류 발생 시 Self-Correction
- 결과물을 이메일로 자동 발송 (요청 시에만)
- Streamlit 대시보드에서 실행 / 모니터링 / 로그 탭으로 진행 상황 확인

---

## 🏗️ 시스템 아키텍처

상세 아키텍처 다이어그램은 [`architecture.mermaid`](./architecture.mermaid) 파일을 참고하세요.

## 📎 문서

| 문서 | 설명 |
|---|---|
| [📋 CHANGELOG](./CHANGELOG.md) | 주요 설계 결정 및 변경 이력 |
| [🔧 ISSUES](./ISSUES.md) | 현재 진행 중인 이슈 및 해결 과제 |

---

### 파이프라인 흐름

```
사용자 입력 (키워드/목적)
    ↓
① Research Agent   — Tavily 웹 검색 + Gemini 2.5 Flash 정리
    ↓
② Code Agent       — Ollama(qwen2.5-coder) 코드 생성
                       → GPT-5.4-mini 코드 리뷰 + 의도 검증
                       → Docker 샌드박스 실행
                       → 실패 시 Gemini 2.5 Flash 에러 분석 → Ollama 재생성
   (코드 불필요 시 스킵)
    ↓
③ Output Agent     — Gemini 2.5 Flash 문서 정리 + 결과 출력
    ↓
④ Email Agent      — 요청 시에만 발송
```

---

## 🛠️ 기술 스택

| 분류 | 기술 | 용도 |
|---|---|---|
| **언어** | Python 3.11 | 전체 시스템 구현 |
| **워크플로우 제어** | LangGraph | 파이프라인 + Self-Correction 루프 |
| **웹 검색** | Tavily API | 실시간 웹 검색 |
| **Cloud LLM** | Gemini 2.5 Flash | 리서치 정리, 문서 작성, 에러 분석 |
| **Cloud LLM** | GPT-5.4-mini (학교 API) | 코드 리뷰, 사용자 의도 검증 |
| **Local LLM** | Ollama + qwen2.5-coder | 코드 생성, 코드 수정 |
| **GPU** | NVIDIA RTX 3080 | 로컬 추론 가속 |
| **샌드박스** | Docker | 보안 격리 코드 실행 환경 |
| **UI** | Streamlit | 실행 / 모니터링 / 로그 탭 대시보드 |
| **이메일** | Gmail SMTP | 결과물 자동 발송 (요청 시) |
| **실행 환경** | WSL2 + Docker | 개발 및 배포 환경 |
| **학교 API Gateway** | Mindlogic FactChat | GPT-5.4-mini 연동 (OpenAI 호환) |

---

## 🤖 에이전트 역할 구조

### Research Agent
- Tavily API로 최신 웹 문서, 기술 레퍼런스, 예제 코드 검색
- Gemini 2.5 Flash가 검색 결과를 정제하고 요약
- 이후 Code Agent가 참고할 수 있는 컨텍스트 형태로 전달

### Code Agent
- Research Agent의 결과를 컨텍스트로 받아 최신 문법 기반 코드 생성 (Ollama + qwen2.5-coder)
- GPT-5.4-mini가 실행 전 코드 리뷰 및 사용자 의도 부합 여부 검증
- Docker 샌드박스에서 코드 실행 및 테스트
- 오류 발생 시 Gemini 2.5 Flash가 에러 분석 → Ollama가 수정 코드 재생성
- 코드 생성이 불필요한 요청은 스킵

### Output Agent
- Gemini 2.5 Flash가 리서치 결과 및 코드 실행 결과를 문서로 정리
- Markdown 형식으로 출력

### Email Agent
- 사용자가 이메일 발송을 요청한 경우에만 실행
- Output Agent의 결과물을 첨부하여 발송
- 토큰/API 사용량 절약을 위해 요청 시에만 동작

---

## 🤝 AI 협업 구조

| AI | 모델 | 역할 | 비용 |
|---|---|---|---|
| **Gemini 2.5 Flash** | gemini-2.5-flash | 리서치 정리, 문서 작성, 에러 분석 | 무료 티어 |
| **GPT-5.4-mini** | gpt-5.4-mini | 코드 리뷰, 의도 검증 | 학교 API |
| **Ollama** | qwen2.5-coder | 코드 생성, 코드 수정 | 무료 (로컬) |

---

## 🔄 Self-Correction Loop

```
코드 생성 (Ollama + qwen2.5-coder)
    ↓
코드 리뷰 + 의도 검증 (GPT-5.4-mini)
    ↓
Docker 샌드박스 실행
    ↓ 성공
Output Agent → 완료
    ↓ 실패
에러 분석 (Gemini 2.5 Flash)
    ↓
수정 코드 재생성 (Ollama) → 최대 3회
    ↓ 3회 초과
사용자에게 실패 리포트 반환
```

---

## 🖥️ Streamlit 대시보드

| 탭 | 기능 |
|---|---|
| 🚀 실행 | 키워드/목적 입력, 파이프라인 단계별 진행 상황 실시간 표시 |
| 📊 모니터링 | 각 에이전트 단계별 입출력 내용 확인 |
| 📝 로그 | LLM 호출 내역, 토큰 사용량 확인 |

---

## 🐳 Docker 샌드박스 설정

| 항목 | 값 | 설명 |
|---|---|---|
| `timeout` | 60초 | 코드 실행 최대 시간 |
| `memory_limit` | 1GB | 컨테이너 최대 메모리 |
| `cpu_limit` | 2.0 | CPU 2코어 |
| `network` | none | 네트워크 완전 차단 |
| `max_retries` | 3 | Self-Correction 최대 재시도 횟수 |

---

## 📁 프로젝트 구조

```
auto-vibe-coding/
├── README.md
├── ISSUES.md
├── CHANGELOG.md
├── architecture.mermaid
├── docker-compose.yaml
├── Dockerfile
├── Dockerfile.sandbox
├── requirements.txt
├── .env
├── src/
│   ├── main.py
│   ├── agents/
│   │   ├── research_agent.py
│   │   ├── code_agent.py
│   │   ├── output_agent.py
│   │   └── email_agent.py
│   ├── workflows/
│   │   └── graph.py
│   ├── sandbox/
│   │   ├── executor.py
│   │   └── error_parser.py
│   ├── utils/
│   │   └── logger.py
│   └── ui/
│       └── dashboard.py
├── config/
│   ├── agents.yaml
│   ├── models.yaml
│   └── sandbox.yaml
└── tests/
```

---

## ⚙️ 환경 설정

### 사전 요구사항
- WSL2 (Ubuntu 24.04)
- Docker 28.x + NVIDIA Container Toolkit
- NVIDIA RTX 3080 12GB
- Python 3.11

### 환경 변수 설정

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

SCHOOL_API_KEY=your_school_api_key
SCHOOL_API_BASE_URL=https://factchat-cloud.mindlogic.ai/v1/gateway
SCHOOL_MODEL=gpt-5.4-mini

TAVILY_API_KEY=your_tavily_api_key

OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5-coder

EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=your_email@gmail.com
```

### 실행

```bash
docker build -f Dockerfile.sandbox -t auto-vibe-sandbox .
docker-compose up -d
docker exec -it auto-vibe-coding_ollama_1 ollama pull qwen2.5-coder
```

### 대시보드 접속

```
http://localhost:8501
```

---

## 📄 라이선스

MIT License

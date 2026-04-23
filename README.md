# 🚀 Auto Vibe Coding Engine

> 키워드 또는 목적을 입력하면 웹 리서치 → 내용 정리 → 코드 자동 생성 → 실행 및 피드백까지 자동으로 처리하는 멀티 에이전트 시스템

---

## 📌 프로젝트 개요

Auto Vibe Coding Engine은 사용자의 키워드나 목적을 입력받아, 리서치와 코드 생성을 자동으로 수행하는 파이프라인 기반 멀티 에이전트 시스템입니다.

- 최신 웹 정보를 기반으로 리서치하고 문서를 자동 정리
- 리서치 결과를 컨텍스트로 활용한 코드 자동 생성
- Docker 샌드박스에서 코드를 실행하고 오류 발생 시 Self-Correction
- 결과물을 이메일로 자동 발송 (요청 시)

---

## 🏗️ 시스템 아키텍처

상세 아키텍처 다이어그램은 [`architecture.mermaid`](./architecture.mermaid) 파일을 참고하세요.

### 파이프라인 흐름

```
사용자 입력 (키워드/목적)
    ↓
① Research Agent   — Tavily 웹 검색 + Gemini Flash 정리
    ↓
② Code Agent       — Ollama 코드 생성
                       → GPT-5.4 mini 코드 리뷰 + 의도 검증
                       → Docker 샌드박스 실행
                       → 실패 시 Gemini Flash 에러 분석 → Ollama 재생성
   (코드 불필요 시 스킵)
    ↓
③ Output Agent     — Gemini Flash 문서 정리 + 결과 출력
    ↓
④ Email Agent      — 요청 시에만 발송 (Gmail SMTP / SendGrid)
```

---

## 🛠️ 기술 스택

| 분류 | 기술 | 용도 |
|---|---|---|
| **언어** | Python 3.x | 전체 시스템 구현 |
| **워크플로우 제어** | LangGraph | 파이프라인 + Self-Correction 루프 |
| **웹 검색** | Tavily API | 실시간 웹 검색 |
| **Cloud LLM** | Gemini Flash | 리서치 정리, 문서 작성, 에러 분석 |
| **Cloud LLM** | GPT-5.4 mini | 코드 리뷰, 사용자 의도 검증 |
| **Local LLM** | Ollama | 코드 생성, 코드 수정 |
| **GPU** | NVIDIA RTX 3080 | 로컬 추론 가속 |
| **샌드박스** | Docker | 보안 격리 코드 실행 환경 |
| **UI** | Streamlit | 에이전트 워크플로우 모니터링 |
| **이메일** | Gmail SMTP / SendGrid | 결과물 자동 발송 |
| **실행 환경** | WSL2 + Docker | 개발 및 배포 환경 |

---

## 🤖 에이전트 역할 구조

### Research Agent
- Tavily API로 최신 웹 문서, 기술 레퍼런스, 예제 코드 검색
- Gemini Flash가 검색 결과를 정제하고 요약
- 이후 Code Agent가 참고할 수 있는 컨텍스트 형태로 전달

### Code Agent
- Research Agent의 결과를 컨텍스트로 받아 최신 문법 기반 코드 생성 (Ollama)
- GPT-5.4 mini가 실행 전 코드 리뷰 및 사용자 의도 부합 여부 검증
- Docker 샌드박스에서 코드 실행 및 테스트
- 오류 발생 시 Gemini Flash가 에러 분석 → Ollama가 수정 코드 재생성 (Self-Correction)
- 코드 생성이 불필요한 요청은 스킵

### Output Agent
- Gemini Flash가 리서치 결과 및 코드 실행 결과를 문서로 정리
- Markdown 또는 지정 형식으로 출력

### Email Agent
- 사용자가 이메일 발송을 요청한 경우에만 실행
- Output Agent의 결과물을 첨부하여 발송
- 불필요한 API 사용 방지를 위해 요청 시에만 동작

---

## 🔄 Self-Correction Loop

```
코드 생성 (Ollama)
    ↓
코드 리뷰 + 의도 검증 (GPT-5.4 mini)
    ↓
Docker 샌드박스 실행
    ↓ 성공
Output Agent → 완료
    ↓ 실패
에러 분석 (Gemini Flash)
    ↓
수정 코드 재생성 (Ollama) → 최대 3회
    ↓ 3회 초과
사용자에게 실패 리포트 반환
```

---

## 🤝 AI 협업 구조

| AI | 역할 | 비용 |
|---|---|---|
| **Gemini Flash** | 리서치 정리, 문서 작성, 에러 분석 | 무료 티어 |
| **GPT-5.4 mini** | 코드 리뷰, 사용자 의도 검증 | 학교 API (토큰 절약형) |
| **Ollama (로컬)** | 코드 생성, 코드 수정 | 무료 (RTX 3080) |

> GPT-5.4 mini는 코드와 사용자 의도 요약만 전달하여 토큰 사용량 최소화

---

## 📁 프로젝트 구조

```
auto-vibe-coding/
├── README.md
├── architecture.mermaid
├── docker-compose.yml
├── Dockerfile.sandbox
├── requirements.txt
├── .env                        # API 키 관리
├── src/
│   ├── main.py                 # 엔트리포인트
│   ├── agents/
│   │   ├── research_agent.py   # Research Agent (Tavily + Gemini Flash)
│   │   ├── code_agent.py       # Code Agent (Ollama + GPT-5.4 mini)
│   │   ├── output_agent.py     # Output Agent (Gemini Flash)
│   │   └── email_agent.py      # Email Agent (요청 시)
│   ├── workflows/
│   │   └── graph.py            # LangGraph 파이프라인 + Self-Correction
│   ├── sandbox/
│   │   ├── executor.py         # Docker 샌드박스 실행기
│   │   └── error_parser.py     # 에러 로그 정제
│   └── ui/
│       └── dashboard.py        # Streamlit 대시보드
├── config/
│   ├── agents.yaml             # 에이전트 프롬프트 설정
│   ├── models.yaml             # LLM 모델 설정
│   └── sandbox.yaml            # 샌드박스 리소스/타임아웃 설정
└── tests/
    └── ...
```

---

## ⚙️ 환경 설정

### 사전 요구사항
- WSL2 (Ubuntu 22.04 권장)
- Docker + NVIDIA Container Toolkit
- NVIDIA RTX 3080 (Ollama 로컬 추론용)
- Python 3.10+

### WSL2 GPU 설정
```bash
# GPU 확인
nvidia-smi

# NVIDIA Container Toolkit 설치
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list \
  | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo service docker restart
```

### 환경 변수 설정
```bash
cp .env.example .env
# .env 파일에 API 키 입력
```

```env
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_school_api_key
TAVILY_API_KEY=your_tavily_api_key
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### 실행
```bash
docker-compose up -d
python src/main.py
```

---

## 🔑 해결 과제

### 1. Self-Correction 루프 안정화
에러 메시지를 정제하여 Gemini Flash → Ollama로 효율적으로 전달하는 프롬프트 파이프라인 설계

### 2. 토큰 비용 최적화
GPT-5.4 mini에 전달하는 컨텍스트를 코드와 의도 요약으로만 제한하여 학교 API 토큰 절약

### 3. Docker 샌드박스 보안
AI가 생성한 코드의 파일시스템 접근, 네트워크 요청, 실행 시간을 제한하는 격리 환경 구성

### 4. Code Agent 스킵 판단
리서치만 필요한 요청과 코드 생성이 필요한 요청을 정확히 분류하는 로직 설계

---

## 📄 라이선스

MIT License

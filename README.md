# 🚀 Hybrid Vibe Coding Engine

> 사용자의 추상적인 의도(Vibe)만으로 실제 구동 가능한 소프트웨어를 자동 생성하는 자율형 하이브리드 개발 엔진

## 📌 프로젝트 개요

Hybrid Vibe Coding Engine은 클라우드 LLM과 로컬 LLM의 협업을 통해, 사용자의 고수준 요구사항만으로 완성된 소프트웨어를 자율적으로 생성하는 멀티 에이전트 시스템입니다.

### 핵심 기능

- **하이브리드 추론** — 클라우드 LLM(기획/설계)과 로컬 LLM(구현)이 역할을 분담하여 협업
- **자율 연구 에이전트** — 최신 기술 스택 및 라이브러리 사용법을 실시간으로 검색·학습
- **자율 피드백 루프** — 코드 실행 에러 발생 시 로그를 분석하고 스스로 수정하는 Self-Correction
- **의도 검증 (Intent Verification)** — 생성 결과물이 사용자의 최초 의도와 부합하는지 비판적으로 검토·최적화

## 🏗️ 시스템 아키텍처

```
사용자 (Vibe 입력)
        │
        ▼
┌─────────────────────────────────┐
│       Streamlit Dashboard       │
│    (워크플로우 모니터링 UI)       │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│      PM Agent (팀장 에이전트)     │
│  - 의도 해석 및 태스크 분해       │
│  - 최종 결과물 의도 검증          │
│  Cloud LLM: GPT-4o / Gemini    │
└───────┬─────────────┬───────────┘
        │             │
        ▼             ▼
┌──────────────┐ ┌──────────────────┐
│  Researcher  │ │    Developer     │
│    Agent     │ │     Agent        │
│ - 기술 리서치 │ │ - 코드 생성/수정  │
│ - 문서 검색  │ │ - 테스트 실행     │
│ Cloud LLM    │ │ Local LLM(Ollama)│
└──────┬───────┘ └────────┬─────────┘
       │                  │
       └────────┬─────────┘
                ▼
┌─────────────────────────────────┐
│   Docker Sandbox (코드 실행)     │
│   - 격리된 실행 환경             │
│   - 에러 로그 수집               │
└────────────────┬────────────────┘
                 │
                 ▼
        Self-Correction Loop
        (에러 시 재시도)
```

> 상세 아키텍처 다이어그램은 [`architecture.mermaid`](./architecture.mermaid) 파일을 참고하세요.

## 🛠️ 기술 스택

| 분류 | 기술 | 용도 |
|------|------|------|
| **언어** | Python 3.x | 전체 시스템 구현 |
| **에이전트 프레임워크** | CrewAI | 역할 기반 에이전트 협업 |
| **워크플로우 제어** | LangGraph | 순환 제어 구조 (피드백 루프) |
| **Cloud LLM** | OpenAI GPT-4o | 기획·설계·의도 검증 (학교 API Gateway) |
| **Cloud LLM** | Gemini 3 Flash | 리서치·보조 추론 (무료 티어) |
| **Local LLM** | Ollama | 코드 생성·구현 (Qwen2.5-Coder, Llama 3.3) |
| **GPU** | NVIDIA RTX 3080 | 로컬 추론 가속 |
| **샌드박스** | Docker | 보안 격리 코드 실행 환경 |
| **UI** | Streamlit | 에이전트 워크플로우 모니터링 대시보드 |

## 🤖 에이전트 역할 구조

### PM Agent (팀장)
- 사용자의 Vibe를 구체적인 태스크로 분해
- 하위 에이전트에게 작업 할당
- 최종 결과물이 사용자 의도에 부합하는지 교차 검증

### Researcher Agent (연구원)
- 최신 기술 문서, API 레퍼런스, 예제 코드 검색
- 검색 결과를 Developer Agent가 활용할 수 있는 형태로 정제

### Developer Agent (개발자)
- 로컬 LLM(Ollama)을 활용한 실제 코드 생성
- Docker 샌드박스 내 코드 실행 및 테스트
- 에러 발생 시 Self-Correction Loop 수행

## 🔄 Self-Correction Loop

```
코드 생성 → Docker 실행 → 성공? ──Yes──→ PM 의도 검증 → 완료
                            │
                           No
                            │
                            ▼
                   에러 로그 정제 → Developer Agent 재시도
                   (최대 N회 반복)
```

1. Developer Agent가 코드를 생성하여 Docker 샌드박스에서 실행
2. 에러 발생 시 로그를 정제하여 에이전트에게 재전달
3. 에이전트가 에러 원인을 분석하고 수정된 코드를 재생성
4. 성공 시 PM Agent가 사용자 의도 부합 여부를 최종 검증

## 🔑 해결 과제

### 1. 자율 피드백 루프 구현
코드 실행 에러 발생 시 에러 메시지를 정제하여 에이전트에게 재전달하는 프롬프트 파이프라인 설계가 필요합니다.

### 2. 토큰 및 컨텍스트 관리
대화가 길어질수록 증가하는 토큰 사용량을 억제하기 위한 데이터 압축(TOON 기법 등) 및 요약 알고리즘 적용이 필요합니다.

### 3. 보안 샌드박싱
AI가 생성한 코드가 로컬 시스템에 영향을 주지 않도록 Docker 기반 격리 실행 환경을 안전하게 구축해야 합니다.

### 4. 교차 검증 로직
에러가 없더라도 사용자 의도에 부합하는지 판단하는 PM Agent의 검증 페르소나를 고도화해야 합니다.

## 📁 프로젝트 구조

```
hybrid-vibe-engine/
├── README.md
├── architecture.mermaid
├── docker-compose.yml
├── Dockerfile.sandbox
├── requirements.txt
├── src/
│   ├── main.py                 # 엔트리포인트
│   ├── agents/
│   │   ├── pm_agent.py         # PM Agent (팀장)
│   │   ├── researcher_agent.py # Researcher Agent
│   │   └── developer_agent.py  # Developer Agent
│   ├── workflows/
│   │   ├── crew_config.py      # CrewAI 설정
│   │   └── graph.py            # LangGraph 워크플로우
│   ├── sandbox/
│   │   ├── executor.py         # Docker 샌드박스 실행기
│   │   └── error_parser.py     # 에러 로그 정제
│   ├── context/
│   │   └── compressor.py       # 토큰/컨텍스트 압축
│   └── ui/
│       └── dashboard.py        # Streamlit 대시보드
├── config/
│   ├── agents.yaml             # 에이전트 페르소나 설정
│   └── models.yaml             # LLM 모델 설정
└── tests/
    └── ...
```

## 📄 라이선스

MIT License

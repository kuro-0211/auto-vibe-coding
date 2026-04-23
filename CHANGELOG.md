# 📋 CHANGELOG

프로젝트 주요 설계 결정 및 변경 이력입니다.

---

## [현재] 파이프라인 아키텍처 확정

### 아키텍처 — CrewAI 제거, LangGraph 단일화

**배경:**
초기 설계에서는 CrewAI + LangGraph를 함께 사용하는 구조를 검토했으나 두 프레임워크가 LLM 호출과 상태를 각자 관리하여 충돌 및 중복 문제가 발생할 수 있음을 확인.

**검토 내용:**

| 항목 | CrewAI | LangGraph |
|---|---|---|
| 특징 | 역할 기반 에이전트 협업 | 상태 기반 그래프 워크플로우 |
| 강점 | Agent 페르소나, 태스크 위임 | 루프/분기/상태 제어 |
| 적합성 | 자율 협업 에이전트 | 순환 파이프라인 제어 |

**결정:** LangGraph 단일 사용
- Self-Correction 루프(코드 생성 → 실행 → 실패 → 재생성)는 순환 그래프 구조이므로 LangGraph가 더 적합
- 에이전트 역할 분담은 직접 클래스로 구현하여 CrewAI 의존성 제거
- 복잡도 감소 및 의존성 단순화

---

### 아키텍처 — PM Agent 제거, 파이프라인 구조로 전환

**배경:**
초기 설계의 PM Agent → Researcher → Developer 구조는 실제 목표(리서치 + 코드 생성)에 비해 과도하게 복잡함.

**결정:** 순서가 고정된 파이프라인 구조 채택
```
Research Agent → Code Agent → Output Agent → Email Agent
```
PM Agent 역할은 LangGraph의 분기 조건으로 대체.

---

### AI 구성 — GPT-4o 제거, 3개 AI 역할 분담 확정

**배경:**
초기 설계에서 GPT-4o(기획/설계), Gemini(리서치), Ollama(구현) 3개를 사용하려 했으나 PM Agent 제거로 GPT-4o 역할이 사라짐.

**검토 과정:**
1. Gemini Flash를 리서치 + 코드 리뷰 + 에러 분석 전담으로 검토
2. 학교 API(Mindlogic FactChat)가 GPT-5.4-mini를 지원함을 확인
3. 코드 리뷰/의도 검증은 GPT-5.4-mini가 더 적합하다고 판단

**결정:**

| AI | 역할 |
|---|---|
| Gemini 2.5 Flash | 리서치 정리, 문서 작성, 에러 분석 |
| GPT-5.4-mini (학교 API) | 코드 리뷰, 의도 검증 |
| Ollama + qwen2.5-coder | 코드 생성, 코드 수정 |

---

### AI 구성 — Gemini API 직접 호출 방식 채택

**배경:**
Gemini를 학교 API Gateway 경유로 호출하면 학교 API 토큰을 소모하므로 직접 Gemini API 키를 사용하는 방향으로 결정.

**문제 발생:**
- `google-generativeai` 패키지 deprecated → `google-genai`로 교체
- `gemini-2.0-flash` 사용 중단 → `gemini-2.5-flash`로 변경
- 무료 티어 일일 20회 한도 확인

**현재 상태:** Gemini 일일 한도 이슈로 학교 API Gateway 대체 재검토 중 (ISSUE-001 참고)

---

### 학교 API — Legacy 엔드포인트에서 Gateway로 변경

**배경:**
초기에 Legacy 엔드포인트(`/v1/api/openai`) 사용을 검토했으나 지원 모델이 `gpt-5-mini`까지만 확인됨.

**결정:** API Gateway(`/v1/gateway`) 사용
- 단일 엔드포인트로 OpenAI, Anthropic, Gemini 등 모든 모델 접근 가능
- `gpt-5.4-mini` 지원 확인
- OpenAI SDK와 100% 호환 (`base_url`만 변경)

```python
client = OpenAI(
    api_key=SCHOOL_API_KEY,
    base_url="https://factchat-cloud.mindlogic.ai/v1/gateway"
)
```

---

### 로컬 모델 — qwen2.5-coder 채택

**배경:**
코드 생성 전용 로컬 모델 선택 과정에서 여러 모델 검토.

**검토 내용:**

| 모델 | 개발사 | 코딩 성능 | 크기 |
|---|---|---|---|
| codellama | Meta (미국) | ⭐⭐⭐ | 4.7GB |
| llama3.1:8b | Meta (미국) | ⭐⭐⭐⭐ | 4.9GB |
| qwen2.5-coder | Alibaba (중국) | ⭐⭐⭐⭐⭐ | 4.7GB |

**결정:** `qwen2.5-coder` 채택
- 코딩 특화 모델 중 최상위 성능
- 로컬 실행이므로 외부 데이터 전송 없음
- RTX 3080 12GB VRAM 내 여유있게 실행 가능

---

### 샌드박스 — 보안 격리 설정 확정

**결정 사항:**
- `timeout`: 30초 → **60초**로 증가 (복잡한 코드 실행 고려)
- `memory_limit`: 512MB → **1GB**로 증가
- `cpu_limit`: 1.0 → **2.0**으로 증가
- `network`: none 유지 (보안 격리)

---

### UI — Streamlit 단일 페이지에서 3탭 구조로 변경

**배경:**
실행 결과만 보여주는 단일 페이지에서 진행 과정을 실시간으로 확인할 수 있는 구조 필요.

**결정:** 3탭 구조 채택
- 🚀 실행 탭: 입력 + 단계별 실시간 진행 표시
- 📊 모니터링 탭: 각 에이전트 단계별 입출력 내용
- 📝 로그 탭: LLM 호출 내역 + 토큰 사용량

**추가:** `src/utils/logger.py` 생성하여 파이프라인 전체 로그 수집

---

### 이메일 — 자동 발송에서 요청 시 발송으로 변경

**배경:**
항상 이메일을 자동 발송하면 API 사용량 낭비 및 불필요한 발송 발생.

**결정:** 사용자가 명시적으로 요청할 때만 Email Agent 실행
- 토큰/API 사용량 절약
- 사용자가 원하지 않는 이메일 발송 방지

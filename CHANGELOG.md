# 📋 CHANGELOG

프로젝트 주요 설계 결정 및 변경 이력입니다.

---

## [v1.2] 프런트엔드 Reflex 전환 + 실시간성 강화

### UI — Streamlit → Reflex 이관

**배경:**
Streamlit은 단일 페이지 rerun 모델이라 LangGraph 스트림과 결합 시 매 노드 완료마다 전체 페이지가 재구성되어 상호작용성/체감 성능이 낮았음. HITL 편집 도중 다른 위젯 클릭으로 입력이 초기화되는 부작용도 잦았음.

**결정:** Reflex(React + FastAPI) 기반 SPA 대시보드로 이관 (`aria_app/`)
- 백그라운드 이벤트(`@rx.event(background=True)`) 안에서 LangGraph `stream()` 결과를 `asyncio.to_thread + queue`로 받아 State에 점진 반영 → 새로고침 없이 노드별 결과 실시간 갱신
- Reflex 0.9 호환: `rx.Base` 폐기 대응을 위해 import fallback 체인 추가, `rx.foreach` 중첩 제약을 피해 사이드바 히스토리를 평탄화(`HistoryFlatEntry`)
- 컨테이너 진입점을 `reflex run`으로 교체, 마운트 볼륨 환경에서 worker churn 방지를 위해 `REFLEX_HOT_RELOAD=0`/`REFLEX_USE_GRANIAN=0`
- 포트: `3000` (프런트) / `8000` (백엔드)
- Legacy Streamlit 대시보드(`src/ui/dashboard.py`)는 참고용으로 보존

---

### Log Page — `pipeline_logger` 변화를 Reflex가 감지하지 못하는 버그 수정

**증상:**
실행을 한 번 마친 뒤 "로그" 탭을 열어도 LLM 호출 내역과 토큰 카운터가 비어 있거나 갱신되지 않음.

**원인:**
`AriaState.llm_logs` / `llm_log_total` / `llm_log_local` / `token_count`가 모두 `@rx.var`인데 내부에서 State 밖의 글로벌 `utils.logger.pipeline_logger`를 직접 읽고 있었음. Reflex는 자기 State 속성이 바뀔 때만 var 재계산/재전송을 트리거하므로 글로벌 객체의 mutation을 감지할 수 없었음.

**결정:**
- `llm_logs_data: list[dict]`, `token_usage_data: dict[str,int]`를 State 속성으로 추가
- `_sync_pipeline_logger()` 헬퍼로 phase1/phase2 스트림 루프의 각 노드 완료 직후와 종료 시점에 `pipeline_logger` → State 미러링
- 4개 `@rx.var`는 글로벌 대신 State 속성을 읽도록 변경 → 로그 페이지/사이드바 토큰 카운터가 실행 중에도 실시간 갱신

---

### Code Agent — 한국어 주석 `# [설명] ` 마커 도입

**배경:**
qwen2.5-coder가 생성한 코드의 한국어 주석이 코드 라인과 시각적으로 잘 구분되지 않아 HITL 편집창에서 어느 줄이 주석인지 한눈에 파악하기 어려웠음. 리뷰/에러수정 단계에서 마커가 임의로 벗겨지는 문제도 있었음.

**결정:**
- 생성 프롬프트: 한국어 주석은 모두 `# [설명] ` 접두어로 시작 강제, 영어 주석에는 미적용
- 리뷰 / 에러수정 프롬프트: 기존 `# [설명] ` 마커 보존 + 새로 추가하는 한국어 주석에도 동일 규칙 적용
- 효과: HITL 편집창에서 시각적 식별 용이 + `Ctrl+F`로 `[설명]` 검색 시 모든 주석 일괄 점프 가능

---

### Sandbox executor — CWD 의존 제거

**배경:**
`config/sandbox.yaml`을 CWD 기준 상대 경로로 열고 있어 Streamlit/Reflex/CLI 등 런처가 달라지면 파일을 찾지 못해 실행 실패.

**결정:**
- `executor.py`가 자기 파일 위치(`__file__`) 기준으로 프로젝트 루트를 계산해 `<root>/config/sandbox.yaml` 절대 경로로 해석
- CWD 상대 경로는 폴백으로만 유지

---

## [v1.1] 기능 완성도 향상

### Code Agent 스킵 판단 — 키워드 기반 → LLM 기반

**배경:**
키워드 기반 판단 방식은 문장의 의도를 정확히 파악하지 못해 오판이 빈번했음.

```
기존: "파이썬 함수란?" → needs_code: True ❌ (키워드 "함수" 감지)
개선: GPT-5.4-mini가 의도 파악 → needs_code: False ✅
```

**결정:**
- GPT-5.4-mini가 요청 의도를 분석하여 코드 생성 필요 여부 판단
- API 오류 시 키워드 방식으로 폴백하여 안정성 확보

---

### Research Agent — 리서치 품질 향상

**배경:**
검색 결과를 단순 텍스트로 잘라서 전달하던 방식에서 구조화된 형식으로 개선.

**변경 내용:**
- 신뢰 도메인 우선 검색 (`docs.python.org`, `github.com`, `stackoverflow.com` 등)
- 출처 URL 포함한 참고 출처 섹션 추가
- 구조화된 출력 형식 적용
  ```
  ## 핵심 요약
  ## 주요 내용
  ## 참고 출처
  ```

---

### Self-Correction — 에러 분석 대시보드 표시

**배경:**
에러 발생 시 로그에만 분석 내용이 출력되고 대시보드에 표시되지 않아 사용자가 원인을 알 수 없었음.

**변경 내용:**
- `AgentState`에 `error_analysis` 필드 추가
- `run_error_analysis()` 반환값을 `(code, analysis)` 튜플로 변경
- Gemma의 에러 분석 결과를 대시보드에 실시간 표시
- 최종 결과 화면에서 에러 분석 내용 강조 표시

---

### 실행 결과 포맷팅 개선

**변경 내용:**
- `executor.py`에 실행 시간(`elapsed`), 출력 줄 수(`lines`) 메타정보 추가
- 대시보드 결과 표시 구조 개선
  - 실행 성공: 실행 결과 → 코드 (접힘) → 문서 → 리서치 (접힘)
  - 실행 실패: 에러 분석 → 최종 코드 → 리서치 (접힘)
  - 리서치만: 결과 문서 → 리서치 (접힘)
- HTML 이스케이프 처리로 태그 노출 버그 수정

---

## [v1.0] 기초 틀 구성

### 아키텍처 — CrewAI 제거, LangGraph 단일화

**배경:**
초기 설계에서 CrewAI + LangGraph 동시 사용을 검토했으나 두 프레임워크가 상태를 각자 관리하여 충돌 및 중복 문제 발생 가능성 확인.

**결정:** LangGraph 단일 사용
- Self-Correction 루프는 순환 그래프 구조이므로 LangGraph가 더 적합
- 에이전트 역할 분담은 직접 클래스로 구현
- 복잡도 감소 및 의존성 단순화

---

### 아키텍처 — PM Agent 제거, 파이프라인 구조로 전환

**배경:**
초기 설계의 PM Agent → Researcher → Developer 구조는 실제 목표에 비해 과도하게 복잡.

**결정:** 순서가 고정된 파이프라인 구조 채택
```
Research Agent → Code Agent → Output Agent → Email Agent
```

---

### AI 구성 — 3개 AI 역할 분담 확정

**검토 과정:**
1. 초기: GPT-4o + Gemini Flash + Ollama 3개 검토
2. Gemini API 일일 한도 문제 (하루 20회) 발생
3. 학교 API(Mindlogic FactChat)가 GPT-5.4-mini 지원 확인
4. Gemini 완전 제거 → 학교 API + 로컬 모델로 대체

**최종 결정:**

| AI | 역할 |
|---|---|
| GPT-5.4-mini (학교 API) | 리서치 정리, 코드 생성 판단 |
| qwen2.5-coder (Ollama) | 코드 생성, 코드 리뷰, 수정 |
| gemma3:4b (Ollama) | 문서 작성, 에러 분석 |

---

### 학교 API — Legacy 엔드포인트에서 Gateway로 변경

**결정:** API Gateway(`/v1/gateway`) 사용
- 단일 엔드포인트로 모든 모델 접근 가능
- `gpt-5.4-mini` 지원 확인
- OpenAI SDK와 100% 호환

---

### 로컬 모델 — 역할 분리

**결정:**
- `qwen2.5-coder` (4.7GB): 코드 생성/리뷰 전담 (코딩 특화 모델)
- `gemma3:4b` (3.3GB): 문서 작성/에러 분석 전담 (언어 능력 우수)
- RTX 3080 12GB에서 합계 8GB로 안정적 동작

---

### Human-in-the-Loop 구현

**배경:**
AI가 생성한 코드를 검토 없이 바로 실행하는 것은 위험할 수 있음.

**결정:** 2단계 파이프라인으로 분리
- Phase 1: 리서치 → 코드 생성 → 코드 리뷰 (사용자 확인 후 중단)
- Phase 2: 사용자 승인 후 → Docker 실행 → 결과 출력
- 승인/거절 버튼으로 실행 여부 결정

---

### Checkpointer 추가

**결정:** LangGraph SqliteSaver 사용
- 세션별 상태를 SQLite DB에 저장
- 실행 중단 후 재개 가능한 구조 확보
- 추후 멀티스텝 프로젝트 관리 기능 확장 기반

---

### 샌드박스 — 보안 격리 설정 확정

| 항목 | 초기값 | 최종값 | 변경 이유 |
|---|---|---|---|
| `timeout` | 30초 | 60초 | 복잡한 코드 실행 고려 |
| `memory_limit` | 512MB | 1GB | 여유 확보 |
| `cpu_limit` | 1.0 | 2.0 | 성능 향상 |
| `network` | none | none | 보안 유지 |

---

### Docker 샌드박스 실행 방식 변경

**배경:**
파일 마운트 방식으로는 컨테이너 간 경로 공유가 안 되어 실행 실패.

**변경:**
- 파일 마운트 방식 → `command=["python", "-c", clean_code]` stdin 방식으로 변경
- 코드 전처리 함수 `clean_code()` 추가 (백틱 제거)

---

### 이메일 — Gmail → 네이버 SMTP 전환

**배경:**
Gmail 앱 비밀번호 방식이 지속적으로 인증 실패 발생.

**결정:** 네이버 SMTP 사용
- `smtp.naver.com:465` SSL 방식
- 네이버 앱 비밀번호 12자리 사용
- 정상 동작 확인

---

### UI — Streamlit 단일 페이지 → 사이드바 기반 대시보드

**배경:**
탭 방식 UI에서 사이드바 메뉴 방식으로 전환하여 더 직관적인 대시보드 구성.

**결정:** 사이드바 + 2열 레이아웃
- 좌측: 입력 + 파이프라인 단계
- 우측: 실시간 결과 카드
- 사이드바: 페이지 네비게이션 + 메트릭 (토큰, 시간, 세션)

**디자인:**
- Pretendard 폰트 적용
- Apple 디자인 시스템 참고 색상 체계
- `st.html()` 방식으로 CSS 주입 (텍스트 출력 오류 해결)

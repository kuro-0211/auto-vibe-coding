# 📋 CHANGELOG

프로젝트 주요 설계 결정 및 변경 이력입니다.

---

## [v1.3.1] Output Agent LLM 제거 — 템플릿 조립으로 전환

### 배경
`Output Agent`는 마지막 단계에서 gemma3:4b로 "최종 결과 문서"를 한 번 더 다듬고 있었음. 하지만:
- `research_agent`가 이미 GPT-5.4-mini로 환각 억제 + 출처 강제 규칙 아래 `## 핵심 요약 / ## 주요 내용 / ## 참고 출처` 구조로 정리한 결과를, 더 작은 gemma3:4b가 다시 풀어쓰는 구조 — 사실 변형 / 출처 누락 위험만 늘어남
- 코드 케이스에선 코드·실행 결과가 이미 별도 필드로 노출되는데, gemma가 자연어로 "이 코드는 …를 합니다"를 다시 만들어 UI에 중복 표시
- gemma3:4b 호출이 보통 가장 느린 마지막 노드라 체감 완료 시간을 압박

### 결정 — `run_output()`을 순수 템플릿 조립으로 전환 (LLM 호출 0회)
- **리서치 전용 케이스**: `research_result`를 그대로 반환 (GPT가 만든 구조를 그대로 살림)
- **코드 케이스**: `# 실행 결과` 섹션(✅/❌ 뱃지 + 시간/줄수 메타 + output/error 코드블록) + 실패 시 `## 에러 분석` + `# 참고 리서치` 섹션으로 마크다운 조립. 코드 본문은 `code_result` 별도 필드로 PDF/UI에서 이미 표시되므로 `final_output`에는 미포함

### UI 정리
- run 페이지 최종 화면에서 "🔍 리서치 결과" 별도 아코디언 제거 — 리서치는 `final_output` 안의 `# 참고 리서치` 섹션으로 이미 노출되므로 중복

### 효과
- 마지막 노드의 gemma3:4b 호출 1회(보통 2~5초) 제거 → 완료 체감 속도 향상
- 출처 인용/숫자/이름 변형 위험 제거
- 두 가지 폴리시 레벨(GPT 정리 위에 gemma 재정리)이 섞여 일관성이 깨지던 문제 해소

---

## [v1.3] SQLite 기반 멀티스텝 프로젝트 관리

### 배경
단일 실행 단위(`history.db`의 row 하나)만으로는 "FastAPI 기본 서버 → JWT 인증 추가 → DB 연결" 같은 누적 작업을 이어가기 어려웠음. LangGraph `SqliteSaver`는 thread 단위 체크포인트라 같은 흐름 안에서의 재개에는 좋지만, 의도적으로 새 세션을 만들면서 이전 결과를 컨텍스트로 가져오는 멀티스텝 워크플로우에는 맞지 않았음.

### 결정 — 프로젝트/세션 2단 모델
`data/projects.db`에 별도 SQLite 추가 (기존 `history.db` / `checkpoints.db`와 분리)

| 테이블 | 키 | 의미 |
|---|---|---|
| `projects` | id, name, description, status(`active`/`completed`/`paused`), created_at, updated_at | 멀티스텝 작업 묶음 단위 |
| `sessions` | id, project_id, session_number, user_input, research_result, code_result, execution_result(JSON), error_analysis, final_output, success, created_at | 프로젝트 내 N번째 실행의 전체 결과 |

- `session_number`는 프로젝트별 시퀀스(`MAX(session_number)+1`)로 부여 → "3단계 / 마지막: FastAPI 기본 서버 구현" 같은 UI 표현이 자연스럽게 나옴
- `ON DELETE CASCADE`로 프로젝트 삭제 시 세션 일괄 정리

### 파이프라인 컨텍스트 전파
- `AgentState`에 `project_id` / `previous_code` / `previous_context` / `session_number` 추가
- 프로젝트가 선택된 실행에서 `research_agent`는 `previous_context`를 "이전 세션 컨텍스트" 블록으로 프롬프트에 주입, `code_agent`는 `previous_code`를 "이전 세션 코드 — 위 코드를 기반으로 …" 형태로 받아 누적 개발 유도
- `output_node` 종료 직후 `project_id`가 있으면 `pm.save_session()` 호출 → 성공/실패 무관하게 세션이 영속화됨 (실패해도 다음 세션이 에러 분석을 컨텍스트로 받아 이어갈 수 있도록)

### Reflex UI
- 사이드바: `📂 프로젝트` 네비 추가 (실행 / 프로젝트 / 모니터링 / 로그 / 스케줄 순)
- `/project` — 새 프로젝트 생성 폼 + 목록 카드(상태 뱃지, 세션 수, 마지막 실행 시간, 이어서 작업/세션 보기/삭제)
- `/project/[pid]` — 프로젝트 요약 + 완료/중단 토글 + 세션 타임라인. 각 세션을 아코디언으로 펼치면 결과/리서치/코드/실행/에러 5탭으로 분류
- 실행 페이지 idle 상단에 선택 배너 추가: 프로젝트 선택 시 "이번이 N번째 세션 · 마지막: …", 미선택 시 "✨ 새 작업으로 실행 (프로젝트 없음)"
- Reflex 0.9의 `rx.foreach` 중첩 제약을 피하기 위해 프로젝트/세션 목록은 `ProjectView` / `SessionView` 타입드 뷰모델로 평탄화 (히스토리 사이드바의 `HistoryFlatEntry`와 동일 패턴)

### Legacy 정리
- v1.2에서 "참고용 보존" 처리했던 Streamlit `src/ui/dashboard.py`(1083 LOC) 완전 제거 — Reflex로 전면 이전 완료, 두 갈래 유지 필요 없어짐

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
- Legacy Streamlit 대시보드(`src/ui/dashboard.py`)는 참고용으로 일시 보존 → v1.3에서 삭제

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

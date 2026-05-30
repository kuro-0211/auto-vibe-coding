# 🔧 ISSUES

현재 진행 중인 이슈 및 해결 과제 목록입니다.

---

## 🔴 진행 중

### [ISSUE-001] 학교 API 토큰 한도
- **증상:** 요청이 많아지면 토큰 소진으로 API 호출 실패
- **원인:** 학교 API 토큰 한도가 적음
- **현재 전략:** GPT-5.4-mini는 리서치 정리 + 코드 생성 판단만 사용, 나머지는 로컬 모델로 처리
- **해결 방향:** 프롬프트 길이 최소화, 캐싱 도입 검토

---

### [ISSUE-002] Gemma 에러 분석 결과 간헐적 누락
- **증상:** 에러 분석 실행은 되나 분석 내용이 빈 문자열로 반환되는 경우 발생
- **원인:** Gemma 응답 지연 또는 프롬프트 처리 실패
- **현재 상태:** 프롬프트 단순화로 개선됨, 간헐적으로 재발 가능
- **해결 방향:** 응답 검증 로직 추가, 재시도 메커니즘 도입

---

### [ISSUE-003] 외부 네트워크 차단으로 인한 코드 실행 실패
- **증상:** 외부 API 호출 코드 실행 시 항상 실패
- **원인:** Docker 샌드박스 `network: none` 설정으로 네트워크 완전 차단
- **현재 상태:** 의도된 동작이나 사용자에게 명확한 안내 필요
- **해결 방향:** 네트워크 필요 여부를 코드 생성 전에 판단하여 사용자에게 안내

---

### [ISSUE-004] Gmail 앱 비밀번호 방식 인증 실패
- **증상:** Gmail SMTP 인증 실패 (`535 Username and Password not accepted`)
- **해결:** 네이버 SMTP로 전환하여 해결
- **현재 상태:** 네이버 SMTP로 정상 동작 중

---

## 🟡 검토 중

### [ISSUE-005] In-progress AriaState 영속화 (HITL 편집 손실 방지) 미구현
- **현황:** v1.3에서 *완료된* 세션은 `data/projects.db`에 영속화되어 프로젝트 선택 시 `previous_code` / `previous_context`로 다음 세션에 자동 전파됨. 그러나 진행 *중간*의 Reflex `AriaState`(`phase1_result`, `agent_logs`, `llm_logs_data`, `step_status`, HITL `edited_code` 등)는 여전히 인메모리라 새로고침/서버 재시작 시 소실
- **남은 위험 시나리오:** HITL 편집창에서 한참 코드를 수정하다 새로고침으로 입력이 통째로 날아감
- **필요 작업:**
  - `session_id`를 쿠키/localStorage로 보존
  - `on_load`에서 체크포인터 thread를 조회해 `phase1_result`/`phase`를 복구
  - `agent_logs` / `llm_logs_data`는 그래프 state 밖이라 sidecar 테이블(session_id 키)에 별도 저장·복구
  - phase 실행 도중 새로고침은 노드 중간 인터럽트라 LangGraph로도 살릴 수 없음 → 마지막 완료 노드부터 "재시작" 버튼 제공
- **우선순위:** 중간 (멀티스텝 영속화는 v1.3에서 해결, HITL 편집 손실은 별개 이슈로 잔존)

---

### [ISSUE-006] 파일 업로드/다운로드 미지원
- **현황:** 사용자가 CSV, JSON 등 파일을 업로드하여 분석 불가
- **필요 기능:** 파일 업로드 → 샌드박스에 마운트 → 코드에서 접근
- **우선순위:** 중간

---

## ✅ 해결 완료

### [RESOLVED-001] `langchain.schema` ImportError
- **해결:** `from langchain_core.messages import HumanMessage` 로 변경

### [RESOLVED-002] `google-generativeai` deprecated 경고
- **해결:** Gemini API 제거, 학교 API + 로컬 모델로 완전 대체

### [RESOLVED-003] 소스파일 첫 줄 `cat` 명령어 오염
- **해결:** `sed -i '/^EOF$/d'` 및 `sed -i '1{/^cat/d}'` 로 일괄 수정

### [RESOLVED-004] Docker 샌드박스 파일 경로 문제
- **해결:** 파일 마운트 방식 → `stdin` 방식으로 변경

### [RESOLVED-005] 코드에 백틱(` ``` `) 포함으로 실행 실패
- **해결:** `executor.py`에 `clean_code()` 함수 추가하여 전처리

### [RESOLVED-006] CSS `<style>` 태그 내용이 텍스트로 출력
- **해결:** `st.markdown` → `st.html()` 로 변경

### [RESOLVED-007] Self-Correction 3회 초과 시 4번째 실행 버그
- **해결:** `check_execution` 분기 조건 수정

### [RESOLVED-008] 에러 분석 내용에 HTML 태그 노출
- **해결:** `html.escape()` 처리로 HTML 이스케이프

### [RESOLVED-009] Gmail SMTP 인증 실패
- **해결:** 네이버 SMTP + 앱 비밀번호 방식으로 전환

### [RESOLVED-010] Gemini API 일일 한도 초과
- **해결:** Gemini API 완전 제거, 학교 API + 로컬 모델로 대체
  - 리서치 정리 → GPT-5.4-mini (학교 API)
  - 에러 분석, 문서 작성 → gemma3:4b (로컬)
  - 코드 생성, 리뷰 → qwen2.5-coder (로컬)

### [RESOLVED-011] 코드 생성 필요 여부 키워드 기반 판단 부정확
- **해결:** GPT-5.4-mini LLM 기반 의도 판단으로 전환 + 키워드 폴백 유지

### [RESOLVED-012] 리서치 결과 품질 낮음 (500자 제한, 출처 없음)
- **해결:** 신뢰 도메인 우선 검색, 출처 URL 포함, 구조화된 형식 (핵심 요약 / 주요 내용 / 참고 출처)

### [RESOLVED-013] 에러 분석 내용 대시보드 미표시
- **해결:** `AgentState`에 `error_analysis` 필드 추가, 튜플 반환으로 분석 결과 전달

### [RESOLVED-014] 실행 결과 포맷팅 부재
- **해결:** 실행 시간, 출력 줄 수 메타정보 추가, 결과 구조 개선 (성공/실패/리서치 분기)

### [RESOLVED-015] 스케줄링 미지원 (구 ISSUE-007)
- **해결:** APScheduler 백그라운드 + `data/schedule.db` 영속 저장으로 매시간/매일/매주/매월 자동 실행 지원. 대시보드 "⏰ 스케줄" 탭에서 등록·활성/비활성·삭제 및 다음 실행 시간 확인 가능 (Asia/Seoul)

### [RESOLVED-016] 로그 페이지가 실행 후에도 갱신되지 않음
- **증상:** Reflex 대시보드에서 한 번 실행 후 "📝 로그" 탭을 열어도 LLM 호출 내역/토큰 카운터가 빈 채로 남음
- **원인:** `AriaState`의 4개 `@rx.var`(`llm_logs`, `llm_log_total`, `llm_log_local`, `token_count`)가 State 밖 글로벌 `pipeline_logger`를 직접 참조 → Reflex가 mutation을 감지 못해 var 재계산/재전송 트리거 안 됨
- **해결:** `llm_logs_data` / `token_usage_data`를 State 속성으로 추가하고, phase1/phase2 스트림 루프의 각 노드 완료 직후 `_sync_pipeline_logger()`로 미러링. 4개 var는 State 속성을 읽도록 변경

### [RESOLVED-017] HITL 편집창에서 한국어 주석 식별 어려움
- **증상:** 생성된 코드의 한국어 주석이 코드 라인과 시각적으로 구분되지 않아 편집 시 어느 줄이 주석인지 한눈에 파악 어려움
- **해결:** 코드 생성/리뷰/에러수정 프롬프트에 한국어 주석은 모두 `# [설명] ` 접두어로 시작하도록 규칙 명시. 리뷰·재수정 단계에서도 마커 보존 강제 → 편집창에서 시각적 식별 + `Ctrl+F`로 `[설명]` 검색 시 일괄 점프

### [RESOLVED-018] 샌드박스 executor가 CWD에 따라 sandbox.yaml을 못 찾음
- **증상:** Streamlit/Reflex/CLI 등 런처가 달라지면 `config/sandbox.yaml` 로딩 실패
- **해결:** `executor.py`가 `__file__` 기준으로 프로젝트 루트를 계산해 절대 경로로 yaml 해석, CWD 상대 경로는 폴백으로만 유지

### [RESOLVED-019] 누적 코드 작업 시 이전 세션 컨텍스트가 사라짐
- **증상:** "FastAPI 서버 만들어줘" → "여기에 JWT 인증 추가해줘"를 두 번에 나눠 입력하면 두 번째 실행이 이전 코드를 모른 채 처음부터 새로 작성
- **원인:** 실행 단위가 stateless. `history.db`에는 결과가 쌓이지만 다음 실행 프롬프트에 자동 주입되는 경로가 없었음
- **해결:** v1.3에서 `data/projects.db`(projects/sessions) + `src/utils/project_manager.py` + `AgentState`(project_id/previous_code/previous_context/session_number) 추가. Reflex 사이드바 `📂 프로젝트` 탭에서 생성/선택하면 다음 실행이 이전 세션의 코드·리서치를 컨텍스트로 자동 포함

### [RESOLVED-020] Streamlit dashboard.py 잔존 (v1.2 Reflex 전환 후 legacy 보존)
- **증상:** Reflex 전환 후 `src/ui/dashboard.py`(1083 LOC)가 참고용으로 남아 있어 두 UI를 함께 유지해야 한다는 오해 유발
- **해결:** v1.3에서 완전 삭제. UI 소스는 Reflex `aria_app/` 하나만 권위 있는 단일 소스가 됨

### [RESOLVED-021] Output Agent의 LLM 재가공이 사실 변형/출처 누락 위험
- **증상:** `research_agent`(GPT-5.4-mini)가 환각 억제 + 출처 강제 규칙 아래 `## 핵심 요약 / ## 주요 내용 / ## 참고 출처`로 정리한 결과를, `output_agent`(gemma3:4b)가 마지막에 또 한 번 자연어로 풀어쓰는 구조였음. 두 가지 폴리시 레벨이 섞여 인용이 빠지거나 숫자가 미세하게 비틀리는 경우 발생. 코드 케이스에선 코드·실행 결과까지 풀어쓰면서 UI에 같은 내용이 중복 표시
- **해결:** v1.3.1에서 `run_output()`을 LLM 없는 순수 템플릿 조립으로 전환. 리서치 케이스는 `research_result` 그대로 반환, 코드 케이스는 `# 실행 결과` + 실패 시 `## 에러 분석` + `# 참고 리서치` 섹션 마크다운 조립. UI에서 중복되던 "🔍 리서치 결과" 아코디언도 제거. 부수 효과로 마지막 노드의 gemma3:4b 호출 1회 제거되어 완료 체감 속도 향상

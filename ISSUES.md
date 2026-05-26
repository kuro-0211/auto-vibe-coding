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

### [ISSUE-005] 멀티스텝 세션 영속화 (UI 레벨) 미구현
- **현황:** LangGraph `SqliteSaver`는 `data/checkpoints.db`에 노드 완료 단위로 체크포인트를 저장하고 있으나, Reflex `AriaState`(`session_id`, `phase`, `phase1_result`, `agent_logs`, `llm_logs_data`, `step_status` 등)는 인메모리라 새로고침/서버 재시작 시 전부 소실
- **위험 시나리오:** HITL 편집창에서 한참 코드를 수정하다 새로고침으로 입력이 통째로 날아감
- **필요 작업:**
  - `session_id`를 쿠키/localStorage로 보존
  - `on_load`에서 체크포인터 thread를 조회해 `phase1_result`/`phase`를 복구
  - `agent_logs` / `llm_logs_data`는 그래프 state 밖이라 sidecar 테이블(session_id 키)에 별도 저장·복구
  - phase 실행 도중 새로고침은 노드 중간 인터럽트라 LangGraph로도 살릴 수 없음 → 마지막 완료 노드부터 "재시작" 버튼 제공
- **우선순위:** 중간 (HITL 편집 손실 방지 효과)

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

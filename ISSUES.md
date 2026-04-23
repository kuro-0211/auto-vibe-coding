# 🔧 ISSUES

현재 진행 중인 이슈 및 해결 과제 목록입니다.

---

## 🔴 진행 중

### [ISSUE-001] Gemini 2.5 Flash 일일 한도 소진
- **증상:** `429 RESOURCE_EXHAUSTED` 에러 발생
- **원인:** 무료 티어 기준 하루 20회 요청 제한
- **영향:** Research Agent, Output Agent, 에러 분석 단계 전체 중단
- **임시 대응:** 한도 리셋(매일 자정) 후 재사용
- **해결 방향:** 학교 API Gateway를 통한 Gemini 호출로 대체 검토
  ```
  현재: Gemini API 키 → 직접 호출 (일 20회 제한)
  대안: 학교 API Gateway → gemini-3-flash-preview 호출
  ```

---

### [ISSUE-002] Self-Correction 3회 초과 시 4번째 실행 버그
- **증상:** 재시도 횟수가 3회를 초과해도 루프가 한 번 더 실행됨
- **원인:** `graph.py`의 `check_execution` 분기 조건 오류
- **현재 상태:** 수정 완료 (확인 필요)
- **수정 내용:**
  ```python
  def check_execution(state: AgentState) -> str:
      if state["execution_result"]["success"]:
          return "output"
      elif state["retry_count"] >= 3:  # 3회 초과 시 output으로
          return "output"
      else:
          return "error_analysis"
  ```

---

### [ISSUE-003] Gmail 이메일 발송 실패
- **증상:** `535 Username and Password not accepted` 에러
- **원인:** Gmail 앱 비밀번호 미설정
- **현재 상태:** 이메일 기능 임시 비활성화
- **해결 방법:**
  1. Google 계정 → 보안 → 2단계 인증 활성화
  2. 앱 비밀번호 발급 (메일 항목 선택)
  3. `.env`의 `EMAIL_PASSWORD`에 앱 비밀번호 입력

---

### [ISSUE-004] Streamlit UI 실행 후 결과 미반영
- **증상:** 실행 버튼 클릭 후 단계 표시가 업데이트되지 않음
- **원인:** Streamlit 세션 상태와 LangGraph 스트리밍 간 동기화 문제
- **현재 상태:** `graph.stream()` 방식으로 개선 적용
- **추가 확인 필요:** 모니터링/로그 탭 데이터 갱신 여부

---

### [ISSUE-005] Code Agent 스킵 판단 부정확
- **증상:** 코드 생성이 불필요한 요청에도 Code Agent가 실행되는 경우 있음
- **원인:** 현재 키워드 기반 단순 분류 방식 사용
  ```python
  keywords = ["코드", "만들어", "구현", "작성", "짜줘", "개발", "프로그램", "스크립트"]
  ```
- **해결 방향:** LLM 기반 의도 분류로 개선 필요

---

## 🟡 검토 중

### [ISSUE-006] 로컬 모델 VRAM 한계
- **현황:** RTX 3080 12GB 기준 동시 실행 가능 모델 제한
  ```
  qwen2.5-coder  4.7GB
  추가 모델       최대 약 7GB 여유
  ```
- **검토 사항:**
  - `qwen3.5:4b` (2.7GB) 추가 시 합계 7.4GB → 안정적
  - `qwen3.5:9b` (5.8GB) 추가 시 합계 10.5GB → 아슬아슬
  - `qwen3.6:35b-a3b` (24GB) → VRAM 초과, 현재 Ollama 미지원
- **결정 필요:** 로컬 2개 + 학교 API 1개 조합 확정

---

### [ISSUE-007] 토큰 사용량 최적화
- **현황:** GPT-5.4-mini 학교 API 토큰 한도가 적음
- **현재 전략:** 코드 리뷰 시 코드 + 의도 요약만 전달 (전체 리서치 내용 제외)
- **목표:** 요청당 학교 API 토큰 1,500 이하 유지

---

## ✅ 해결 완료

### [RESOLVED-001] `langchain.schema` ImportError
- **증상:** `ModuleNotFoundError: No module named 'langchain.schema'`
- **원인:** LangChain 최신 버전에서 경로 변경
- **해결:** `from langchain_core.messages import HumanMessage` 로 변경

### [RESOLVED-002] `google-generativeai` deprecated 경고
- **증상:** `FutureWarning: All support for the google.generativeai package has ended`
- **해결:** `google-genai` 패키지로 교체 및 코드 전면 수정

### [RESOLVED-003] 소스파일 첫 줄 `cat` 명령어 오염
- **증상:** `NameError: name 'cat' is not defined`
- **원인:** `cat > file << 'EOF'` 명령어가 파일 내용에 포함됨
- **해결:** `sed -i '/^EOF$/d'` 및 `sed -i '1{/^cat/d}'` 로 일괄 수정

### [RESOLVED-004] docker-compose `timeout` 파라미터 오류
- **증상:** `run() got an unexpected keyword argument 'timeout'`
- **해결:** Docker SDK에서 `timeout` 파라미터 제거

### [RESOLVED-005] `docker-compose up --build` ContainerConfig 오류
- **증상:** `KeyError: 'ContainerConfig'`
- **원인:** `docker-compose` 버전(1.29.2) 호환성 문제
- **해결:** `docker-compose down` 후 재실행으로 우회

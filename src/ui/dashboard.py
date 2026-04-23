import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from dotenv import load_dotenv
from workflows.graph import build_graph
from utils.logger import pipeline_logger

load_dotenv()

st.set_page_config(
    page_title="Auto Vibe Coding Engine",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Auto Vibe Coding Engine")
st.caption("키워드 또는 목적을 입력하면 리서치 → 코드 생성 → 실행까지 자동으로 처리합니다.")

# ── 탭 구성 ───────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🚀 실행", "📊 모니터링", "📝 로그"])

# ══════════════════════════════════════════════════════════
# 탭 1: 실행
# ══════════════════════════════════════════════════════════
with tab1:
    with st.form("input_form"):
        user_input = st.text_area(
            "🎯 키워드 또는 목적 입력",
            placeholder="예: FastAPI로 간단한 REST API 서버 만들어줘",
            height=100
        )
        send_email = st.checkbox("📧 결과를 이메일로 받기")
        submitted = st.form_submit_button("▶ 실행", use_container_width=True)

    if submitted and user_input.strip():
        pipeline_logger.reset()

        st.divider()

        # 진행 상태 표시
        steps = {
            "research":        "🔍 Research Agent — 웹 검색 및 정리",
            "code_decision":   "💡 코드 생성 필요 여부 판단",
            "code_generation": "🦙 Ollama — 코드 생성",
            "code_review":     "🤖 GPT-5.4-mini — 코드 리뷰 및 의도 검증",
            "execution":       "🐳 Docker 샌드박스 — 코드 실행",
            "error_analysis":  "⚠️ Gemini — 에러 분석 및 수정",
            "output":          "📄 Output Agent — 결과 정리",
            "email":           "📧 Email Agent — 이메일 발송",
        }

        step_placeholders = {}
        for key, label in steps.items():
            step_placeholders[key] = st.empty()
            step_placeholders[key].markdown(f"⬜ {label}")

        initial_state = {
            "user_input": user_input,
            "send_email": send_email,
            "research_result": None,
            "code_result": None,
            "execution_result": None,
            "final_output": None,
            "error": None,
            "retry_count": 0,
            "needs_code": None,
        }

        result = None
        error_occurred = False

        try:
            graph = build_graph()
            for stream_output in graph.stream(initial_state):
                for node_name, node_state in stream_output.items():
                    if node_name in step_placeholders:
                        label = steps[node_name]
                        if node_name == "error_analysis":
                            retry = node_state.get("retry_count", 0)
                            step_placeholders[node_name].markdown(
                                f"✅ {label} (재시도 {retry}/3)"
                            )
                        else:
                            step_placeholders[node_name].markdown(f"✅ {label}")
                    result = node_state

        except Exception as e:
            error_occurred = True
            st.error(f"오류: {str(e)}")

        if not error_occurred and result:
            st.divider()
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📋 최종 결과")
                if result.get("final_output"):
                    st.markdown(result["final_output"])

            with col2:
                if result.get("research_result"):
                    with st.expander("🔍 리서치 결과", expanded=False):
                        st.markdown(result["research_result"])

                if result.get("code_result"):
                    with st.expander("💻 생성된 코드", expanded=True):
                        st.code(result["code_result"], language="python")

                if result.get("execution_result"):
                    exec_result = result["execution_result"]
                    with st.expander("🐳 실행 결과", expanded=True):
                        if exec_result.get("success"):
                            st.success("실행 성공")
                            st.code(exec_result.get("output", ""), language="bash")
                        else:
                            retry = result.get("retry_count", 0)
                            st.error(f"실행 실패 ({retry}회 시도)")
                            st.code(exec_result.get("error", ""), language="bash")

            if send_email:
                st.info("📧 이메일 발송 완료")

    elif submitted and not user_input.strip():
        st.warning("입력값을 작성해주세요.")

# ══════════════════════════════════════════════════════════
# 탭 2: 모니터링
# ══════════════════════════════════════════════════════════
with tab2:
    st.subheader("📊 파이프라인 모니터링")

    if not pipeline_logger.steps:
        st.info("아직 실행된 파이프라인이 없습니다. 실행 탭에서 먼저 실행해주세요.")
    else:
        for step in pipeline_logger.steps:
            status_icon = "✅" if step["status"] == "done" else "❌" if step["status"] == "error" else "🔄"
            with st.expander(f"{status_icon} [{step['time']}] {step['step']}", expanded=False):
                if step.get("input"):
                    st.markdown("**📥 입력:**")
                    st.text(step["input"])
                if step.get("output"):
                    st.markdown("**📤 출력:**")
                    st.text(step["output"])

# ══════════════════════════════════════════════════════════
# 탭 3: 로그
# ══════════════════════════════════════════════════════════
with tab3:
    st.subheader("📝 LLM 호출 로그")

    if not pipeline_logger.logs:
        st.info("아직 실행된 로그가 없습니다.")
    else:
        # 토큰 사용량 요약
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "🤖 학교 API 토큰 사용량",
                f"{pipeline_logger.token_usage['school_api']:,} 토큰"
            )
        with col2:
            st.metric(
                "✨ Gemini 토큰 사용량",
                f"{pipeline_logger.token_usage['gemini']:,} 토큰"
            )

        st.divider()

        # 상세 로그
        for i, log in enumerate(pipeline_logger.logs):
            with st.expander(
                f"[{log['time']}] {log['model']} — {log['tokens']} 토큰",
                expanded=False
            ):
                st.markdown("**📤 프롬프트:**")
                st.text(log["prompt"])
                st.markdown("**📥 응답:**")
                st.text(log["response"])

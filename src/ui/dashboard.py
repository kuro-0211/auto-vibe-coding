import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import uuid
from dotenv import load_dotenv
from workflows.graph import build_phase1_graph, build_phase2_graph
from utils.logger import pipeline_logger

load_dotenv()

st.set_page_config(
    page_title="Auto Vibe Coding Engine",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Auto Vibe Coding Engine")
st.caption("키워드 또는 목적을 입력하면 리서치 → 코드 생성 → 실행까지 자동으로 처리합니다.")

# ── 세션 상태 초기화 ───────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "phase" not in st.session_state:
    st.session_state.phase = "idle"  # idle / phase1_done / phase2_done
if "phase1_result" not in st.session_state:
    st.session_state.phase1_result = None
if "result" not in st.session_state:
    st.session_state.result = None
if "send_email" not in st.session_state:
    st.session_state.send_email = False

tab1, tab2, tab3 = st.tabs(["🚀 실행", "📊 모니터링", "📝 로그"])

with tab1:
    # ── 입력 폼 ────────────────────────────────────────────
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
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.phase = "idle"
        st.session_state.phase1_result = None
        st.session_state.result = None
        st.session_state.send_email = send_email

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

        config = {"configurable": {"thread_id": st.session_state.session_id}}

        # ── Phase 1 실행 ────────────────────────────────────
        with st.spinner("⚙️ Phase 1 실행 중 (리서치 + 코드 생성 + 리뷰)..."):
            try:
                graph = build_phase1_graph()
                result = None
                for stream_output in graph.stream(initial_state, config=config):
                    for node_name, node_state in stream_output.items():
                        st.write(f"✅ {node_name} 완료")
                        result = node_state

                st.session_state.phase1_result = result
                st.session_state.phase = "phase1_done"

            except Exception as e:
                st.error(f"오류: {str(e)}")

        st.rerun()

    elif submitted and not user_input.strip():
        st.warning("입력값을 작성해주세요.")

    # ── Phase 1 완료 → 사용자 승인 ─────────────────────────
    if st.session_state.phase == "phase1_done" and st.session_state.phase1_result:
        result = st.session_state.phase1_result
        st.divider()

        # 코드가 생성된 경우 승인 요청
        if result.get("code_result"):
            st.warning("⏳ 코드 리뷰 완료 — 실행 전 승인이 필요합니다.")
            st.code(result["code_result"], language="python")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 승인 — 코드 실행", use_container_width=True, type="primary"):
                    config = {"configurable": {"thread_id": st.session_state.session_id}}

                    with st.spinner("⚙️ Phase 2 실행 중 (실행 + 결과 정리)..."):
                        try:
                            graph = build_phase2_graph()
                            final_result = None
                            for stream_output in graph.stream(result, config=config):
                                for node_name, node_state in stream_output.items():
                                    st.write(f"✅ {node_name} 완료")
                                    final_result = node_state

                            st.session_state.result = final_result
                            st.session_state.phase = "phase2_done"

                        except Exception as e:
                            st.error(f"오류: {str(e)}")

                    st.rerun()

            with col2:
                if st.button("❌ 거절 — 코드 재생성", use_container_width=True):
                    st.session_state.phase = "idle"
                    st.session_state.phase1_result = None
                    st.rerun()

        # 코드 불필요한 경우 바로 Output
        else:
            with st.spinner("📄 결과 정리 중..."):
                try:
                    graph = build_phase2_graph()
                    config = {"configurable": {"thread_id": st.session_state.session_id}}
                    final_result = None
                    for stream_output in graph.stream(result, config=config):
                        for node_name, node_state in stream_output.items():
                            final_result = node_state

                    st.session_state.result = final_result
                    st.session_state.phase = "phase2_done"

                except Exception as e:
                    st.error(f"오류: {str(e)}")

            st.rerun()

    # ── 최종 결과 출력 ─────────────────────────────────────
    if st.session_state.phase == "phase2_done" and st.session_state.result:
        result = st.session_state.result
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

# ══════════════════════════════════════════════════════════
# 탭 2: 모니터링
# ══════════════════════════════════════════════════════════
with tab2:
    st.subheader("📊 파이프라인 모니터링")
    st.caption(f"세션 ID: `{st.session_state.session_id}`")

    if not pipeline_logger.steps:
        st.info("아직 실행된 파이프라인이 없습니다.")
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
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "🤖 학교 API 토큰 사용량",
                f"{pipeline_logger.token_usage['school_api']:,} 토큰"
            )
        with col2:
            st.metric(
                "🦙 로컬 LLM 호출 수",
                f"{len([l for l in pipeline_logger.logs if 'gpt' not in l['model']])} 회"
            )

        st.divider()

        for log in pipeline_logger.logs:
            with st.expander(
                f"[{log['time']}] {log['model']} — {log['tokens']} 토큰",
                expanded=False
            ):
                st.markdown("**📤 프롬프트:**")
                st.text(log["prompt"])
                st.markdown("**📥 응답:**")
                st.text(log["response"])

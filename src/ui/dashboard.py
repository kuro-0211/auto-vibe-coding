import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import uuid
from dotenv import load_dotenv
from workflows.graph import build_phase1_graph, build_phase2_graph
from utils.logger import pipeline_logger

load_dotenv("/app/.env")

st.set_page_config(
    page_title="Auto Vibe Coding Engine",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Auto Vibe Coding Engine")
st.caption("키워드 또는 목적을 입력하면 리서치 → 코드 생성 → 실행까지 자동으로 처리합니다.")

# ── 세션 상태 초기화 ───────────────────────────────────────
defaults = {
    "session_id": str(uuid.uuid4()),
    "phase": "idle",
    "phase1_result": None,
    "result": None,
    "send_email": False,
    "agent_logs": [],
    "step_status": {},
    "live_content": "",
    "user_input": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def add_agent_log(agent: str, action: str, content: str = ""):
    st.session_state.agent_logs.append({
        "agent": agent,
        "action": action,
        "content": content[:300] if content else ""
    })

def update_step(key: str, status: str):
    st.session_state.step_status[key] = status

def get_step_icon(key: str) -> str:
    s = st.session_state.step_status.get(key, "idle")
    return "✅" if s == "done" else "🔄" if s == "running" else "⬜"

tab1, tab2, tab3 = st.tabs(["🚀 실행", "📊 모니터링", "📝 로그"])

# ══════════════════════════════════════════════════════════
# 탭 1: 실행
# ══════════════════════════════════════════════════════════
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
        st.session_state.phase = "running_phase1"
        st.session_state.phase1_result = None
        st.session_state.result = None
        st.session_state.send_email = send_email
        st.session_state.agent_logs = []
        st.session_state.step_status = {}
        st.session_state.live_content = ""
        st.session_state.user_input = user_input
        st.rerun()

    elif submitted and not user_input.strip():
        st.warning("입력값을 작성해주세요.")

    # ── Phase 1 실행 ────────────────────────────────────────
    if st.session_state.phase == "running_phase1":
        st.divider()
        st.subheader("⚙️ Phase 1 — 리서치 + 코드 생성")

        col_left, col_right = st.columns([1, 2])

        step_labels = {
            "research":        "🔍 Research Agent",
            "code_decision":   "💡 코드 필요 여부",
            "code_generation": "🦙 코드 생성",
            "code_review":     "🔍 코드 리뷰",
        }

        with col_left:
            st.markdown("**🔄 파이프라인 단계**")
            placeholders = {k: st.empty() for k in step_labels}
            for k, label in step_labels.items():
                placeholders[k].markdown(f"⬜ {label}")

        with col_right:
            st.markdown("**📡 에이전트 실시간 출력**")
            live_box = st.empty()

        initial_state = {
            "user_input": st.session_state.user_input,
            "send_email": st.session_state.send_email,
            "research_result": None,
            "code_result": None,
            "execution_result": None,
            "final_output": None,
            "error": None,
            "retry_count": 0,
            "needs_code": None,
        }

        config = {"configurable": {"thread_id": st.session_state.session_id}}

        try:
            graph = build_phase1_graph()

            for stream_output in graph.stream(initial_state, config=config):
                for node_name, node_state in stream_output.items():
                    update_step(node_name, "done")

                    if node_name in placeholders:
                        placeholders[node_name].markdown(f"✅ {step_labels[node_name]}")

                    if node_name == "research":
                        research = node_state.get("research_result", "")
                        add_agent_log("Research Agent", "웹 검색 완료", research)
                        live_box.markdown(f"**🔍 Research Agent 완료**\n\n{research[:500]}...")

                    elif node_name == "code_decision":
                        needs = node_state.get("needs_code", False)
                        add_agent_log("Code Decision", f"코드 생성 필요: {needs}")
                        live_box.markdown(f"**💡 코드 생성 필요: {'✅ 예' if needs else '❌ 아니오'}**")

                    elif node_name == "code_generation":
                        code = node_state.get("code_result", "")
                        add_agent_log("Code Generation", "코드 생성 완료", code)
                        live_box.markdown("**🦙 코드 생성 완료**")

                    elif node_name == "code_review":
                        reviewed = node_state.get("code_result", "")
                        add_agent_log("Code Review", "코드 리뷰 완료", reviewed)
                        live_box.markdown("**🔍 코드 리뷰 완료**")

                    st.session_state.phase1_result = node_state

            st.session_state.phase = "phase1_done"
            st.rerun()

        except Exception as e:
            st.error(f"오류: {str(e)}")
            st.session_state.phase = "idle"

    # ── Phase 1 완료 → 승인 UI ─────────────────────────────
    if st.session_state.phase == "phase1_done" and st.session_state.phase1_result:
        result = st.session_state.phase1_result
        st.divider()
        st.subheader("✅ Phase 1 완료")

        step_labels = {
            "research":        "🔍 Research Agent",
            "code_decision":   "💡 코드 필요 여부",
            "code_generation": "🦙 코드 생성",
            "code_review":     "🔍 코드 리뷰",
        }
        for k, label in step_labels.items():
            icon = get_step_icon(k)
            st.markdown(f"{icon} {label}")

        if result.get("code_result"):
            st.divider()
            st.warning("⏳ 코드 리뷰 완료 — 실행 전 승인이 필요합니다.")
            st.markdown("**🔍 리뷰된 코드:**")
            st.code(result["code_result"], language="python")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 승인 — 코드 실행", use_container_width=True, type="primary"):
                    st.session_state.phase = "running_phase2"
                    st.rerun()
            with col2:
                if st.button("❌ 거절 — 처음부터", use_container_width=True):
                    st.session_state.phase = "idle"
                    st.session_state.phase1_result = None
                    st.rerun()
        else:
            st.session_state.phase = "running_phase2"
            st.rerun()

    # ── Phase 2 실행 ────────────────────────────────────────
    if st.session_state.phase == "running_phase2" and st.session_state.phase1_result:
        result = st.session_state.phase1_result
        st.divider()
        st.subheader("⚙️ Phase 2 — 실행 + 결과 정리")

        col_left2, col_right2 = st.columns([1, 2])

        step_labels2 = {
            "execution":      "🐳 Docker 실행",
            "error_analysis": "⚠️ 에러 분석",
            "output":         "📄 결과 정리",
        }

        with col_left2:
            st.markdown("**🔄 실행 단계**")
            placeholders2 = {k: st.empty() for k in step_labels2}
            for k, label in step_labels2.items():
                placeholders2[k].markdown(f"⬜ {label}")

        with col_right2:
            st.markdown("**📡 실시간 출력**")
            live_box2 = st.empty()

        config = {"configurable": {"thread_id": st.session_state.session_id}}

        try:
            graph = build_phase2_graph()
            final_result = None

            for stream_output in graph.stream(result, config=config):
                for node_name, node_state in stream_output.items():
                    update_step(node_name, "done")

                    if node_name in placeholders2:
                        retry = node_state.get("retry_count", 0)
                        label = step_labels2.get(node_name, node_name)
                        suffix = f" ({retry}/3)" if node_name == "error_analysis" else ""
                        placeholders2[node_name].markdown(f"✅ {label}{suffix}")

                    if node_name == "execution":
                        exec_result = node_state.get("execution_result", {})
                        add_agent_log("Execution", "실행 완료", str(exec_result))
                        if exec_result.get("success"):
                            live_box2.success(f"✅ 실행 성공\n\n{exec_result.get('output', '')}")
                        else:
                            live_box2.error(f"❌ 실행 실패\n\n{exec_result.get('error', '')}")

                    elif node_name == "error_analysis":
                        retry = node_state.get("retry_count", 0)
                        add_agent_log("Error Analysis", f"에러 분석 재시도 {retry}/3")
                        live_box2.warning(f"⚠️ 에러 분석 중... (재시도 {retry}/3)")

                    elif node_name == "output":
                        output = node_state.get("final_output", "")
                        add_agent_log("Output Agent", "문서 작성 완료", output)
                        live_box2.markdown("**📄 결과 정리 완료**")

                    final_result = node_state

            st.session_state.result = final_result
            st.session_state.phase = "phase2_done"
            st.rerun()

        except Exception as e:
            st.error(f"오류: {str(e)}")
            st.session_state.phase = "idle"

    # ── 최종 결과 출력 ─────────────────────────────────────
    if st.session_state.phase == "phase2_done" and st.session_state.result:
        result = st.session_state.result
        st.divider()
        st.subheader("🎉 완료!")

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

        st.divider()
        if st.button("🔄 새로 시작", use_container_width=True):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

# ══════════════════════════════════════════════════════════
# 탭 2: 모니터링
# ══════════════════════════════════════════════════════════
with tab2:
    st.subheader("📊 에이전트 협업 모니터링")
    st.caption(f"세션 ID: `{st.session_state.session_id}`")

    if not st.session_state.agent_logs:
        st.info("아직 실행된 파이프라인이 없습니다.")
    else:
        for log in st.session_state.agent_logs:
            icon = "🔍" if "Research" in log["agent"] else \
                   "🦙" if "Code" in log["agent"] else \
                   "🐳" if "Execution" in log["agent"] else \
                   "📄" if "Output" in log["agent"] else "⚙️"

            with st.expander(f"{icon} {log['agent']} — {log['action']}", expanded=False):
                if log.get("content"):
                    st.text(log["content"])

        st.divider()
        st.markdown("**🔄 파이프라인 흐름**")
        agents = [log["agent"] for log in st.session_state.agent_logs]
        st.code(" → ".join(agents))

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
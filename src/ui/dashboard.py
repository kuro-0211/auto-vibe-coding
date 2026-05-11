import sys
import os
import html as html_lib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import uuid
import time
from dotenv import load_dotenv
from workflows.graph import build_phase1_graph, build_phase2_graph
from utils.logger import pipeline_logger

load_dotenv("/app/.env")

st.set_page_config(
    page_title="Auto Vibe Coding Engine",
    page_icon="🚀",
    layout="wide"
)

st.html("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>
html, body, [class*="css"] {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp { background: #e8e8ed !important; }
.main .block-container { padding: 0 !important; max-width: 100% !important; }
#MainMenu, header, footer { visibility: hidden; }
[data-testid="stSidebar"] { background: #1d1d1f !important; border-right: 1px solid rgba(255,255,255,0.1) !important; }
[data-testid="stSidebar"] > div { padding: 0 !important; }
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div { color: #f5f5f7 !important; }
[data-testid="stSidebar"] .stButton > button { background: transparent !important; color: #8e8e93 !important; border: none !important; font-size: 13px !important; font-weight: 500 !important; text-align: left !important; padding: 9px 14px !important; border-radius: 8px !important; width: 100% !important; }
[data-testid="stSidebar"] .stButton > button:hover { background: #2c2c2e !important; color: #f5f5f7 !important; }
[data-testid="stSidebar"] .stButton > button[kind="primary"] { background: #3a3a3c !important; color: #ffffff !important; border: 1px solid rgba(255,255,255,0.15) !important; }
[data-testid="stSidebar"] [data-testid="metric-container"] { background: #2c2c2e !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; }
[data-testid="stSidebar"] [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 20px !important; font-weight: 600 !important; }
[data-testid="stSidebar"] [data-testid="stMetricLabel"] { color: #8e8e93 !important; font-size: 11px !important; }
.stButton > button { font-family: 'Pretendard', sans-serif !important; font-size: 13px !important; font-weight: 500 !important; border-radius: 8px !important; border: 1.5px solid rgba(0,0,0,0.18) !important; background: #ffffff !important; color: #1d1d1f !important; padding: 8px 14px !important; }
.stButton > button:hover { background: #f0f0f5 !important; }
.stButton > button[kind="primary"] { background: #1d1d1f !important; color: #ffffff !important; border-color: #1d1d1f !important; }
.stButton > button[kind="primary"]:hover { background: #3a3a3c !important; }
.stTextArea textarea { font-family: 'Pretendard', sans-serif !important; font-size: 14px !important; border-radius: 8px !important; border: 1.5px solid rgba(0,0,0,0.18) !important; background: #ffffff !important; color: #1d1d1f !important; line-height: 1.6 !important; }
.stTextArea textarea:focus { border-color: #0066cc !important; box-shadow: 0 0 0 3px rgba(0,102,204,0.15) !important; }
.stTextArea label { font-size: 10px !important; font-weight: 700 !important; color: #aeaeb2 !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; }
.stCheckbox label { font-family: 'Pretendard', sans-serif !important; font-size: 13px !important; color: #6e6e73 !important; }
[data-testid="stForm"] { background: transparent !important; border: none !important; padding: 0 !important; }
.streamlit-expanderHeader { font-family: 'Pretendard', sans-serif !important; font-size: 13px !important; font-weight: 500 !important; border-radius: 8px !important; border: 1.5px solid rgba(0,0,0,0.15) !important; background: #ffffff !important; color: #1d1d1f !important; }
.streamlit-expanderContent { border: 1.5px solid rgba(0,0,0,0.15) !important; border-top: none !important; border-radius: 0 0 8px 8px !important; background: #ffffff !important; }
.stCodeBlock { border-radius: 8px !important; }
.stSuccess, .stError, .stWarning, .stInfo { border-radius: 8px !important; font-family: 'Pretendard', sans-serif !important; font-size: 13px !important; }
[data-testid="metric-container"] { background: #ffffff !important; border: 1.5px solid rgba(0,0,0,0.15) !important; border-radius: 10px !important; padding: 12px 16px !important; }
[data-testid="stMetricValue"] { font-family: 'Pretendard', sans-serif !important; font-size: 22px !important; font-weight: 600 !important; color: #1d1d1f !important; }
[data-testid="stMetricLabel"] { font-family: 'Pretendard', sans-serif !important; font-size: 11px !important; color: #6e6e73 !important; }
[data-testid="column"]:first-child { background: #f0f0f5; border-right: 1.5px solid rgba(0,0,0,0.12); padding: 16px !important; }
[data-testid="column"]:nth-child(2) { background: #e8e8ed; padding: 16px !important; }
</style>
""")

BADGE = {
    "green": ("#d4edda", "#1a5e2a"),
    "blue":  ("#cce4ff", "#003d7a"),
    "amber": ("#fde8c0", "#6b3f00"),
    "red":   ("#ffd5d5", "#7a1515"),
    "gray":  ("#e8e8ed", "#6e6e73"),
}

def card_html(title, badge_text, badge_key, body, icon=""):
    bg, color = BADGE[badge_key]
    return f"""<div style="background:#fff;border:1.5px solid rgba(0,0,0,0.15);border-radius:12px;padding:16px;margin-bottom:12px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
            <div style="font-size:13px;font-weight:600;color:#1d1d1f;">{icon} {title}</div>
            <span style="font-size:11px;font-weight:600;padding:3px 10px;border-radius:999px;background:{bg};color:{color};">{badge_text}</span>
        </div>
        <div>{body}</div>
    </div>"""

def step_html(key, icon, label, status_map):
    s = status_map.get(key, "idle")
    if s == "done":
        bg, color, dot = "#d4edda", "#1a5e2a", "#1a7f37"
    elif s == "running":
        bg, color, dot = "#cce4ff", "#003d7a", "#0066cc"
    else:
        bg, color, dot = "#e8e8ed", "#6e6e73", "#aeaeb2"
    return f"""<div style="display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;font-size:12px;font-weight:500;margin-bottom:4px;color:{color};background:{bg};">
    <div style="width:7px;height:7px;border-radius:50%;background:{dot};flex-shrink:0;"></div>
    {icon} {label}
</div>"""

ALL_STEPS = [
    ("research",        "🔍", "Research Agent"),
    ("code_decision",   "💡", "코드 필요 여부"),
    ("code_generation", "🦙", "코드 생성"),
    ("code_review",     "🔍", "코드 리뷰"),
    ("execution",       "🐳", "Docker 실행"),
    ("error_analysis",  "⚠️", "에러 분석"),
    ("output",          "📄", "결과 정리"),
    ("email",           "📧", "이메일 발송"),
]

defaults = {
    "session_id": str(uuid.uuid4()),
    "phase": "idle",
    "phase1_result": None,
    "result": None,
    "send_email": False,
    "agent_logs": [],
    "step_status": {},
    "user_input": "",
    "start_time": None,
    "elapsed": 0,
    "current_page": "run",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def add_log(agent, action, content=""):
    st.session_state.agent_logs.append({
        "agent": agent, "action": action,
        "content": content[:300] if content else ""
    })

def set_step(key, status):
    st.session_state.step_status[key] = status

# ── 사이드바 ───────────────────────────────────────────────
with st.sidebar:
    st.html("""
    <div style="padding:22px 16px 16px;border-bottom:1px solid rgba(255,255,255,0.1);margin-bottom:8px;">
        <div style="font-size:14px;font-weight:700;color:#f5f5f7;line-height:1.35;margin-bottom:6px;">Auto Vibe<br>Coding Engine</div>
        <span style="font-size:11px;color:#8e8e93;background:rgba(255,255,255,0.08);padding:2px 8px;border-radius:999px;">v1.0.0</span>
    </div>
    """)

    for page_id, icon, label in [("run","🚀","실행"),("monitor","📊","모니터링"),("log","📝","로그")]:
        is_active = st.session_state.current_page == page_id
        if st.button(f"{icon}  {label}", key=f"nav_{page_id}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.current_page = page_id
            st.rerun()

    st.html("<div style='height:1px;background:rgba(255,255,255,0.1);margin:12px 0;'></div>")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("토큰", f"{pipeline_logger.token_usage.get('school_api', 0):,}")
    with col2:
        st.metric("시간", f"{st.session_state.elapsed}s")

    st.html(f"""
    <div style="padding:10px 4px 4px;">
        <div style="font-size:10px;font-weight:700;color:rgba(255,255,255,0.3);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">세션</div>
        <div style="font-size:11px;color:rgba(255,255,255,0.35);word-break:break-all;font-family:monospace;">
            {st.session_state.session_id[:22]}...
        </div>
    </div>
    """)

# ── 상단 바 ────────────────────────────────────────────────
phase_labels = {
    "idle": "대기 중", "running_phase1": "Phase 1 실행 중",
    "phase1_done": "승인 대기", "running_phase2": "Phase 2 실행 중", "phase2_done": "완료",
}
page_titles = {"run": "실행", "monitor": "모니터링", "log": "로그"}

st.html(f"""
<div style="display:flex;align-items:center;justify-content:space-between;padding:13px 20px;
border-bottom:1.5px solid rgba(0,0,0,0.15);background:#ffffff;">
    <span style="font-size:15px;font-weight:600;color:#1d1d1f;">{page_titles.get(st.session_state.current_page,'')}</span>
    <span style="font-size:11px;color:#6e6e73;background:#e8e8ed;padding:5px 12px;
    border-radius:999px;border:1px solid rgba(0,0,0,0.12);font-weight:500;">{phase_labels.get(st.session_state.phase,'')}</span>
</div>
""")

# ══════════════════════════════════════════════════════════
# 실행 페이지
# ══════════════════════════════════════════════════════════
if st.session_state.current_page == "run":
    left, right = st.columns([1, 2], gap="small")

    with left:
        with st.form("input_form"):
            user_input = st.text_area(
                "입력",
                placeholder="키워드 또는 목적을 입력하세요\n예: FastAPI로 REST API 서버 만들어줘",
                height=120
            )
            send_email = st.checkbox("📧  이메일로 받기")
            submitted = st.form_submit_button("▶  실행", use_container_width=True, type="primary")

        if submitted and user_input.strip():
            pipeline_logger.reset()
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.phase = "running_phase1"
            st.session_state.phase1_result = None
            st.session_state.result = None
            st.session_state.send_email = send_email
            st.session_state.agent_logs = []
            st.session_state.step_status = {}
            st.session_state.user_input = user_input
            st.session_state.start_time = time.time()
            st.session_state.elapsed = 0
            st.rerun()
        elif submitted:
            st.warning("입력값을 작성해주세요.")

        st.html("<div style='height:1px;background:rgba(0,0,0,0.12);margin:14px 0;'></div>")
        st.html("<div style='font-size:10px;font-weight:700;color:#aeaeb2;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;'>파이프라인 단계</div>")

        step_placeholders = {}
        for key, icon, label in ALL_STEPS:
            step_placeholders[key] = st.empty()
            step_placeholders[key].markdown(
                step_html(key, icon, label, st.session_state.step_status),
                unsafe_allow_html=True
            )

    with right:

        # ── 대기 중 ────────────────────────────────────────
        if st.session_state.phase == "idle":
            st.html("""
            <div style="background:#fff;border:1.5px solid rgba(0,0,0,0.15);border-radius:12px;
            padding:56px 16px;text-align:center;margin-top:8px;">
                <div style="font-size:36px;margin-bottom:14px;">🚀</div>
                <div style="font-size:15px;font-weight:600;color:#1d1d1f;margin-bottom:6px;">시작할 준비가 됐어요</div>
                <div style="font-size:13px;color:#6e6e73;line-height:1.6;">
                    왼쪽 입력창에 키워드나 목적을 입력하고<br>실행 버튼을 눌러주세요.
                </div>
            </div>
            """)

        # ── Phase 1 실행 중 ────────────────────────────────
        elif st.session_state.phase == "running_phase1":
            live_research = st.empty()
            live_code = st.empty()

            initial_state = {
                "user_input": st.session_state.user_input,
                "send_email": st.session_state.send_email,
                "research_result": None, "code_result": None,
                "execution_result": None, "final_output": None,
                "error": None, "error_analysis": None,
                "retry_count": 0, "needs_code": None,
            }
            config = {"configurable": {"thread_id": st.session_state.session_id}}
            try:
                graph = build_phase1_graph()
                for stream_output in graph.stream(initial_state, config=config):
                    for node_name, node_state in stream_output.items():
                        set_step(node_name, "done")
                        if node_name in step_placeholders:
                            icon = next((i for k, i, _ in ALL_STEPS if k == node_name), "")
                            lbl = next((l for k, _, l in ALL_STEPS if k == node_name), "")
                            step_placeholders[node_name].markdown(
                                step_html(node_name, icon, lbl, st.session_state.step_status),
                                unsafe_allow_html=True
                            )

                        if node_name == "research":
                            res = node_state.get("research_result", "")
                            add_log("Research Agent", "웹 검색 완료", res)
                            safe_res = html_lib.escape(res[:400])
                            live_research.markdown(card_html(
                                "리서치 결과", "완료", "green",
                                f"<div style='font-size:13px;color:#6e6e73;line-height:1.6;'>{safe_res}...</div>",
                                "🔍"
                            ), unsafe_allow_html=True)

                        elif node_name == "code_decision":
                            add_log("Code Decision", f"코드 필요: {node_state.get('needs_code', False)}")

                        elif node_name == "code_generation":
                            code = node_state.get("code_result", "")
                            add_log("Code Generation", "코드 생성 완료", code)
                            safe_code = html_lib.escape(code[:300])
                            live_code.markdown(card_html(
                                "생성된 코드", "생성 완료", "blue",
                                f"<pre style='background:#f0f0f5;border-radius:8px;padding:12px;font-size:12px;color:#1d1d1f;line-height:1.6;margin:0;overflow:auto;'>{safe_code}</pre>",
                                "🦙"
                            ), unsafe_allow_html=True)

                        elif node_name == "code_review":
                            add_log("Code Review", "코드 리뷰 완료")

                        elif node_name == "output":
                            add_log("Output Agent", "결과 정리 완료")

                        st.session_state.phase1_result = node_state

                if st.session_state.start_time:
                    st.session_state.elapsed = int(time.time() - st.session_state.start_time)
                st.session_state.phase = "phase1_done"
                st.rerun()
            except Exception as e:
                st.error(f"오류: {str(e)}")
                st.session_state.phase = "idle"

        # ── Phase 1 완료 → 승인 대기 ──────────────────────
        elif st.session_state.phase == "phase1_done" and st.session_state.phase1_result:
            result = st.session_state.phase1_result

            # 코드 없이 output 완료된 경우 (리서치만)
            if result.get("final_output") and not result.get("code_result"):
                st.session_state.result = result
                st.session_state.phase = "phase2_done"
                st.rerun()

            if result.get("research_result"):
                safe_res = html_lib.escape(result['research_result'][:400])
                st.markdown(card_html("리서치 결과", "완료", "green",
                    f"<div style='font-size:13px;color:#6e6e73;line-height:1.6;'>{safe_res}...</div>", "🔍"
                ), unsafe_allow_html=True)

            if result.get("code_result"):
                safe_code = html_lib.escape(result['code_result'][:300])
                st.markdown(card_html("생성된 코드", "리뷰 완료", "green",
                    f"<pre style='background:#f0f0f5;border-radius:8px;padding:12px;font-size:12px;color:#1d1d1f;line-height:1.6;margin:0;overflow:auto;'>{safe_code}</pre>",
                    "🦙"
                ), unsafe_allow_html=True)

                st.html("""
                <div style="background:#fde8c0;border:1.5px solid rgba(255,159,10,0.35);border-radius:12px;
                padding:14px 16px;margin-bottom:12px;">
                    <div style="font-size:13px;font-weight:600;color:#6b3f00;margin-bottom:3px;">⏳ 코드 실행 전 승인이 필요합니다</div>
                    <div style="font-size:12px;color:#6b3f00;opacity:0.8;">리뷰된 코드를 확인하고 실행을 승인해주세요.</div>
                </div>
                """)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅  승인 — 코드 실행", use_container_width=True, type="primary"):
                        st.session_state.phase = "running_phase2"
                        st.rerun()
                with col2:
                    if st.button("❌  거절 — 처음부터", use_container_width=True):
                        st.session_state.phase = "idle"
                        st.session_state.phase1_result = None
                        st.rerun()

        # ── Phase 2 실행 중 ────────────────────────────────
        elif st.session_state.phase == "running_phase2" and st.session_state.phase1_result:
            result = st.session_state.phase1_result
            live_exec = st.empty()
            config = {"configurable": {"thread_id": st.session_state.session_id}}

            try:
                graph = build_phase2_graph()
                final_result = None
                for stream_output in graph.stream(result, config=config):
                    for node_name, node_state in stream_output.items():
                        set_step(node_name, "done")
                        if node_name in step_placeholders:
                            icon = next((i for k, i, _ in ALL_STEPS if k == node_name), "")
                            lbl = next((l for k, _, l in ALL_STEPS if k == node_name), "")
                            step_placeholders[node_name].markdown(
                                step_html(node_name, icon, lbl, st.session_state.step_status),
                                unsafe_allow_html=True
                            )

                        if node_name == "execution":
                            exec_r = node_state.get("execution_result", {})
                            add_log("Execution", "실행 완료", str(exec_r))
                            if exec_r and exec_r.get("success"):
                                elapsed = exec_r.get('elapsed', 0)
                                lines = exec_r.get('lines', 0)
                                safe_out = html_lib.escape(exec_r.get('output', ''))
                                st.markdown(card_html("실행 결과", "성공", "green",
                                    f"""<div style='display:flex;gap:12px;margin-bottom:10px;'>
                                    <span style='font-size:11px;background:#d4edda;color:#1a5e2a;padding:2px 8px;border-radius:999px;font-weight:600;'>⏱ {elapsed}s</span>
                                    <span style='font-size:11px;background:#d4edda;color:#1a5e2a;padding:2px 8px;border-radius:999px;font-weight:600;'>📄 {lines}줄 출력</span>
                                    </div>
                                    <pre style='background:#d4edda;border-radius:8px;padding:12px;font-size:12px;color:#1a5e2a;line-height:1.6;margin:0;'>$ python solution.py\n{safe_out}</pre>""",
                                    "🐳"
                                ), unsafe_allow_html=True)
                            elif exec_r:
                                safe_err = html_lib.escape(exec_r.get('error', '')[:200])
                                live_exec.markdown(card_html("실행 결과", "실패 — 재시도 중", "amber",
                                    f"<pre style='background:#ffd5d5;border-radius:8px;padding:12px;font-size:12px;color:#7a1515;line-height:1.6;margin:0;'>{safe_err}</pre>",
                                    "🐳"
                                ), unsafe_allow_html=True)

                        elif node_name == "error_analysis":
                            retry = node_state.get("retry_count", 0)
                            analysis = node_state.get("error_analysis", "")
                            add_log("Error Analysis", f"에러 분석 {retry}/3", analysis)
                            if analysis:
                                safe_analysis = html_lib.escape(analysis)
                                live_exec.markdown(card_html(
                                    f"에러 분석 ({retry}/3)", "분석 완료", "amber",
                                    f"<div style='font-size:13px;color:#6b3f00;line-height:1.8;white-space:pre-wrap;'>{safe_analysis}</div>",
                                    "⚠️"
                                ), unsafe_allow_html=True)

                        elif node_name == "output":
                            add_log("Output Agent", "결과 정리 완료")

                        final_result = node_state

                if st.session_state.start_time:
                    st.session_state.elapsed = int(time.time() - st.session_state.start_time)
                st.session_state.result = final_result
                st.session_state.phase = "phase2_done"
                st.rerun()

            except Exception as e:
                st.error(f"오류: {str(e)}")
                st.session_state.phase = "idle"

        # ── 최종 결과 ──────────────────────────────────────
        elif st.session_state.phase == "phase2_done" and st.session_state.result:
            result = st.session_state.result
            exec_r = result.get("execution_result")
            error_analysis = result.get("error_analysis", "")
            retry_count = result.get("retry_count", 0)

            # 실행 성공
            if exec_r and exec_r.get("success"):
                safe_out = html_lib.escape(exec_r.get('output', ''))
                st.markdown(card_html("실행 결과", "성공", "green",
                    f"<pre style='background:#d4edda;border-radius:8px;padding:12px;font-size:12px;color:#1a5e2a;line-height:1.6;margin:0;'>$ python solution.py\n{safe_out}</pre>",
                    "🐳"
                ), unsafe_allow_html=True)

                if result.get("code_result"):
                    with st.expander("💻  생성된 코드", expanded=False):
                        st.code(result["code_result"], language="python")

                if result.get("final_output"):
                    with st.expander("📄  최종 결과 문서", expanded=True):
                        st.markdown(result["final_output"])

            # 실행 실패
            elif exec_r and not exec_r.get("success"):
                if error_analysis:
                    safe_analysis = html_lib.escape(error_analysis)
                    st.markdown(card_html(
                        f"에러 분석 결과 ({retry_count}회 시도)", "실패", "red",
                        f"<div style='font-size:13px;color:#7a1515;line-height:1.8;white-space:pre-wrap;'>{safe_analysis}</div>",
                        "⚠️"
                    ), unsafe_allow_html=True)
                else:
                    safe_err = html_lib.escape(exec_r.get('error', '')[:300])
                    st.markdown(card_html("실행 결과", f"실패 ({retry_count}회 시도)", "red",
                        f"<pre style='background:#ffd5d5;border-radius:8px;padding:12px;font-size:12px;color:#7a1515;line-height:1.6;margin:0;'>{safe_err}</pre>",
                        "🐳"
                    ), unsafe_allow_html=True)

                if result.get("code_result"):
                    with st.expander("💻  최종 생성된 코드", expanded=True):
                        st.code(result["code_result"], language="python")

            # 코드 없음 (리서치만)
            else:
                if result.get("final_output"):
                    with st.expander("📄  전체 결과 문서", expanded=True):
                        st.markdown(result["final_output"])

            # 리서치 결과는 항상 접혀있게
            if result.get("research_result"):
                with st.expander("🔍  리서치 결과", expanded=False):
                    st.markdown(result["research_result"])

            st.html("<div style='height:1px;background:rgba(0,0,0,0.12);margin:14px 0;'></div>")
            if st.button("🔄  새로 시작", use_container_width=True):
                for k, v in defaults.items():
                    st.session_state[k] = v
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()

# ══════════════════════════════════════════════════════════
# 모니터링 페이지
# ══════════════════════════════════════════════════════════
elif st.session_state.current_page == "monitor":
    if not st.session_state.agent_logs:
        st.html("""
        <div style="background:#fff;border:1.5px solid rgba(0,0,0,0.15);border-radius:12px;
        padding:56px 16px;text-align:center;margin:16px;">
            <div style="font-size:36px;margin-bottom:14px;">📊</div>
            <div style="font-size:15px;font-weight:600;color:#1d1d1f;margin-bottom:6px;">아직 실행된 파이프라인이 없습니다</div>
            <div style="font-size:13px;color:#6e6e73;">실행 탭에서 먼저 실행해주세요.</div>
        </div>
        """)
    else:
        st.markdown("<div style='padding:16px;'>", unsafe_allow_html=True)
        agents = [log["agent"] for log in st.session_state.agent_logs]
        badges = " → ".join([
            f"<span style='font-size:11px;font-weight:600;padding:3px 10px;border-radius:999px;background:#cce4ff;color:#003d7a;'>{html_lib.escape(a)}</span>"
            for a in agents
        ])
        st.markdown(f"""
        <div style="background:#fff;border:1.5px solid rgba(0,0,0,0.15);border-radius:12px;padding:16px;margin-bottom:12px;">
            <div style="font-size:13px;font-weight:600;color:#1d1d1f;margin-bottom:12px;">🔄 파이프라인 흐름</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;">{badges}</div>
        </div>
        """, unsafe_allow_html=True)

        for log in st.session_state.agent_logs:
            icon = "🔍" if "Research" in log["agent"] else \
                   "🦙" if "Code" in log["agent"] else \
                   "🐳" if "Execution" in log["agent"] else \
                   "⚠️" if "Error" in log["agent"] else \
                   "📄" if "Output" in log["agent"] else "⚙️"
            with st.expander(f"{icon}  {log['agent']} — {log['action']}", expanded=False):
                if log.get("content"):
                    safe_content = html_lib.escape(log['content'])
                    st.markdown(f"<div style='font-size:13px;color:#6e6e73;line-height:1.6;white-space:pre-wrap;'>{safe_content}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 로그 페이지
# ══════════════════════════════════════════════════════════
elif st.session_state.current_page == "log":
    st.markdown("<div style='padding:16px;'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("학교 API 토큰", f"{pipeline_logger.token_usage.get('school_api', 0):,}")
    with col2:
        local_calls = len([l for l in pipeline_logger.logs if 'gpt' not in l['model']])
        st.metric("로컬 LLM 호출", f"{local_calls}회")
    with col3:
        st.metric("총 호출", f"{len(pipeline_logger.logs)}회")

    st.html("<div style='height:1px;background:rgba(0,0,0,0.12);margin:14px 0;'></div>")

    if not pipeline_logger.logs:
        st.html("""
        <div style="background:#fff;border:1.5px solid rgba(0,0,0,0.15);border-radius:12px;
        padding:56px 16px;text-align:center;">
            <div style="font-size:36px;margin-bottom:14px;">📝</div>
            <div style="font-size:15px;font-weight:600;color:#1d1d1f;">아직 실행된 로그가 없습니다</div>
        </div>
        """)
    else:
        for log in pipeline_logger.logs:
            with st.expander(f"[{log['time']}]  {log['model']} — {log['tokens']} tokens", expanded=False):
                st.markdown("**프롬프트**")
                st.text(log["prompt"])
                st.markdown("**응답**")
                st.text(log["response"])

    st.markdown("</div>", unsafe_allow_html=True)

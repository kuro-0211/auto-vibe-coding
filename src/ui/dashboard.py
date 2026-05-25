import sys
import os
import html as html_lib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import uuid
import time
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from workflows.graph import build_phase1_graph, build_phase2_graph
from agents.output_agent import export_to_pdf, export_to_docx
from utils.history import list_history, get_history, clear_history
from utils.logger import pipeline_logger
from utils import scheduler as sched_mod

sched_mod.init_scheduler()
load_dotenv("/app/.env")

st.set_page_config(
    page_title="ARIA",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════
# Claude-style Dark Theme CSS
# ══════════════════════════════════════════════════════════
st.html("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>
html, body, [class*="css"] { font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important; }

.stApp { background: #faf9f5 !important; color: #1f1f1f !important; }
.main .block-container { padding: 24px 24px 220px 24px !important; max-width: 860px !important; margin: 0 auto !important; }

/* 메뉴/푸터만 숨기고 사이드바 토글 버튼은 살림 */
#MainMenu, footer { visibility: hidden; }
header { background: transparent !important; }
[data-testid="stHeader"] { background: transparent !important; height: auto !important; }
[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] { visibility: visible !important; color: #1f1f1f !important; }

/* ── Sidebar (warm cream, 항상 보이게) ─────────────────── */
[data-testid="stSidebar"] {
    background: #f0eee6 !important;
    border-right: 1px solid rgba(0,0,0,0.10) !important;
    width: 260px !important; min-width: 260px !important;
}
[data-testid="stSidebar"] > div { padding: 0 !important; }
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div, [data-testid="stSidebar"] label { color: #1f1f1f !important; }
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important; color: #1f1f1f !important;
    border: 1px solid transparent !important;
    font-size: 13px !important; font-weight: 500 !important;
    text-align: left !important; padding: 8px 12px !important;
    border-radius: 8px !important; width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover { background: rgba(0,0,0,0.04) !important; }
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: rgba(204,120,92,0.14) !important;
    color: #b86a4f !important;
    border-color: rgba(204,120,92,0.35) !important;
}
[data-testid="stSidebar"] [data-testid="metric-container"] {
    background: #ffffff !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    border-radius: 8px !important; padding: 8px 12px !important;
}
[data-testid="stSidebar"] [data-testid="stMetricValue"] { color: #1f1f1f !important; font-size: 18px !important; font-weight: 600 !important; }
[data-testid="stSidebar"] [data-testid="stMetricLabel"] { color: #6e6e73 !important; font-size: 11px !important; }

/* ── Main buttons ─────────────────────────────────────── */
.stButton > button {
    font-family: 'Pretendard', sans-serif !important;
    font-size: 13px !important; font-weight: 500 !important;
    border-radius: 8px !important;
    border: 1px solid rgba(0,0,0,0.12) !important;
    background: #ffffff !important; color: #1f1f1f !important;
    padding: 8px 14px !important;
}
.stButton > button:hover { background: #f5f4ef !important; }
.stButton > button[kind="primary"] { background: #cc785c !important; color: #ffffff !important; border-color: #cc785c !important; }
.stButton > button[kind="primary"]:hover { background: #b86a4f !important; border-color: #b86a4f !important; }
[data-testid="stDownloadButton"] > button {
    background: #ffffff !important; color: #1f1f1f !important;
    border: 1px solid rgba(0,0,0,0.12) !important; border-radius: 8px !important;
}
[data-testid="stDownloadButton"] > button:hover { background: #f5f4ef !important; }

/* ── Inputs ───────────────────────────────────────────── */
.stTextArea textarea, .stTextInput input, .stNumberInput input {
    background: #ffffff !important; color: #1f1f1f !important;
    border: 1px solid rgba(0,0,0,0.14) !important;
    border-radius: 10px !important; font-family: 'Pretendard', sans-serif !important;
    font-size: 14px !important; line-height: 1.55 !important;
}
.stTextArea textarea:focus, .stTextInput input:focus, .stNumberInput input:focus {
    border-color: #cc785c !important;
    box-shadow: 0 0 0 2px rgba(204,120,92,0.18) !important;
}
.stTextArea label, .stTextInput label, .stNumberInput label, .stSelectbox label, .stCheckbox label {
    color: #6e6e73 !important; font-size: 11px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.06em !important;
}

/* ── Selectbox ───────────────────────────────────────── */
[data-baseweb="select"] > div {
    background: #ffffff !important;
    border-color: rgba(0,0,0,0.14) !important;
    color: #1f1f1f !important; border-radius: 10px !important;
}
[data-baseweb="popover"] { background: #ffffff !important; border: 1px solid rgba(0,0,0,0.08) !important; }
[role="listbox"] { background: #ffffff !important; }
[role="option"] { color: #1f1f1f !important; }
[role="option"]:hover { background: #f5f4ef !important; }

/* ── Checkbox ─────────────────────────────────────────── */
.stCheckbox label { text-transform: none !important; letter-spacing: 0 !important; font-size: 13px !important; color: #1f1f1f !important; font-weight: 500 !important; }

/* ── Code blocks ──────────────────────────────────────── */
.stCodeBlock, pre, code {
    background: #f5f4ef !important; color: #1f1f1f !important;
    border-left: 3px solid #cc785c !important;
    border-radius: 8px !important; font-size: 12.5px !important;
}
.stCodeBlock pre { background: #f5f4ef !important; }

/* ── Markdown text ────────────────────────────────────── */
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown strong, .stMarkdown em { color: #1f1f1f !important; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #1f1f1f !important; }
.stMarkdown a { color: #cc785c !important; }
.stMarkdown blockquote { border-left: 3px solid #cc785c !important; background: rgba(204,120,92,0.06) !important; color: #1f1f1f !important; }

/* ── Expander ─────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid rgba(0,0,0,0.10) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary { color: #1f1f1f !important; font-size: 13px !important; font-weight: 500 !important; }
[data-testid="stExpander"] summary:hover { background: #fafaf7 !important; }

/* ── Alerts ───────────────────────────────────────────── */
.stSuccess { background: rgba(76,175,80,0.10) !important; border: 1px solid rgba(76,175,80,0.30) !important; color: #2e7d32 !important; border-radius: 10px !important; }
.stError   { background: rgba(239,83,80,0.08) !important; border: 1px solid rgba(239,83,80,0.30) !important; color: #c62828 !important; border-radius: 10px !important; }
.stWarning { background: rgba(255,152,0,0.10) !important; border: 1px solid rgba(255,152,0,0.30) !important; color: #b26500 !important; border-radius: 10px !important; }
.stInfo    { background: #f5f4ef !important; border: 1px solid rgba(0,0,0,0.08) !important; color: #1f1f1f !important; border-radius: 10px !important; }

/* ── Metric (main) ────────────────────────────────────── */
[data-testid="metric-container"] {
    background: #ffffff !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    border-radius: 12px !important; padding: 12px 16px !important;
}
[data-testid="stMetricValue"] { color: #1f1f1f !important; font-size: 22px !important; font-weight: 600 !important; }
[data-testid="stMetricLabel"] { color: #6e6e73 !important; font-size: 11px !important; }

/* ── Tabs ─────────────────────────────────────────────── */
[data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid rgba(0,0,0,0.10) !important; }
[data-baseweb="tab"] { color: #6e6e73 !important; }
[data-baseweb="tab"][aria-selected="true"] { color: #cc785c !important; border-bottom-color: #cc785c !important; }

/* ── Captions ─────────────────────────────────────────── */
[data-testid="stCaptionContainer"], small { color: #6e6e73 !important; }

/* ── Forms ───────────────────────────────────────────── */
[data-testid="stForm"] { background: transparent !important; border: none !important; padding: 0 !important; }

/* ── Sticky input bar (실행 페이지 전용) ─────────────── */
.st-key-input_bar {
    position: fixed !important;
    bottom: 0 !important;
    left: 260px !important;
    right: 0 !important;
    background: linear-gradient(180deg, rgba(250,249,245,0.0) 0%, #faf9f5 22%) !important;
    padding: 28px 24px 18px 24px !important;
    z-index: 90 !important;
    border-top: 1px solid rgba(0,0,0,0.08) !important;
}
.st-key-input_bar > div { max-width: 812px; margin: 0 auto; }

@media (max-width: 768px) {
    .st-key-input_bar { left: 0 !important; }
}
</style>
""")

# ══════════════════════════════════════════════════════════
# 상수 / 설정
# ══════════════════════════════════════════════════════════
ACCENT = "#cc785c"
CARD_BG = "#ffffff"
BORDER = "rgba(0,0,0,0.10)"
TEXT = "#1f1f1f"
SUB = "#6e6e73"
HINT = "#aeaeb2"
SUCCESS = "#2e7d32"
FAIL = "#c62828"
WARN = "#b26500"
CODE_BG = "#f5f4ef"

ALL_STEPS = [
    ("research",        "Research"),
    ("code_decision",   "Decision"),
    ("code_generation", "Generate"),
    ("code_review",     "Review"),
    ("human_review",    "Edit"),
    ("execution",       "Execute"),
    ("error_analysis",  "Analyze"),
    ("output",          "Output"),
    ("email",           "Email"),
]

EXAMPLES = [
    "파이썬으로 정렬 알고리즘 구현해줘",
    "FastAPI REST API 만들어줘",
    "다익스트라 알고리즘 설명해줘",
    "비트코인 최근 1주일 동향 정리",
]

# ══════════════════════════════════════════════════════════
# Session defaults
# ══════════════════════════════════════════════════════════
defaults = {
    "session_id": str(uuid.uuid4()),
    "phase": "idle",
    "phase1_result": None,
    "result": None,
    "send_email": False,
    "email_format": "pdf",
    "agent_logs": [],
    "step_status": {},
    "user_input": "",
    "pending_input": "",  # 입력창 prefill용
    "start_time": None,
    "elapsed": 0,
    "current_page": "run",
    "selected_history_id": None,
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


def reset_run_state(prefill_input: str = ""):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.phase = "idle"
    st.session_state.phase1_result = None
    st.session_state.result = None
    st.session_state.agent_logs = []
    st.session_state.step_status = {}
    st.session_state.user_input = prefill_input
    st.session_state.pending_input = prefill_input
    st.session_state.start_time = None
    st.session_state.elapsed = 0
    st.session_state.selected_history_id = None


@st.cache_data(show_spinner=False, max_entries=200)
def _build_history_files(history_id: int, final_output: str, code: str) -> tuple[bytes, bytes]:
    return export_to_pdf(final_output, code), export_to_docx(final_output, code)


def _date_group(iso_str: str) -> str:
    try:
        d = datetime.fromisoformat(iso_str).date()
    except Exception:
        return "이전"
    today = date.today()
    if d == today:
        return "오늘"
    if d == today - timedelta(days=1):
        return "어제"
    if d >= today - timedelta(days=7):
        return "이번 주"
    if d >= today - timedelta(days=30):
        return "이번 달"
    return "이전"


# ══════════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.html("""
    <div style="padding:18px 16px 10px;">
        <div style="display:flex;align-items:center;gap:8px;">
            <div style="width:28px;height:28px;border-radius:8px;background:#cc785c;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;">A</div>
            <div>
                <div style="font-size:14px;font-weight:700;color:#1f1f1f;line-height:1.1;">ARIA</div>
                <div style="font-size:10px;color:#6e6e73;">v1.3 · Claude UI</div>
            </div>
        </div>
    </div>
    """)

    # 새 대화 (실행 페이지로 + 상태 초기화)
    if st.button("✚  새 대화", key="nav_new", use_container_width=True,
                 type="primary" if st.session_state.current_page == "run" else "secondary"):
        reset_run_state()
        st.session_state.current_page = "run"
        st.rerun()

    st.html("<div style='height:1px;background:rgba(0,0,0,0.08);margin:10px 12px;'></div>")

    # 히스토리 목록 (날짜 그룹핑)
    st.html("<div style='font-size:10px;font-weight:700;color:#6e6e73;text-transform:uppercase;letter-spacing:0.06em;padding:4px 16px 6px;'>히스토리</div>")

    hist_items = list_history(limit=50)
    if not hist_items:
        st.html("<div style='font-size:12px;color:#aeaeb2;padding:4px 16px 12px;'>아직 비어 있어요</div>")
    else:
        groups: dict[str, list] = {}
        for item in hist_items:
            g = _date_group(item.get("created_at", ""))
            groups.setdefault(g, []).append(item)
        order = ["오늘", "어제", "이번 주", "이번 달", "이전"]
        for grp in order:
            if grp not in groups:
                continue
            st.html(f"<div style='font-size:10px;color:#aeaeb2;padding:6px 16px 2px;font-weight:600;'>{grp}</div>")
            for item in groups[grp]:
                preview = (item.get("user_input") or "").strip()
                preview = preview[:25] + ("…" if len(preview) > 25 else "")
                if not preview:
                    preview = "(빈 입력)"
                if item.get("success"):
                    dot = "🟢" if item["success"] else "🔴"
                else:
                    dot = "🔴"
                label = f"{dot}  {preview}"
                if st.button(label, key=f"hist_{item['id']}", use_container_width=True):
                    st.session_state.selected_history_id = item["id"]
                    st.session_state.current_page = "history_detail"
                    st.rerun()

    st.html("<div style='height:1px;background:rgba(0,0,0,0.08);margin:10px 12px;'></div>")

    # 하단 nav
    for page_id, icon, label in [
        ("monitor",  "📊", "모니터링"),
        ("log",      "📝", "로그"),
        ("schedule", "⏰", "스케줄"),
    ]:
        is_active = st.session_state.current_page == page_id
        if st.button(f"{icon}  {label}", key=f"nav_{page_id}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.current_page = page_id
            st.rerun()

    st.html("<div style='height:1px;background:rgba(0,0,0,0.08);margin:10px 12px;'></div>")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("토큰", f"{pipeline_logger.token_usage.get('school_api', 0):,}")
    with c2:
        st.metric("시간", f"{st.session_state.elapsed}s")

    st.html(f"""
    <div style="padding:10px 16px 14px;">
        <div style="font-size:10px;font-weight:700;color:#aeaeb2;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">세션</div>
        <div style="font-size:10px;color:#6e6e73;font-family:monospace;word-break:break-all;">{st.session_state.session_id[:22]}…</div>
    </div>
    """)


# ══════════════════════════════════════════════════════════
# 페이지 헤더
# ══════════════════════════════════════════════════════════
phase_labels = {
    "idle": "대기 중",
    "running_phase1": "Phase 1 실행 중",
    "phase1_done": "사용자 검토 대기",
    "running_phase2": "Phase 2 실행 중",
    "phase2_done": "완료",
}
page_titles = {
    "run": "ARIA",
    "monitor": "모니터링",
    "log": "로그",
    "schedule": "스케줄",
    "history_detail": "히스토리 상세",
}


def page_header(title: str, sub: str = ""):
    st.html(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin:8px 0 22px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:24px;height:24px;border-radius:6px;background:#cc785c;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;">A</div>
        <span style="font-size:18px;font-weight:600;color:#1f1f1f;">{html_lib.escape(title)}</span>
      </div>
      <span style="font-size:11px;color:#6e6e73;background:#ffffff;padding:4px 12px;border-radius:999px;border:1px solid rgba(0,0,0,0.10);">{html_lib.escape(sub)}</span>
    </div>
    """)


# ══════════════════════════════════════════════════════════
# 카드 / 헬퍼
# ══════════════════════════════════════════════════════════
def card(title: str, body_html: str, badge: str | None = None, badge_color: str = ACCENT, icon: str = ""):
    badge_html = ""
    if badge:
        badge_html = f"""<span style="font-size:11px;font-weight:600;padding:3px 10px;border-radius:999px;background:{badge_color}22;color:{badge_color};border:1px solid {badge_color}44;">{html_lib.escape(badge)}</span>"""
    st.html(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:12px;padding:16px 18px;margin-bottom:14px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
            <div style="font-size:10px;font-weight:700;color:{SUB};text-transform:uppercase;letter-spacing:0.08em;">{icon} {html_lib.escape(title)}</div>
            {badge_html}
        </div>
        <div style="color:{TEXT};font-size:13.5px;line-height:1.65;">{body_html}</div>
    </div>
    """)


def pipeline_bar(status_map: dict):
    parts = []
    for key, label in ALL_STEPS:
        s = status_map.get(key, "idle")
        if s == "done":
            color, bg, dot = ACCENT, f"{ACCENT}1f", ACCENT
            anim = ""
        elif s == "running":
            color, bg, dot = "#1f1f1f", "rgba(204,120,92,0.10)", ACCENT
            anim = "animation:pulse 1.2s ease-in-out infinite;"
        else:
            color, bg, dot = "#aeaeb2", "#f5f4ef", "#d4d4d0"
            anim = ""
        parts.append(f"""
        <div style="display:flex;align-items:center;gap:6px;padding:5px 10px;border-radius:999px;background:{bg};color:{color};font-size:11px;font-weight:600;">
            <span style="width:6px;height:6px;border-radius:50%;background:{dot};{anim}"></span>
            {label}
        </div>
        """)
    st.html(f"""
    <style>@keyframes pulse {{0%,100% {{opacity:1}} 50% {{opacity:0.4}}}}</style>
    <div style="display:flex;gap:6px;flex-wrap:wrap;padding:0 4px 12px;justify-content:center;">{''.join(parts)}</div>
    """)


# ══════════════════════════════════════════════════════════
# 실행 페이지
# ══════════════════════════════════════════════════════════
if st.session_state.current_page == "run":
    page_header(page_titles["run"], phase_labels.get(st.session_state.phase, ""))

    # ── 환영 화면 ──────────────────────────────────────
    if st.session_state.phase == "idle":
        st.html(f"""
        <div style="text-align:center;padding:40px 0 28px;">
            <div style="width:60px;height:60px;border-radius:18px;background:linear-gradient(135deg,#cc785c,#a85b40);display:inline-flex;align-items:center;justify-content:center;font-size:28px;font-weight:700;color:#fff;margin-bottom:16px;">A</div>
            <div style="font-size:24px;font-weight:600;color:#1f1f1f;margin-bottom:6px;">무엇을 도와드릴까요?</div>
            <div style="font-size:13px;color:#6e6e73;">키워드나 목적을 입력하면 리서치 · 코드 생성 · 실행까지 자동 처리해드립니다</div>
        </div>
        """)

        # 예시 카드
        st.html("<div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px;'>")
        ex_cols = st.columns(2)
        for idx, ex in enumerate(EXAMPLES):
            with ex_cols[idx % 2]:
                if st.button(ex, key=f"ex_{idx}", use_container_width=True):
                    st.session_state.pending_input = ex
                    st.rerun()
        st.html("</div>")

    # ── Phase 1 실행 중 ───────────────────────────────
    elif st.session_state.phase == "running_phase1":
        initial_state = {
            "user_input": st.session_state.user_input,
            "send_email": st.session_state.send_email,
            "email_format": st.session_state.email_format,
            "research_result": None, "code_result": None,
            "execution_result": None, "final_output": None,
            "error": None, "error_analysis": None,
            "retry_count": 0, "needs_code": None,
            "edited_code": None,
            "start_time": st.session_state.start_time,
        }
        config = {"configurable": {"thread_id": st.session_state.session_id}}
        live_research = st.empty()
        live_code = st.empty()
        try:
            graph = build_phase1_graph()
            for stream_output in graph.stream(initial_state, config=config):
                for node_name, node_state in stream_output.items():
                    set_step(node_name, "done")
                    if node_name == "research":
                        res = node_state.get("research_result", "") or ""
                        add_log("Research Agent", "웹 검색 완료", res)
                        safe = html_lib.escape(res[:500])
                        with live_research:
                            card("리서치 결과", f"<div style='white-space:pre-wrap;color:#1f1f1f;'>{safe}{'…' if len(res) > 500 else ''}</div>",
                                 badge="완료", badge_color=SUCCESS, icon="🔍")
                    elif node_name == "code_decision":
                        add_log("Code Decision", f"코드 필요: {node_state.get('needs_code', False)}")
                    elif node_name == "code_generation":
                        code = node_state.get("code_result", "") or ""
                        add_log("Code Generation", "코드 생성 완료", code)
                        safe = html_lib.escape(code[:400])
                        with live_code:
                            card("생성된 코드", f"<pre style='background:#f5f4ef;border-left:3px solid {ACCENT};border-radius:8px;padding:12px;font-size:12px;color:#1f1f1f;margin:0;overflow:auto;'>{safe}{'…' if len(code) > 400 else ''}</pre>",
                                 badge="생성", badge_color=ACCENT, icon="🦙")
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
            st.error(f"오류: {e}")
            st.session_state.phase = "idle"

    # ── Phase 1 완료 → HITL 검토 ───────────────────────
    elif st.session_state.phase == "phase1_done" and st.session_state.phase1_result:
        result = st.session_state.phase1_result

        # 코드 없이 끝난 경우 (리서치만) → 바로 phase2_done으로
        if result.get("final_output") and not result.get("code_result"):
            st.session_state.result = result
            st.session_state.phase = "phase2_done"
            st.rerun()

        if result.get("research_result"):
            safe_res = html_lib.escape(result["research_result"][:600])
            card("리서치 결과", f"<div style='white-space:pre-wrap;color:#1f1f1f;'>{safe_res}…</div>",
                 badge="완료", badge_color=SUCCESS, icon="🔍")

        if result.get("code_result"):
            # 코드 검토 안내
            st.html(f"""
            <div style="background:rgba(255,152,0,0.10);border:1px solid rgba(255,152,0,0.30);border-radius:12px;padding:14px 16px;margin-bottom:12px;">
                <div style="font-size:13px;font-weight:600;color:#b26500;margin-bottom:4px;">✏️ 코드 검토 및 수정</div>
                <div style="font-size:12px;color:#b26500;opacity:0.85;">리뷰된 코드를 직접 편집할 수 있습니다. 수정 후 승인하면 편집한 코드로 실행됩니다.</div>
            </div>
            """)

            edited_code = st.text_area(
                "코드 편집",
                value=result["code_result"],
                height=320,
                key="code_editor",
            )

            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("✅  승인 — 실행", use_container_width=True, type="primary"):
                    st.session_state.phase1_result["code_result"] = edited_code
                    st.session_state.phase1_result["edited_code"] = None
                    st.session_state.phase = "running_phase2"
                    st.rerun()
            with col2:
                if st.button("🔄  원본 복원", use_container_width=True):
                    st.session_state.pop("code_editor", None)
                    st.rerun()
            with col3:
                if st.button("❌  거절 — 처음부터", use_container_width=True):
                    reset_run_state()
                    st.rerun()

    # ── Phase 2 실행 중 ───────────────────────────────
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
                    if node_name == "execution":
                        exec_r = node_state.get("execution_result", {}) or {}
                        add_log("Execution", "실행 완료", str(exec_r))
                        if exec_r and exec_r.get("success"):
                            elapsed = exec_r.get("elapsed", 0)
                            lines = exec_r.get("lines", 0)
                            out = html_lib.escape(exec_r.get("output", "") or "")
                            with live_exec:
                                card("실행 결과", f"""
                                <div style='display:flex;gap:8px;margin-bottom:10px;'>
                                  <span style='font-size:11px;background:rgba(76,175,80,0.18);color:#2e7d32;padding:3px 9px;border-radius:999px;font-weight:600;'>⏱ {elapsed}s</span>
                                  <span style='font-size:11px;background:rgba(76,175,80,0.18);color:#2e7d32;padding:3px 9px;border-radius:999px;font-weight:600;'>📄 {lines}줄</span>
                                </div>
                                <pre style='background:#f5f4ef;border-left:3px solid {SUCCESS};border-radius:8px;padding:12px;font-size:12px;color:#2e7d32;margin:0;overflow:auto;'>$ python solution.py\n{out}</pre>
                                """, badge="성공", badge_color=SUCCESS, icon="🐳")
                        elif exec_r:
                            err = html_lib.escape((exec_r.get("error", "") or "")[:300])
                            with live_exec:
                                card("실행 결과", f"<pre style='background:#f5f4ef;border-left:3px solid {WARN};border-radius:8px;padding:12px;font-size:12px;color:#b26500;margin:0;'>{err}</pre>",
                                     badge="실패 — 재시도", badge_color=WARN, icon="🐳")
                    elif node_name == "error_analysis":
                        retry = node_state.get("retry_count", 0)
                        analysis = node_state.get("error_analysis", "") or ""
                        add_log("Error Analysis", f"에러 분석 {retry}/3", analysis)
                        if analysis:
                            safe_a = html_lib.escape(analysis)
                            with live_exec:
                                card(f"에러 분석 ({retry}/3)", f"<div style='white-space:pre-wrap;color:#b26500;'>{safe_a}</div>",
                                     badge="분석 완료", badge_color=WARN, icon="⚠️")
                    elif node_name == "output":
                        add_log("Output Agent", "결과 정리 완료")
                    final_result = node_state

            if st.session_state.start_time:
                st.session_state.elapsed = int(time.time() - st.session_state.start_time)
            st.session_state.result = final_result
            st.session_state.phase = "phase2_done"
            st.rerun()
        except Exception as e:
            st.error(f"오류: {e}")
            st.session_state.phase = "idle"

    # ── 최종 결과 ──────────────────────────────────────
    elif st.session_state.phase == "phase2_done" and st.session_state.result:
        result = st.session_state.result
        exec_r = result.get("execution_result")
        error_analysis = result.get("error_analysis", "")
        retry_count = result.get("retry_count", 0)

        if exec_r and exec_r.get("success"):
            out = html_lib.escape(exec_r.get("output", "") or "")
            card("실행 결과", f"<pre style='background:#f5f4ef;border-left:3px solid {SUCCESS};border-radius:8px;padding:12px;font-size:12px;color:#2e7d32;margin:0;overflow:auto;'>$ python solution.py\n{out}</pre>",
                 badge="성공", badge_color=SUCCESS, icon="🐳")
            if result.get("code_result"):
                with st.expander("💻  생성된 코드", expanded=False):
                    st.code(result["code_result"], language="python")
            if result.get("final_output"):
                with st.expander("📄  최종 결과 문서", expanded=True):
                    st.markdown(result["final_output"])

        elif exec_r and not exec_r.get("success"):
            if error_analysis:
                safe_a = html_lib.escape(error_analysis)
                card(f"에러 분석 결과 ({retry_count}회 시도)", f"<div style='white-space:pre-wrap;color:#c62828;'>{safe_a}</div>",
                     badge="실패", badge_color=FAIL, icon="⚠️")
            else:
                err = html_lib.escape((exec_r.get("error", "") or "")[:400])
                card("실행 결과", f"<pre style='background:#f5f4ef;border-left:3px solid {FAIL};border-radius:8px;padding:12px;font-size:12px;color:#c62828;margin:0;'>{err}</pre>",
                     badge=f"실패 ({retry_count}회)", badge_color=FAIL, icon="🐳")
            if result.get("code_result"):
                with st.expander("💻  최종 생성된 코드", expanded=True):
                    st.code(result["code_result"], language="python")

        else:
            if result.get("final_output"):
                with st.expander("📄  전체 결과 문서", expanded=True):
                    st.markdown(result["final_output"])

        if result.get("research_result"):
            with st.expander("🔍  리서치 결과", expanded=False):
                st.markdown(result["research_result"])

        # 다운로드
        if result.get("final_output"):
            st.html(f"<div style='font-size:10px;font-weight:700;color:{SUB};text-transform:uppercase;letter-spacing:0.06em;margin:18px 0 8px;'>결과 다운로드</div>")
            final_text = result["final_output"]
            code_text = result.get("code_result", "") or ""
            try:
                pdf_bytes = export_to_pdf(final_text, code_text)
                docx_bytes = export_to_docx(final_text, code_text)
                d1, d2, d3 = st.columns(3)
                with d1:
                    st.download_button("📄  PDF", data=pdf_bytes, file_name="aria_result.pdf",
                                       mime="application/pdf", use_container_width=True)
                with d2:
                    st.download_button("📝  Word", data=docx_bytes, file_name="aria_result.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       use_container_width=True)
                with d3:
                    st.download_button("📋  Markdown", data=final_text.encode("utf-8"),
                                       file_name="aria_result.md", mime="text/markdown",
                                       use_container_width=True)
            except Exception as e:
                st.error(f"파일 생성 실패: {e}")

        st.html("<div style='height:14px;'></div>")
        if st.button("✚  새 대화 시작", use_container_width=True):
            reset_run_state()
            st.rerun()

    # ── 입력 바 (하단 고정) ────────────────────────────
    with st.container(key="input_bar"):
        # 파이프라인 상태바
        if st.session_state.phase != "idle":
            pipeline_bar(st.session_state.step_status)

        # 옵션 (한 줄)
        opt_c1, opt_c2 = st.columns([1, 2])
        with opt_c1:
            send_email = st.checkbox("📧  이메일", key="send_email_cb",
                                     value=st.session_state.send_email)
        with opt_c2:
            email_format = st.selectbox(
                "첨부 형식",
                options=["pdf", "docx", "md", "none"],
                format_func=lambda x: {"pdf":"📄 PDF","docx":"📝 Word","md":"📋 MD","none":"🚫 없음"}[x],
                index=["pdf","docx","md","none"].index(st.session_state.email_format),
                key="email_format_sel",
                label_visibility="collapsed",
            )

        with st.form("input_form", clear_on_submit=False):
            user_input = st.text_area(
                "input",
                value=st.session_state.pending_input,
                placeholder="키워드나 목적을 입력하세요... (예: FastAPI로 REST API 만들어줘)",
                height=80,
                label_visibility="collapsed",
                key="input_ta",
            )
            submit_c1, submit_c2 = st.columns([5, 1])
            with submit_c2:
                submitted = st.form_submit_button("▶  실행", type="primary", use_container_width=True)

        if submitted and user_input.strip():
            pipeline_logger.reset()
            reset_run_state()
            st.session_state.phase = "running_phase1"
            st.session_state.send_email = send_email
            st.session_state.email_format = email_format
            st.session_state.user_input = user_input
            st.session_state.start_time = time.time()
            st.session_state.elapsed = 0
            st.session_state.pending_input = ""
            st.rerun()
        elif submitted:
            st.warning("입력 내용을 작성해주세요.")


# ══════════════════════════════════════════════════════════
# 모니터링 페이지
# ══════════════════════════════════════════════════════════
elif st.session_state.current_page == "monitor":
    page_header(page_titles["monitor"], "에이전트 흐름 추적")

    if not st.session_state.agent_logs:
        st.html(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:12px;padding:48px 16px;text-align:center;">
            <div style="font-size:32px;margin-bottom:12px;">📊</div>
            <div style="font-size:15px;font-weight:600;color:{TEXT};margin-bottom:6px;">아직 실행된 파이프라인이 없습니다</div>
            <div style="font-size:13px;color:{SUB};">실행 탭에서 먼저 실행해주세요.</div>
        </div>
        """)
    else:
        agents = [log["agent"] for log in st.session_state.agent_logs]
        badges = " → ".join([
            f"<span style='font-size:11px;font-weight:600;padding:3px 10px;border-radius:999px;background:rgba(204,120,92,0.18);color:#cc785c;'>{html_lib.escape(a)}</span>"
            for a in agents
        ])
        st.html(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:12px;padding:16px;margin-bottom:14px;">
          <div style="font-size:10px;font-weight:700;color:{SUB};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">파이프라인 흐름</div>
          <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;">{badges}</div>
        </div>
        """)

        for log in st.session_state.agent_logs:
            icon = "🔍" if "Research" in log["agent"] else \
                   "🦙" if "Code" in log["agent"] else \
                   "🐳" if "Execution" in log["agent"] else \
                   "⚠️" if "Error" in log["agent"] else \
                   "📄" if "Output" in log["agent"] else "⚙️"
            with st.expander(f"{icon}  {log['agent']} — {log['action']}", expanded=False):
                if log.get("content"):
                    safe = html_lib.escape(log["content"])
                    st.html(f"<div style='font-size:13px;color:#1f1f1f;line-height:1.65;white-space:pre-wrap;'>{safe}</div>")


# ══════════════════════════════════════════════════════════
# 로그 페이지
# ══════════════════════════════════════════════════════════
elif st.session_state.current_page == "log":
    page_header(page_titles["log"], "LLM 호출 내역")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("학교 API 토큰", f"{pipeline_logger.token_usage.get('school_api', 0):,}")
    with c2:
        local_calls = len([l for l in pipeline_logger.logs if "gpt" not in l["model"]])
        st.metric("로컬 LLM 호출", f"{local_calls}회")
    with c3:
        st.metric("총 호출", f"{len(pipeline_logger.logs)}회")

    st.html(f"<div style='height:1px;background:{BORDER};margin:18px 0 12px;'></div>")

    if not pipeline_logger.logs:
        st.html(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:12px;padding:48px 16px;text-align:center;">
            <div style="font-size:32px;margin-bottom:12px;">📝</div>
            <div style="font-size:14px;font-weight:600;color:{TEXT};">아직 실행된 로그가 없습니다</div>
        </div>
        """)
    else:
        for log in pipeline_logger.logs:
            with st.expander(f"[{log['time']}]  {log['model']} — {log['tokens']} tokens", expanded=False):
                st.markdown("**프롬프트**")
                st.code(log["prompt"], language="text")
                st.markdown("**응답**")
                st.code(log["response"], language="text")


# ══════════════════════════════════════════════════════════
# 스케줄 페이지
# ══════════════════════════════════════════════════════════
elif st.session_state.current_page == "schedule":
    page_header(page_titles["schedule"], "자동 실행 (Asia/Seoul)")

    DOW_LABELS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    FREQ_LABELS = {"hourly":"매시간","daily":"매일","weekly":"매주","monthly":"매월"}
    FMT_LABELS = {"pdf":"PDF","docx":"Word","md":"Markdown","none":"첨부 없음"}

    sched_running = sched_mod.is_running()
    all_scheds = sched_mod.list_schedules()
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.metric("등록", f"{len(all_scheds)}건")
    with mc2:
        active_n = sum(1 for s in all_scheds if s["enabled"])
        st.metric("활성", f"{active_n}건")
    with mc3:
        st.metric("스케줄러", "🟢 동작" if sched_running else "🔴 정지")

    st.html(f"<div style='height:1px;background:{BORDER};margin:18px 0 12px;'></div>")
    st.html(f"<div style='font-size:11px;font-weight:700;color:{SUB};text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;'>➕ 새 스케줄 등록</div>")

    with st.form("new_schedule_form", clear_on_submit=True):
        s_input = st.text_area("키워드 / 목적", placeholder="예: 오늘의 AI 뉴스 정리해줘", height=80)
        c1, c2 = st.columns(2)
        with c1:
            freq = st.selectbox("실행 주기", options=list(FREQ_LABELS.keys()),
                                format_func=lambda k: FREQ_LABELS[k])
        with c2:
            email_format = st.selectbox(
                "첨부 형식",
                options=["pdf", "docx", "md", "none"],
                format_func=lambda k: FMT_LABELS[k],
                index=0,
            )

        hour = None
        minute = 0
        dow = None
        day = None

        if freq == "hourly":
            minute = st.number_input("분 (매시 X분)", min_value=0, max_value=59, value=0, step=1)
        elif freq == "daily":
            tc1, tc2 = st.columns(2)
            with tc1:
                hour = st.number_input("시", min_value=0, max_value=23, value=9, step=1)
            with tc2:
                minute = st.number_input("분", min_value=0, max_value=59, value=0, step=1)
        elif freq == "weekly":
            wc1, wc2, wc3 = st.columns(3)
            with wc1:
                dow = st.selectbox("요일", options=list(range(7)),
                                   format_func=lambda i: DOW_LABELS[i])
            with wc2:
                hour = st.number_input("시", min_value=0, max_value=23, value=9, step=1, key="w_hour")
            with wc3:
                minute = st.number_input("분", min_value=0, max_value=59, value=0, step=1, key="w_min")
        elif freq == "monthly":
            mc1b, mc2b, mc3b = st.columns(3)
            with mc1b:
                day = st.number_input("일자", min_value=1, max_value=31, value=1, step=1)
            with mc2b:
                hour = st.number_input("시", min_value=0, max_value=23, value=9, step=1, key="m_hour")
            with mc3b:
                minute = st.number_input("분", min_value=0, max_value=59, value=0, step=1, key="m_min")

        send_email_s = st.checkbox("📧  이메일 자동 발송")
        submitted_s = st.form_submit_button("✅  스케줄 등록", use_container_width=True, type="primary")

    if submitted_s:
        if not s_input.strip():
            st.warning("입력 내용을 작성해주세요.")
        else:
            try:
                sid = sched_mod.add_schedule(
                    user_input=s_input.strip(),
                    frequency=freq,
                    hour=int(hour) if hour is not None else None,
                    minute=int(minute),
                    day_of_week=int(dow) if dow is not None else None,
                    day=int(day) if day is not None else None,
                    send_email=send_email_s,
                    email_format=email_format,
                )
                st.success(f"스케줄 #{sid} 등록 완료")
                st.rerun()
            except Exception as e:
                st.error(f"등록 실패: {e}")

    st.html(f"<div style='height:1px;background:{BORDER};margin:20px 0 12px;'></div>")
    st.html(f"<div style='font-size:11px;font-weight:700;color:{SUB};text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;'>📋 등록된 스케줄</div>")

    if not all_scheds:
        st.html(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:12px;padding:40px 16px;text-align:center;">
            <div style="font-size:28px;margin-bottom:10px;">⏰</div>
            <div style="font-size:13px;color:{TEXT};">등록된 스케줄이 없습니다</div>
        </div>
        """)
    else:
        for s in all_scheds:
            nxt = sched_mod.next_run_time(s)
            nxt_str = nxt.strftime("%Y-%m-%d %H:%M") if nxt else "—"

            if s["frequency"] == "hourly":
                cycle = f"매시간 {s['minute']:02d}분"
            elif s["frequency"] == "daily":
                cycle = f"매일 {s['hour']:02d}:{s['minute']:02d}"
            elif s["frequency"] == "weekly":
                dow_lbl = DOW_LABELS[s["day_of_week"]] if s["day_of_week"] is not None else "?"
                cycle = f"매주 {dow_lbl} {s['hour']:02d}:{s['minute']:02d}"
            elif s["frequency"] == "monthly":
                cycle = f"매월 {s['day']}일 {s['hour']:02d}:{s['minute']:02d}"
            else:
                cycle = s["frequency"]

            preview = (s["user_input"] or "")[:40]
            if len(s["user_input"] or "") > 40:
                preview += "…"

            badge_color = SUCCESS if s["enabled"] else "#666"
            badge_label = "활성" if s["enabled"] else "정지"

            last_run = s.get("last_run") or "—"
            last_status = s.get("last_status")
            if last_status == "success":
                last_badge = f"<span style='color:{SUCCESS};font-weight:600;'>✅ 성공</span>"
            elif last_status == "fail":
                last_badge = f"<span style='color:{FAIL};font-weight:600;'>❌ 실패</span>"
            else:
                last_badge = f"<span style='color:{HINT};'>—</span>"

            header = f"#{s['id']}  ·  {preview}  ·  {cycle}  ·  다음 {nxt_str}"
            with st.expander(header, expanded=False):
                st.html(f"""
                <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;">
                    <span style="font-size:11px;font-weight:600;padding:3px 9px;border-radius:999px;background:{badge_color}22;color:{badge_color};">{badge_label}</span>
                    <span style="font-size:11px;font-weight:600;padding:3px 9px;border-radius:999px;background:#f5f4ef;color:{TEXT};border:1px solid rgba(0,0,0,0.06);">첨부 {FMT_LABELS.get(s['email_format'] or 'none', '-')}</span>
                    <span style="font-size:11px;font-weight:600;padding:3px 9px;border-radius:999px;background:rgba(204,120,92,0.18);color:{ACCENT};">📧 {'발송' if s['send_email'] else '미발송'}</span>
                </div>
                <div style="font-size:12px;color:{SUB};line-height:1.7;">
                    <span style='color:{TEXT};'>입력:</span> {html_lib.escape(s['user_input'] or '')}<br>
                    <span style='color:{TEXT};'>다음 실행:</span> {nxt_str}<br>
                    <span style='color:{TEXT};'>마지막 실행:</span> {html_lib.escape(last_run)} · {last_badge}
                </div>
                """)
                bc1, bc2 = st.columns(2)
                with bc1:
                    toggle_label = "⏸  비활성화" if s["enabled"] else "▶  활성화"
                    if st.button(toggle_label, key=f"toggle_{s['id']}", use_container_width=True):
                        sched_mod.set_enabled(s["id"], not s["enabled"])
                        st.rerun()
                with bc2:
                    if st.button("🗑  삭제", key=f"del_{s['id']}", use_container_width=True):
                        sched_mod.delete_schedule(s["id"])
                        st.success(f"스케줄 #{s['id']} 삭제됨")
                        st.rerun()


# ══════════════════════════════════════════════════════════
# 히스토리 상세 페이지
# ══════════════════════════════════════════════════════════
elif st.session_state.current_page == "history_detail":
    page_header(page_titles["history_detail"], "")

    sid = st.session_state.selected_history_id
    detail = get_history(sid) if sid else None

    if not detail:
        st.info("선택된 히스토리가 없습니다. 사이드바에서 항목을 선택해주세요.")
    else:
        success = bool(detail.get("success"))
        badge_color = SUCCESS if success else FAIL
        badge_label = "✅ 성공" if success else "❌ 실패"
        created = (detail.get("created_at") or "").replace("T", " ")
        elapsed = detail.get("elapsed_sec")
        st.html(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:12px;padding:16px;margin-bottom:14px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
            <div>
              <div style="font-size:13px;font-weight:600;color:{TEXT};margin-bottom:4px;">{html_lib.escape((detail.get('user_input') or '')[:120])}</div>
              <div style="font-size:11px;color:{SUB};">{html_lib.escape(created)} · ⏱ {elapsed if elapsed is not None else '—'}s · 재시도 {detail.get('retry_count', 0)}회</div>
            </div>
            <span style="font-size:11px;font-weight:600;padding:4px 12px;border-radius:999px;background:{badge_color}22;color:{badge_color};">{badge_label}</span>
          </div>
        </div>
        """)

        tabs = st.tabs(["📄 최종 결과", "🔍 리서치", "💻 코드", "🐳 실행 결과", "⚠️ 에러 분석"])
        with tabs[0]:
            if detail.get("final_output"):
                st.markdown(detail["final_output"])
            else:
                st.caption("최종 결과 없음")
        with tabs[1]:
            if detail.get("research_result"):
                st.markdown(detail["research_result"])
            else:
                st.caption("리서치 결과 없음")
        with tabs[2]:
            if detail.get("code_result"):
                st.code(detail["code_result"], language="python")
            else:
                st.caption("코드 없음")
        with tabs[3]:
            exec_r = detail.get("execution_result")
            if exec_r and isinstance(exec_r, dict):
                if exec_r.get("success"):
                    st.success(f"실행 성공 · {exec_r.get('elapsed', 0)}s · {exec_r.get('lines', 0)}줄")
                    st.code(exec_r.get("output", ""), language="text")
                else:
                    st.error("실행 실패")
                    st.code(exec_r.get("error", ""), language="text")
            else:
                st.caption("실행 결과 없음")
        with tabs[4]:
            if detail.get("error_analysis"):
                st.markdown(detail["error_analysis"])
            else:
                st.caption("에러 분석 없음")

        # 다운로드
        if detail.get("final_output"):
            st.html(f"<div style='font-size:10px;font-weight:700;color:{SUB};text-transform:uppercase;letter-spacing:0.06em;margin:18px 0 8px;'>결과 다운로드</div>")
            try:
                pdf_bytes, docx_bytes = _build_history_files(
                    detail["id"],
                    detail.get("final_output", "") or "",
                    detail.get("code_result", "") or "",
                )
                fname_stem = f"aria_{detail['id']}_{(detail.get('created_at') or '').replace(':','').replace('-','').replace('T','_')}"
                d1, d2, d3 = st.columns(3)
                with d1:
                    st.download_button("📄  PDF", data=pdf_bytes, file_name=f"{fname_stem}.pdf",
                                       mime="application/pdf", use_container_width=True,
                                       key=f"dl_pdf_{detail['id']}")
                with d2:
                    st.download_button("📝  Word", data=docx_bytes, file_name=f"{fname_stem}.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       use_container_width=True, key=f"dl_docx_{detail['id']}")
                with d3:
                    st.download_button("📋  Markdown",
                                       data=(detail.get("final_output") or "").encode("utf-8"),
                                       file_name=f"{fname_stem}.md", mime="text/markdown",
                                       use_container_width=True, key=f"dl_md_{detail['id']}")
            except Exception as e:
                st.error(f"파일 생성 실패: {e}")

        st.html("<div style='height:14px;'></div>")
        col_back, col_clear = st.columns(2)
        with col_back:
            if st.button("✚  새 대화", use_container_width=True):
                reset_run_state()
                st.session_state.current_page = "run"
                st.rerun()
        with col_clear:
            if st.button("🗑  히스토리 전체 삭제", use_container_width=True):
                clear_history()
                st.session_state.selected_history_id = None
                st.session_state.current_page = "run"
                st.rerun()

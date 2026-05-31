"""Central Reflex State for ARIA.

Mirrors the old Streamlit `st.session_state` shape and wraps the langgraph
phase1/phase2 streams in background event handlers so the UI can update
mid-run without page reruns.
"""

from __future__ import annotations

import asyncio
import queue
import threading
import time
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Optional

import reflex as rx

# Reflex 0.9 removed the `rx.Base` shortcut; the class lives at
# `reflex.base.Base` (older versions) or `reflex_base.base.Base`. Use whichever
# import works, with a pydantic fallback as a last resort.
try:
    from reflex.base import Base as _RxBase  # type: ignore
except ImportError:  # pragma: no cover
    try:
        from reflex_base.base import Base as _RxBase  # type: ignore
    except ImportError:  # pragma: no cover
        try:
            _RxBase = rx.Base  # type: ignore[attr-defined]
        except AttributeError:
            from pydantic import BaseModel as _RxBase  # type: ignore

# These imports resolve because aria_app/__init__.py prepends ../../src.
from agents.output_agent import export_to_docx, export_to_pdf
from utils import project_manager as pm
from utils import scheduler as sched_mod
from utils.history import (
    clear_history,
    get_history,
    list_history,
    list_schedule_runs,
)
from utils.logger import pipeline_logger
from workflows.graph import build_phase1_graph, build_phase2_graph


ALL_STEPS: list[tuple[str, str]] = [
    ("research", "Research"),
    ("code_decision", "Decision"),
    ("code_generation", "Generate"),
    ("code_review", "Review"),
    ("human_review", "Edit"),
    ("execution", "Execute"),
    ("error_analysis", "Analyze"),
    ("output", "Output"),
    ("email", "Email"),
]

EXAMPLES: list[str] = [
    "파이썬으로 정렬 알고리즘 구현해줘",
    "FastAPI REST API 만들어줘",
    "다익스트라 알고리즘 설명해줘",
    "비트코인 최근 1주일 동향 정리",
]

PHASE_LABELS = {
    "idle": "대기 중",
    "running_phase1": "Phase 1 실행 중",
    "phase1_done": "사용자 검토 대기",
    "running_phase2": "Phase 2 실행 중",
    "phase2_done": "완료",
}

DOW_LABELS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
FREQ_LABELS = {"hourly": "매시간", "daily": "매일", "weekly": "매주", "monthly": "매월"}
FMT_LABELS = {"pdf": "PDF", "docx": "Word", "md": "Markdown", "none": "첨부 없음"}


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


# ── Typed view models for nested foreach (Reflex 0.9+) ─────
# Reflex 0.9 disallows passing an iter-var (e.g. `grp.items`) to a nested
# `rx.foreach`. So we flatten the sidebar history into a single list where
# each entry is either a header ("kind=header") or a clickable item.
class HistoryFlatEntry(_RxBase):
    kind: str = "item"  # "header" | "item"
    group_label: str = ""
    id: int = 0
    preview: str = ""
    dot: str = ""


class AgentLogView(_RxBase):
    agent: str = ""
    action: str = ""
    content: str = ""


class ScheduleRowView(_RxBase):
    id: int = 0
    enabled: bool = False
    cycle: str = ""
    preview: str = ""
    email_format: str = "-"
    send_email: bool = False


class ScheduleRunView(_RxBase):
    """스케줄러 자동 실행 1건의 표시용 모델."""

    history_id: int = 0
    schedule_id: int = 0
    created_at: str = ""
    preview: str = ""
    success: bool = False
    elapsed: int = 0
    retry: int = 0


class LlmLogView(_RxBase):
    time: str = ""
    model: str = ""
    tokens: int = 0
    prompt: str = ""
    response: str = ""


class PipelineStepView(_RxBase):
    key: str = ""
    label: str = ""
    status: str = "idle"


# ── 프로젝트 ───────────────────────────────────────────────
PROJECT_STATUS_LABELS = {
    "active": "진행중",
    "completed": "완료",
    "paused": "중단",
}


class ProjectView(_RxBase):
    id: int = 0
    name: str = ""
    description: str = ""
    status: str = "active"
    status_label: str = "진행중"
    session_count: int = 0
    last_at: str = "—"
    is_selected: bool = False


class SessionView(_RxBase):
    id: int = 0
    session_number: int = 0
    preview: str = ""
    created_at: str = ""
    success: bool = False
    final_output: str = ""
    research_result: str = ""
    code_result: str = ""
    error_analysis: str = ""
    has_exec: bool = False
    exec_ok: bool = False
    exec_output: str = ""
    exec_error: str = ""
    exec_elapsed: int = 0
    exec_lines: int = 0


class AriaState(rx.State):
    # ── session / phase ────────────────────────────────────
    session_id: str = ""
    phase: str = "idle"

    # ── inputs ─────────────────────────────────────────────
    user_input: str = ""
    pending_input: str = ""
    send_email: bool = False
    email_format: str = "pdf"

    # ── live + final result blobs ──────────────────────────
    phase1_result: dict = {}
    result: dict = {}

    live_research: str = ""
    live_code: str = ""
    live_exec_ok: bool = False
    live_exec_output: str = ""
    live_exec_error: str = ""
    live_exec_elapsed: int = 0
    live_exec_lines: int = 0
    live_exec_has: bool = False
    live_error_analysis: str = ""
    live_retry: int = 0

    # HITL
    edited_code: str = ""

    # pipeline status: node_name -> "idle" | "running" | "done"
    step_status: dict[str, str] = {}

    # monitoring log
    agent_logs: list[AgentLogView] = []

    # LLM call log — mirrored from utils.logger.pipeline_logger so that
    # Reflex can detect changes (computed vars can't observe external
    # globals, so the log page would otherwise never refresh).
    llm_logs_data: list[dict] = []
    token_usage_data: dict[str, int] = {"school_api": 0, "gemini": 0}

    # timing
    start_time: float = 0.0
    elapsed: int = 0

    # error
    last_error: str = ""

    # ── history ───────────────────────────────────────────
    history_items: list[dict] = []
    history_detail: dict = {}

    # ── schedule list + form ──────────────────────────────
    schedule_items: list[dict] = []
    schedule_runs_data: list[dict] = []
    scheduler_running: bool = False

    s_input: str = ""
    s_frequency: str = "daily"
    s_hour: int = 9
    s_minute: int = 0
    s_day_of_week: int = 0
    s_day: int = 1
    s_send_email: bool = False
    s_email_format: str = "pdf"
    s_flash: str = ""

    # ── projects ──────────────────────────────────────────
    selected_project_id: int = 0           # 0 = 선택 안 함
    selected_project_detail_id: int = 0    # 상세 페이지에서 보고 있는 프로젝트
    projects_data: list[dict] = []         # 전체 프로젝트 raw
    project_sessions_data: list[dict] = []  # 상세 페이지의 세션 raw
    selected_project_detail_data: dict = {}

    # 새 프로젝트 폼
    p_name: str = ""
    p_description: str = ""

    # ── computed ──────────────────────────────────────────
    @rx.var
    def phase_label(self) -> str:
        return PHASE_LABELS.get(self.phase, "")

    @rx.var
    def is_idle(self) -> bool:
        return self.phase == "idle"

    @rx.var
    def is_running_phase1(self) -> bool:
        return self.phase == "running_phase1"

    @rx.var
    def is_phase1_done(self) -> bool:
        return self.phase == "phase1_done"

    @rx.var
    def is_running_phase2(self) -> bool:
        return self.phase == "running_phase2"

    @rx.var
    def is_phase2_done(self) -> bool:
        return self.phase == "phase2_done"

    @rx.var
    def has_code_for_review(self) -> bool:
        return bool((self.phase1_result or {}).get("code_result"))

    @rx.var
    def has_research_for_review(self) -> bool:
        return bool((self.phase1_result or {}).get("research_result"))

    @rx.var
    def phase1_research_text(self) -> str:
        return ((self.phase1_result or {}).get("research_result") or "")

    @rx.var
    def phase1_code_text(self) -> str:
        return ((self.phase1_result or {}).get("code_result") or "")

    # History detail safe getters
    @rx.var
    def hd_user_input(self) -> str:
        return ((self.history_detail or {}).get("user_input") or "")[:120]

    @rx.var
    def hd_created_at(self) -> str:
        return ((self.history_detail or {}).get("created_at") or "").replace("T", " ")

    @rx.var
    def hd_elapsed(self) -> str:
        v = (self.history_detail or {}).get("elapsed_sec")
        return f"{v}" if v is not None else "—"

    @rx.var
    def hd_retry(self) -> int:
        return int((self.history_detail or {}).get("retry_count") or 0)

    @rx.var
    def hd_success(self) -> bool:
        return bool((self.history_detail or {}).get("success"))

    @rx.var
    def hd_final_output(self) -> str:
        return (self.history_detail or {}).get("final_output") or ""

    @rx.var
    def hd_research(self) -> str:
        return (self.history_detail or {}).get("research_result") or ""

    @rx.var
    def hd_code(self) -> str:
        return (self.history_detail or {}).get("code_result") or ""

    @rx.var
    def hd_error_analysis(self) -> str:
        return (self.history_detail or {}).get("error_analysis") or ""

    @rx.var
    def hd_exec_ok(self) -> bool:
        exec_r = (self.history_detail or {}).get("execution_result") or {}
        return bool(exec_r.get("success"))

    @rx.var
    def hd_exec_output(self) -> str:
        exec_r = (self.history_detail or {}).get("execution_result") or {}
        return exec_r.get("output", "") or ""

    @rx.var
    def hd_exec_error(self) -> str:
        exec_r = (self.history_detail or {}).get("execution_result") or {}
        return exec_r.get("error", "") or ""

    @rx.var
    def hd_exists(self) -> bool:
        return bool(self.history_detail)

    # Schedule row formatting
    @rx.var
    def schedule_rows(self) -> list[ScheduleRowView]:
        rows: list[ScheduleRowView] = []
        for s in self.schedule_items:
            freq = s.get("frequency")
            mn = s.get("minute") or 0
            hr = s.get("hour")
            if freq == "hourly":
                cycle = f"매시간 {mn:02d}분"
            elif freq == "daily":
                cycle = f"매일 {hr:02d}:{mn:02d}"
            elif freq == "weekly":
                dow = s.get("day_of_week")
                dow_lbl = DOW_LABELS[dow] if dow is not None and 0 <= dow < 7 else "?"
                cycle = f"매주 {dow_lbl} {hr:02d}:{mn:02d}"
            elif freq == "monthly":
                cycle = f"매월 {s.get('day')}일 {hr:02d}:{mn:02d}"
            else:
                cycle = str(freq)
            preview = (s.get("user_input") or "")[:50]
            rows.append(
                ScheduleRowView(
                    id=int(s["id"]),
                    enabled=bool(s.get("enabled")),
                    cycle=cycle,
                    preview=preview,
                    email_format=FMT_LABELS.get(s.get("email_format") or "none", "-"),
                    send_email=bool(s.get("send_email")),
                )
            )
        return rows

    @rx.var
    def final_output_text(self) -> str:
        return (self.result.get("final_output") or "") if self.result else ""

    @rx.var
    def final_code_text(self) -> str:
        return (self.result.get("code_result") or "") if self.result else ""

    @rx.var
    def final_research_text(self) -> str:
        return (self.result.get("research_result") or "") if self.result else ""

    @rx.var
    def final_error_analysis(self) -> str:
        return (self.result.get("error_analysis") or "") if self.result else ""

    @rx.var
    def final_retry_count(self) -> int:
        return int(self.result.get("retry_count") or 0) if self.result else 0

    @rx.var
    def final_exec_ok(self) -> bool:
        exec_r = (self.result or {}).get("execution_result")
        return bool(exec_r and exec_r.get("success"))

    @rx.var
    def final_exec_fail(self) -> bool:
        exec_r = (self.result or {}).get("execution_result")
        return bool(exec_r and not exec_r.get("success"))

    @rx.var
    def final_exec_output(self) -> str:
        exec_r = (self.result or {}).get("execution_result") or {}
        return exec_r.get("output", "") or ""

    @rx.var
    def final_exec_error(self) -> str:
        exec_r = (self.result or {}).get("execution_result") or {}
        return (exec_r.get("error", "") or "")[:400]

    @rx.var
    def final_exec_elapsed(self) -> int:
        exec_r = (self.result or {}).get("execution_result") or {}
        return int(exec_r.get("elapsed") or 0)

    @rx.var
    def final_exec_lines(self) -> int:
        exec_r = (self.result or {}).get("execution_result") or {}
        return int(exec_r.get("lines") or 0)

    @rx.var
    def short_session_id(self) -> str:
        return (self.session_id[:22] + "…") if self.session_id else ""

    @rx.var
    def token_count(self) -> int:
        try:
            return int(self.token_usage_data.get("school_api", 0))
        except Exception:
            return 0

    @rx.var
    def history_flat(self) -> list[HistoryFlatEntry]:
        """Flat list of header + item entries, ordered by recency group."""
        groups: dict[str, list[HistoryFlatEntry]] = {}
        for item in self.history_items:
            g = _date_group(item.get("created_at", "") or "")
            preview = (item.get("user_input") or "").strip()
            preview = (preview[:25] + ("…" if len(preview) > 25 else "")) or "(빈 입력)"
            groups.setdefault(g, []).append(
                HistoryFlatEntry(
                    kind="item",
                    id=int(item["id"]),
                    preview=preview,
                    dot=("🟢" if item.get("success") else "🔴"),
                )
            )
        order = ["오늘", "어제", "이번 주", "이번 달", "이전"]
        out: list[HistoryFlatEntry] = []
        for g in order:
            if g not in groups:
                continue
            out.append(HistoryFlatEntry(kind="header", group_label=g))
            out.extend(groups[g])
        return out

    @rx.var
    def schedule_count_total(self) -> int:
        return len(self.schedule_items)

    @rx.var
    def schedule_count_active(self) -> int:
        return sum(1 for s in self.schedule_items if s.get("enabled"))

    @rx.var
    def scheduler_status_label(self) -> str:
        return "🟢 동작" if self.scheduler_running else "🔴 정지"

    @rx.var
    def schedule_runs_view(self) -> list[ScheduleRunView]:
        out: list[ScheduleRunView] = []
        for r in self.schedule_runs_data:
            preview = (r.get("user_input") or "").strip()
            preview = preview[:60] + ("…" if len(preview) > 60 else "")
            out.append(
                ScheduleRunView(
                    history_id=int(r.get("id") or 0),
                    schedule_id=int(r.get("schedule_id") or 0),
                    created_at=(r.get("created_at") or "").replace("T", " "),
                    preview=preview or "(빈 입력)",
                    success=bool(r.get("success")),
                    elapsed=int(r.get("elapsed_sec") or 0),
                    retry=int(r.get("retry_count") or 0),
                )
            )
        return out

    @rx.var
    def has_schedule_runs(self) -> bool:
        return len(self.schedule_runs_data) > 0

    @rx.var
    def pipeline_steps(self) -> list[PipelineStepView]:
        return [
            PipelineStepView(key=key, label=label, status=self.step_status.get(key, "idle"))
            for key, label in ALL_STEPS
        ]

    @rx.var
    def llm_log_total(self) -> int:
        return len(self.llm_logs_data)

    @rx.var
    def llm_log_local(self) -> int:
        return len([l for l in self.llm_logs_data if "gpt" not in (l.get("model") or "")])

    # ── project computed ─────────────────────────────────
    @rx.var
    def has_selected_project(self) -> bool:
        return bool(self.selected_project_id)

    @rx.var
    def selected_project_name(self) -> str:
        pid = self.selected_project_id
        if not pid:
            return ""
        for p in self.projects_data:
            if int(p.get("id") or 0) == int(pid):
                return str(p.get("name") or "")
        return ""

    @rx.var
    def selected_project_status_label(self) -> str:
        pid = self.selected_project_id
        if not pid:
            return ""
        for p in self.projects_data:
            if int(p.get("id") or 0) == int(pid):
                return PROJECT_STATUS_LABELS.get(p.get("status") or "active", "진행중")
        return "진행중"

    @rx.var
    def selected_project_next_n(self) -> int:
        pid = self.selected_project_id
        if not pid:
            return 1
        for p in self.projects_data:
            if int(p.get("id") or 0) == int(pid):
                return int(p.get("session_count") or 0) + 1
        return 1

    @rx.var
    def selected_project_last_input(self) -> str:
        pid = self.selected_project_id
        if not pid:
            return ""
        try:
            latest = pm.get_latest_session(int(pid)) or {}
            inp = (latest.get("user_input") or "").strip()
            if len(inp) > 40:
                inp = inp[:40] + "…"
            return inp or "—"
        except Exception:
            return "—"

    @rx.var
    def projects_view(self) -> list[ProjectView]:
        out: list[ProjectView] = []
        for p in self.projects_data:
            pid = int(p.get("id") or 0)
            last_at = (p.get("last_session_at") or p.get("updated_at") or "") or "—"
            if last_at and last_at != "—":
                last_at = last_at.replace("T", " ")[:16]
            out.append(
                ProjectView(
                    id=pid,
                    name=str(p.get("name") or ""),
                    description=str(p.get("description") or ""),
                    status=str(p.get("status") or "active"),
                    status_label=PROJECT_STATUS_LABELS.get(p.get("status") or "active", "진행중"),
                    session_count=int(p.get("session_count") or 0),
                    last_at=last_at,
                    is_selected=(pid == int(self.selected_project_id or 0)),
                )
            )
        return out

    @rx.var
    def has_projects(self) -> bool:
        return len(self.projects_data) > 0

    @rx.var
    def project_detail_name(self) -> str:
        return str((self.selected_project_detail_data or {}).get("name") or "")

    @rx.var
    def project_detail_description(self) -> str:
        return str((self.selected_project_detail_data or {}).get("description") or "—")

    @rx.var
    def project_detail_status(self) -> str:
        return str((self.selected_project_detail_data or {}).get("status") or "active")

    @rx.var
    def project_detail_status_label(self) -> str:
        return PROJECT_STATUS_LABELS.get(
            (self.selected_project_detail_data or {}).get("status") or "active",
            "진행중",
        )

    @rx.var
    def project_detail_created(self) -> str:
        return str((self.selected_project_detail_data or {}).get("created_at") or "").replace("T", " ")[:16]

    @rx.var
    def project_detail_updated(self) -> str:
        return str((self.selected_project_detail_data or {}).get("updated_at") or "").replace("T", " ")[:16]

    @rx.var
    def project_detail_exists(self) -> bool:
        return bool(self.selected_project_detail_data)

    @rx.var
    def sessions_view(self) -> list[SessionView]:
        out: list[SessionView] = []
        for s in self.project_sessions_data:
            preview = (s.get("user_input") or "").strip()
            preview_short = preview[:60] + ("…" if len(preview) > 60 else "")
            if not preview_short:
                preview_short = "(빈 입력)"
            exec_r = s.get("execution_result") or {}
            if isinstance(exec_r, dict):
                has_exec = bool(exec_r)
                exec_ok = bool(exec_r.get("success"))
                exec_output = str(exec_r.get("output") or "")
                exec_error = str(exec_r.get("error") or "")
                exec_elapsed = int(exec_r.get("elapsed") or 0)
                exec_lines = int(exec_r.get("lines") or 0)
            else:
                has_exec = False
                exec_ok = False
                exec_output = ""
                exec_error = ""
                exec_elapsed = 0
                exec_lines = 0
            out.append(
                SessionView(
                    id=int(s.get("id") or 0),
                    session_number=int(s.get("session_number") or 0),
                    preview=preview_short,
                    created_at=str(s.get("created_at") or "").replace("T", " ")[:16],
                    success=bool(s.get("success")),
                    final_output=str(s.get("final_output") or ""),
                    research_result=str(s.get("research_result") or ""),
                    code_result=str(s.get("code_result") or ""),
                    error_analysis=str(s.get("error_analysis") or ""),
                    has_exec=has_exec,
                    exec_ok=exec_ok,
                    exec_output=exec_output,
                    exec_error=exec_error,
                    exec_elapsed=exec_elapsed,
                    exec_lines=exec_lines,
                )
            )
        return out

    @rx.var
    def has_sessions(self) -> bool:
        return len(self.project_sessions_data) > 0

    @rx.var
    def llm_logs(self) -> list[LlmLogView]:
        out: list[LlmLogView] = []
        for l in self.llm_logs_data:
            out.append(
                LlmLogView(
                    time=str(l.get("time", "")),
                    model=str(l.get("model", "")),
                    tokens=int(l.get("tokens") or 0),
                    prompt=str(l.get("prompt", "")),
                    response=str(l.get("response", "")),
                )
            )
        return out

    # ── lifecycle ─────────────────────────────────────────
    def on_load(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        self._refresh_history()
        self._refresh_schedule()
        self._refresh_projects()

    def load_project_detail(self):
        pid_raw = self.router.page.params.get("pid", "")
        try:
            pid = int(pid_raw)
        except Exception:
            self.selected_project_detail_id = 0
            self.selected_project_detail_data = {}
            self.project_sessions_data = []
            return
        self.selected_project_detail_id = pid
        self._refresh_project_detail()

    def load_history_detail(self):
        hid_raw = self.router.page.params.get("hid", "")
        try:
            hid = int(hid_raw)
        except Exception:
            self.history_detail = {}
            return
        detail = get_history(hid) or {}
        self.history_detail = dict(detail) if detail else {}

    # ── small helpers ─────────────────────────────────────
    def _add_log(self, agent: str, action: str, content: str = ""):
        self.agent_logs = self.agent_logs + [
            AgentLogView(
                agent=agent,
                action=action,
                content=(content[:300] if content else ""),
            )
        ]

    def _set_step(self, key: str, status: str):
        new = dict(self.step_status)
        new[key] = status
        self.step_status = new

    def _sync_pipeline_logger(self):
        try:
            self.llm_logs_data = [dict(l) for l in pipeline_logger.logs]
            self.token_usage_data = dict(pipeline_logger.token_usage)
        except Exception:
            pass

    def _refresh_history(self):
        try:
            items = list_history(limit=50) or []
            self.history_items = [dict(x) for x in items]
        except Exception:
            self.history_items = []

    def _refresh_schedule(self):
        try:
            self.schedule_items = [dict(x) for x in sched_mod.list_schedules()]
            self.scheduler_running = bool(sched_mod.is_running())
        except Exception:
            self.schedule_items = []
            self.scheduler_running = False
        self._refresh_schedule_runs()

    def _refresh_schedule_runs(self):
        try:
            self.schedule_runs_data = [dict(x) for x in list_schedule_runs(limit=50)]
        except Exception:
            self.schedule_runs_data = []

    def _refresh_projects(self):
        try:
            self.projects_data = [dict(x) for x in pm.get_projects()]
        except Exception:
            self.projects_data = []

    def _refresh_project_detail(self):
        pid = int(self.selected_project_detail_id or 0)
        if not pid:
            self.selected_project_detail_data = {}
            self.project_sessions_data = []
            return
        try:
            proj = pm.get_project(pid)
            self.selected_project_detail_data = dict(proj) if proj else {}
            full_sessions: list[dict] = []
            for s in pm.get_sessions(pid):
                detail = pm.get_session(int(s["id"])) or {}
                full_sessions.append(dict(detail))
            self.project_sessions_data = full_sessions
        except Exception:
            self.selected_project_detail_data = {}
            self.project_sessions_data = []

    # ── reset / nav ───────────────────────────────────────
    def reset_run_state(self, prefill: str = ""):
        self.session_id = str(uuid.uuid4())
        self.phase = "idle"
        self.phase1_result = {}
        self.result = {}
        self.agent_logs = []
        self.step_status = {}
        self.user_input = prefill
        self.pending_input = prefill
        self.start_time = 0.0
        self.elapsed = 0
        self.last_error = ""
        self.live_research = ""
        self.live_code = ""
        self.live_exec_ok = False
        self.live_exec_output = ""
        self.live_exec_error = ""
        self.live_exec_elapsed = 0
        self.live_exec_lines = 0
        self.live_exec_has = False
        self.live_error_analysis = ""
        self.live_retry = 0
        self.edited_code = ""
        self.llm_logs_data = []
        self.token_usage_data = {"school_api": 0, "gemini": 0}

    def use_example(self, ex: str):
        self.pending_input = ex

    def new_chat(self):
        self.reset_run_state()
        return rx.redirect("/")

    # ── project actions ──────────────────────────────────
    def set_p_name(self, v: str):
        self.p_name = v

    def set_p_description(self, v: str):
        self.p_description = v

    def submit_project(self):
        name = (self.p_name or "").strip()
        if not name:
            return rx.toast.warning("프로젝트 이름을 입력해주세요.")
        try:
            new_id = pm.create_project(name, (self.p_description or "").strip())
        except Exception as e:
            return rx.toast.error(f"생성 실패: {e}")
        self.p_name = ""
        self.p_description = ""
        self.selected_project_id = int(new_id)
        self._refresh_projects()
        return rx.toast.success(f"프로젝트 #{new_id} '{name}' 생성 완료")

    def select_project(self, pid: int):
        self.selected_project_id = int(pid)
        self._refresh_projects()
        self.reset_run_state()
        self.selected_project_id = int(pid)  # reset 후 다시 세팅
        return rx.redirect("/")

    def clear_project(self):
        self.selected_project_id = 0

    def view_project(self, pid: int):
        self.selected_project_detail_id = int(pid)
        return rx.redirect(f"/project/{int(pid)}")

    def delete_project(self, pid: int):
        try:
            pm.delete_project(int(pid))
        except Exception as e:
            return rx.toast.error(f"삭제 실패: {e}")
        if int(self.selected_project_id or 0) == int(pid):
            self.selected_project_id = 0
        self._refresh_projects()
        return rx.toast.success(f"프로젝트 #{pid} 삭제됨")

    def toggle_project_completed(self, pid: int):
        try:
            proj = pm.get_project(int(pid)) or {}
            new_status = "completed" if proj.get("status") != "completed" else "active"
            pm.update_project_status(int(pid), new_status)
        except Exception as e:
            return rx.toast.error(f"상태 변경 실패: {e}")
        self._refresh_projects()
        self._refresh_project_detail()

    def toggle_project_paused(self, pid: int):
        try:
            proj = pm.get_project(int(pid)) or {}
            new_status = "active" if proj.get("status") == "paused" else "paused"
            pm.update_project_status(int(pid), new_status)
        except Exception as e:
            return rx.toast.error(f"상태 변경 실패: {e}")
        self._refresh_projects()
        self._refresh_project_detail()

    def continue_project_from_detail(self):
        pid = int(self.selected_project_detail_id or 0)
        if not pid:
            return
        self.selected_project_id = pid
        self.reset_run_state()
        self.selected_project_id = pid
        return rx.redirect("/")

    # ── input form (run page) ─────────────────────────────
    def set_pending_input(self, v: str):
        self.pending_input = v

    def set_send_email(self, v: bool):
        self.send_email = v

    def set_email_format(self, v: str):
        self.email_format = v

    @rx.event(background=True)
    async def submit_input(self):
        """Validate input, reset state, then immediately stream phase 1.

        Merged into a single background event because Reflex 0.9+ does not
        reliably chain a background event from a return value of a normal
        event handler.
        """
        async with self:
            text = (self.pending_input or "").strip()
            if not text:
                return rx.toast.warning("입력 내용을 작성해주세요.")
            try:
                pipeline_logger.reset()
            except Exception:
                pass
            # inline reset (avoid calling reset_run_state which may not see
            # mutations correctly across the lock boundary in some versions).
            self.session_id = str(uuid.uuid4())
            self.phase1_result = {}
            self.result = {}
            self.agent_logs = []
            self.step_status = {}
            self.last_error = ""
            self.live_research = ""
            self.live_code = ""
            self.live_exec_ok = False
            self.live_exec_output = ""
            self.live_exec_error = ""
            self.live_exec_elapsed = 0
            self.live_exec_lines = 0
            self.live_exec_has = False
            self.live_error_analysis = ""
            self.live_retry = 0
            self.edited_code = ""
            self.llm_logs_data = []
            self.token_usage_data = {"school_api": 0, "gemini": 0}
            self.user_input = text
            self.phase = "running_phase1"
            self.start_time = time.time()
            self.elapsed = 0
            session_id = self.session_id
            send_email = self.send_email
            email_format = self.email_format
            start_time = self.start_time
            project_id = int(self.selected_project_id or 0)

        await self._stream_phase1(text, session_id, send_email, email_format, start_time, project_id)

    async def _stream_phase1(
        self,
        text: str,
        session_id: str,
        send_email: bool,
        email_format: str,
        start_time: float,
        project_id: int = 0,
    ):
        # 프로젝트 컨텍스트 (이전 코드/리서치) 조회
        prev_code: Optional[str] = None
        prev_context: Optional[str] = None
        session_number = 1
        if project_id:
            try:
                ctx = pm.get_project_context(project_id) or {}
                prev_code = ctx.get("previous_code")
                prev_context = ctx.get("previous_context")
                session_number = int(ctx.get("session_number") or 1)
            except Exception:
                pass

        initial_state = {
            "user_input": text,
            "send_email": send_email,
            "email_format": email_format,
            "research_result": None,
            "code_result": None,
            "execution_result": None,
            "final_output": None,
            "error": None,
            "error_analysis": None,
            "retry_count": 0,
            "needs_code": None,
            "edited_code": None,
            "start_time": start_time,
            "project_id": project_id if project_id else None,
            "previous_code": prev_code,
            "previous_context": prev_context,
            "session_number": session_number,
            # 수동 실행 — 사이드바 히스토리에 노출
            "schedule_id": None,
        }
        config = {"configurable": {"thread_id": session_id}}

        q: queue.Queue = queue.Queue()

        def producer():
            try:
                graph = build_phase1_graph()
                for ev in graph.stream(initial_state, config=config):
                    q.put(("event", ev))
            except Exception as e:
                q.put(("error", str(e)))
            finally:
                q.put(("done", None))

        threading.Thread(target=producer, daemon=True).start()
        last_state: Optional[dict] = None

        while True:
            kind, payload = await asyncio.to_thread(q.get)
            if kind == "done":
                break
            if kind == "error":
                async with self:
                    self.phase = "idle"
                    self.last_error = str(payload)
                return
            for node_name, node_state in (payload or {}).items():
                last_state = node_state
                async with self:
                    self._set_step(node_name, "done")
                    if node_name == "research":
                        res = (node_state or {}).get("research_result", "") or ""
                        self._add_log("Research Agent", "웹 검색 완료", res)
                        self.live_research = res
                    elif node_name == "code_decision":
                        self._add_log(
                            "Code Decision",
                            f"코드 필요: {(node_state or {}).get('needs_code', False)}",
                        )
                    elif node_name == "code_generation":
                        code = (node_state or {}).get("code_result", "") or ""
                        self._add_log("Code Generation", "코드 생성 완료", code)
                        self.live_code = code
                    elif node_name == "code_review":
                        self._add_log("Code Review", "코드 리뷰 완료")
                    elif node_name == "output":
                        self._add_log("Output Agent", "결과 정리 완료")
                    self.phase1_result = dict(node_state or {})
                    self._sync_pipeline_logger()

        async with self:
            if self.start_time:
                self.elapsed = int(time.time() - self.start_time)
            self._sync_pipeline_logger()
            ls = last_state or {}
            if ls.get("final_output") and not ls.get("code_result"):
                self.result = ls
                self.phase = "phase2_done"
                self._refresh_history()
                self._refresh_projects()
            else:
                self.phase = "phase1_done"
                self.edited_code = ls.get("code_result", "") or ""

    # ── HITL ──────────────────────────────────────────────
    def set_edited_code(self, v: str):
        self.edited_code = v

    @rx.event(background=True)
    async def approve_code(self):
        """Apply HITL edits then stream phase 2 inline (background event)."""
        async with self:
            new_result = dict(self.phase1_result)
            new_result["code_result"] = self.edited_code
            new_result["edited_code"] = None
            self.phase1_result = new_result
            self.phase = "running_phase2"
            state_snapshot = dict(new_result)
            session_id = self.session_id

        await self._stream_phase2(state_snapshot, session_id)

    def restore_original_code(self):
        self.edited_code = self.phase1_result.get("code_result", "") or ""

    def reject_code(self):
        self.reset_run_state()

    # ── background streaming impls ────────────────────────
    async def _stream_phase2(self, state: dict, session_id: str):
        config = {"configurable": {"thread_id": session_id}}

        q: queue.Queue = queue.Queue()

        def producer():
            try:
                graph = build_phase2_graph()
                for ev in graph.stream(state, config=config):
                    q.put(("event", ev))
            except Exception as e:
                q.put(("error", str(e)))
            finally:
                q.put(("done", None))

        threading.Thread(target=producer, daemon=True).start()
        final_state: Optional[dict] = None

        while True:
            kind, payload = await asyncio.to_thread(q.get)
            if kind == "done":
                break
            if kind == "error":
                async with self:
                    self.phase = "idle"
                    self.last_error = str(payload)
                return
            for node_name, node_state in (payload or {}).items():
                final_state = node_state
                async with self:
                    self._set_step(node_name, "done")
                    if node_name == "execution":
                        exec_r = (node_state or {}).get("execution_result") or {}
                        self._add_log("Execution", "실행 완료", str(exec_r))
                        self.live_exec_has = bool(exec_r)
                        self.live_exec_ok = bool(exec_r.get("success"))
                        self.live_exec_output = exec_r.get("output", "") or ""
                        self.live_exec_error = (exec_r.get("error", "") or "")[:400]
                        self.live_exec_elapsed = int(exec_r.get("elapsed") or 0)
                        self.live_exec_lines = int(exec_r.get("lines") or 0)
                    elif node_name == "error_analysis":
                        retry = int((node_state or {}).get("retry_count") or 0)
                        analysis = (node_state or {}).get("error_analysis", "") or ""
                        self._add_log("Error Analysis", f"에러 분석 {retry}/3", analysis)
                        self.live_error_analysis = analysis
                        self.live_retry = retry
                    elif node_name == "output":
                        self._add_log("Output Agent", "결과 정리 완료")
                    self._sync_pipeline_logger()

        async with self:
            if self.start_time:
                self.elapsed = int(time.time() - self.start_time)
            self.result = dict(final_state or {})
            self.phase = "phase2_done"
            self._sync_pipeline_logger()
            self._refresh_history()
            self._refresh_projects()

    # ── downloads ─────────────────────────────────────────
    def download_pdf(self):
        text = (self.result or {}).get("final_output") or ""
        code = (self.result or {}).get("code_result") or ""
        if not text:
            return rx.toast.warning("내려받을 결과가 없습니다.")
        try:
            data = export_to_pdf(text, code)
            return rx.download(data=data, filename="aria_result.pdf")
        except Exception as e:
            return rx.toast.error(f"PDF 생성 실패: {e}")

    def download_docx(self):
        text = (self.result or {}).get("final_output") or ""
        code = (self.result or {}).get("code_result") or ""
        if not text:
            return rx.toast.warning("내려받을 결과가 없습니다.")
        try:
            data = export_to_docx(text, code)
            return rx.download(data=data, filename="aria_result.docx")
        except Exception as e:
            return rx.toast.error(f"Word 생성 실패: {e}")

    def download_md(self):
        text = (self.result or {}).get("final_output") or ""
        if not text:
            return rx.toast.warning("내려받을 결과가 없습니다.")
        return rx.download(data=text.encode("utf-8"), filename="aria_result.md")

    # ── history page actions ──────────────────────────────
    def open_history(self, hid: int):
        return rx.redirect(f"/history/{hid}")

    def clear_history_all(self):
        try:
            clear_history()
        except Exception as e:
            return rx.toast.error(f"삭제 실패: {e}")
        self.history_items = []
        self.history_detail = {}
        return rx.redirect("/")

    def download_history_pdf(self):
        d = self.history_detail or {}
        text = d.get("final_output") or ""
        code = d.get("code_result") or ""
        if not text:
            return rx.toast.warning("결과가 없습니다.")
        try:
            data = export_to_pdf(text, code)
            return rx.download(data=data, filename=f"aria_{d.get('id', 'x')}.pdf")
        except Exception as e:
            return rx.toast.error(f"PDF 생성 실패: {e}")

    def download_history_docx(self):
        d = self.history_detail or {}
        text = d.get("final_output") or ""
        code = d.get("code_result") or ""
        if not text:
            return rx.toast.warning("결과가 없습니다.")
        try:
            data = export_to_docx(text, code)
            return rx.download(data=data, filename=f"aria_{d.get('id', 'x')}.docx")
        except Exception as e:
            return rx.toast.error(f"Word 생성 실패: {e}")

    def download_history_md(self):
        d = self.history_detail or {}
        text = d.get("final_output") or ""
        if not text:
            return rx.toast.warning("결과가 없습니다.")
        return rx.download(
            data=text.encode("utf-8"),
            filename=f"aria_{d.get('id', 'x')}.md",
        )

    # ── schedule form ─────────────────────────────────────
    def set_s_input(self, v: str):
        self.s_input = v

    def set_s_frequency(self, v: str):
        self.s_frequency = v

    def set_s_hour(self, v: str):
        try:
            self.s_hour = int(v)
        except Exception:
            pass

    def set_s_minute(self, v: str):
        try:
            self.s_minute = int(v)
        except Exception:
            pass

    def set_s_day_of_week(self, v: str):
        try:
            self.s_day_of_week = int(v)
        except Exception:
            pass

    def set_s_day(self, v: str):
        try:
            self.s_day = int(v)
        except Exception:
            pass

    def set_s_send_email(self, v: bool):
        self.s_send_email = v

    def set_s_email_format(self, v: str):
        self.s_email_format = v

    def submit_schedule(self):
        if not (self.s_input or "").strip():
            return rx.toast.warning("입력 내용을 작성해주세요.")
        try:
            freq = self.s_frequency
            sid = sched_mod.add_schedule(
                user_input=self.s_input.strip(),
                frequency=freq,
                hour=self.s_hour if freq in ("daily", "weekly", "monthly") else None,
                minute=self.s_minute,
                day_of_week=self.s_day_of_week if freq == "weekly" else None,
                day=self.s_day if freq == "monthly" else None,
                send_email=self.s_send_email,
                email_format=self.s_email_format,
            )
            self.s_input = ""
            self._refresh_schedule()
            return rx.toast.success(f"스케줄 #{sid} 등록 완료")
        except Exception as e:
            return rx.toast.error(f"등록 실패: {e}")

    def toggle_schedule(self, sid: int):
        item = next((s for s in self.schedule_items if int(s["id"]) == int(sid)), None)
        if not item:
            return
        try:
            sched_mod.set_enabled(int(sid), not bool(item.get("enabled")))
            self._refresh_schedule()
        except Exception as e:
            return rx.toast.error(f"변경 실패: {e}")

    def remove_schedule(self, sid: int):
        try:
            sched_mod.delete_schedule(int(sid))
            self._refresh_schedule()
            return rx.toast.success(f"스케줄 #{sid} 삭제됨")
        except Exception as e:
            return rx.toast.error(f"삭제 실패: {e}")

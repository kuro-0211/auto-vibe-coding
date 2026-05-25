"""스케줄링 모듈 (APScheduler BackgroundScheduler).

- 모든 시간은 Asia/Seoul 기준
- DB: /app/data/schedule.db (history.db / checkpoints.db와 분리)
- 스케줄 실행 시 ARIA 파이프라인(Phase1 → Phase2)을 자동 실행하며,
  HITL 편집 단계는 자동 통과 (코드 그대로 사용)
- 실행 결과는 graph.output_node가 history.db에 자동 저장
- Streamlit 멀티스레딩 주의: 스케줄러 스레드에서 st.session_state 접근 금지
"""
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime
from typing import Optional

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

DB_PATH = "/app/data/schedule.db"
SEOUL = pytz.timezone("Asia/Seoul")

logger = logging.getLogger("aria.scheduler")

_scheduler: Optional[BackgroundScheduler] = None


# ── DB ─────────────────────────────────────────────────────
def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input    TEXT    NOT NULL,
                frequency     TEXT    NOT NULL,
                hour          INTEGER,
                minute        INTEGER,
                day_of_week   INTEGER,
                day           INTEGER,
                enabled       INTEGER NOT NULL DEFAULT 1,
                send_email    INTEGER NOT NULL DEFAULT 0,
                email_format  TEXT    NOT NULL DEFAULT 'none',
                last_run      TEXT,
                last_status   TEXT,
                created_at    TEXT    NOT NULL
            )
        """)
        conn.commit()


def add_schedule(
    user_input: str,
    frequency: str,
    *,
    hour: Optional[int] = None,
    minute: int = 0,
    day_of_week: Optional[int] = None,
    day: Optional[int] = None,
    send_email: bool = False,
    email_format: str = "none",
) -> int:
    init_db()
    now_iso = datetime.now(SEOUL).isoformat(timespec="seconds")
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO schedules
               (user_input, frequency, hour, minute, day_of_week, day,
                enabled, send_email, email_format, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)""",
            (
                user_input, frequency, hour, minute, day_of_week, day,
                1 if send_email else 0, email_format, now_iso,
            ),
        )
        sid = cur.lastrowid or 0
        conn.commit()

    row = get_schedule(sid)
    if row:
        _ensure_job(sid, row)
    return sid


def get_schedule(sid: int) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM schedules WHERE id=?", (sid,)).fetchone()
        return dict(row) if row else None


def list_schedules() -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM schedules ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def delete_schedule(sid: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM schedules WHERE id=?", (sid,))
        conn.commit()
    _remove_job(sid)


def set_enabled(sid: int, enabled: bool) -> None:
    with _connect() as conn:
        conn.execute("UPDATE schedules SET enabled=? WHERE id=?", (1 if enabled else 0, sid))
        conn.commit()
    row = get_schedule(sid)
    if row:
        _ensure_job(sid, row)


def _update_run_status(sid: int, status: str) -> None:
    now_iso = datetime.now(SEOUL).isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute(
            "UPDATE schedules SET last_run=?, last_status=? WHERE id=?",
            (now_iso, status, sid),
        )
        conn.commit()


# ── Trigger / 다음 실행 시간 ───────────────────────────────
def build_trigger(row: dict) -> CronTrigger:
    freq = row["frequency"]
    minute = row.get("minute") or 0
    if freq == "hourly":
        return CronTrigger(minute=minute, timezone=SEOUL)
    if freq == "daily":
        return CronTrigger(hour=row["hour"], minute=minute, timezone=SEOUL)
    if freq == "weekly":
        return CronTrigger(day_of_week=row["day_of_week"], hour=row["hour"],
                           minute=minute, timezone=SEOUL)
    if freq == "monthly":
        return CronTrigger(day=row["day"], hour=row["hour"], minute=minute, timezone=SEOUL)
    raise ValueError(f"unknown frequency: {freq}")


def next_run_time(row: dict) -> Optional[datetime]:
    if not row.get("enabled"):
        return None
    try:
        trig = build_trigger(row)
        return trig.get_next_fire_time(None, datetime.now(SEOUL))
    except Exception as e:
        logger.warning(f"next_run_time error: {e}")
        return None


# ── 스케줄 실행 (APScheduler가 호출) ───────────────────────
def run_scheduled(schedule_id: int) -> None:
    """등록된 스케줄 1건 실행. graph는 자체적으로 history.db에 저장."""
    logger.info(f"[scheduler] run schedule_id={schedule_id}")
    if "/app/src" not in sys.path:
        sys.path.insert(0, "/app/src")

    row = get_schedule(schedule_id)
    if not row:
        logger.warning(f"schedule {schedule_id} not found")
        return
    if not row.get("enabled"):
        logger.info(f"schedule {schedule_id} disabled, skip")
        return

    try:
        from workflows.graph import build_phase1_graph, build_phase2_graph

        start = time.time()
        initial = {
            "user_input": row["user_input"],
            "send_email": bool(row["send_email"]),
            "email_format": row["email_format"] or "none",
            "research_result": None, "code_result": None,
            "execution_result": None, "final_output": None,
            "error": None, "error_analysis": None,
            "retry_count": 0, "needs_code": None,
            "human_approved": True,
            "edited_code": None,
            "start_time": start,
        }
        ts = int(start)
        cfg1 = {"configurable": {"thread_id": f"sched-{schedule_id}-{ts}-p1"}}
        cfg2 = {"configurable": {"thread_id": f"sched-{schedule_id}-{ts}-p2"}}

        # Phase 1 (research → code_decision → code/review/human_review or output)
        g1 = build_phase1_graph()
        state = g1.invoke(initial, config=cfg1)

        # 코드가 생성됐고 최종 결과가 아직이면 Phase 2 자동 진행
        if state.get("code_result") and not state.get("final_output"):
            g2 = build_phase2_graph()
            state = g2.invoke(state, config=cfg2)

        exec_r = state.get("execution_result")
        if exec_r:
            status = "success" if exec_r.get("success") else "fail"
        else:
            status = "success" if state.get("final_output") else "fail"

        _update_run_status(schedule_id, status)
        logger.info(f"[scheduler] schedule {schedule_id} done: {status}")

    except Exception as e:
        logger.exception(f"[scheduler] schedule {schedule_id} failed: {e}")
        try:
            _update_run_status(schedule_id, "fail")
        except Exception:
            pass


# ── Scheduler 싱글톤 ───────────────────────────────────────
def _ensure_job(sid: int, row: dict) -> None:
    if _scheduler is None:
        return
    job_id = f"schedule-{sid}"
    if row.get("enabled"):
        try:
            _scheduler.add_job(
                run_scheduled,
                trigger=build_trigger(row),
                args=[sid],
                id=job_id,
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
        except Exception as e:
            logger.warning(f"failed to register job {job_id}: {e}")
    else:
        _remove_job(sid)


def _remove_job(sid: int) -> None:
    if _scheduler is None:
        return
    try:
        _scheduler.remove_job(f"schedule-{sid}")
    except Exception:
        pass


def init_scheduler() -> BackgroundScheduler:
    """앱 부팅 시 1회 호출. 이미 실행 중이면 동일 인스턴스 반환."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    init_db()
    _scheduler = BackgroundScheduler(timezone=SEOUL)
    _scheduler.start()
    logger.info("[scheduler] BackgroundScheduler started (Asia/Seoul)")

    # 등록된 enabled 스케줄 모두 복원
    for row in list_schedules():
        if row.get("enabled"):
            _ensure_job(row["id"], row)

    return _scheduler


def is_running() -> bool:
    return _scheduler is not None and _scheduler.running

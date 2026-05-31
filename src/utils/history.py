"""실행 히스토리 저장/조회 모듈.

기존 LangGraph SqliteSaver(checkpoints.db)와는 별도 DB(history.db)를 사용해
한 번의 실행 결과(입력, 리서치, 코드, 실행 결과, 에러 분석)를 영속화한다.
"""
import json
import os
import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = "/app/data/history.db"


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """history 테이블이 없으면 생성. schedule_id 컬럼이 없으면 추가."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id      TEXT,
                created_at      TEXT NOT NULL,
                user_input      TEXT NOT NULL,
                success         INTEGER NOT NULL,
                elapsed_sec     INTEGER,
                research_result TEXT,
                code_result     TEXT,
                execution_result TEXT,
                error_analysis  TEXT,
                final_output    TEXT,
                retry_count     INTEGER DEFAULT 0,
                schedule_id     INTEGER
            )
        """)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(history)").fetchall()}
        if "schedule_id" not in cols:
            conn.execute("ALTER TABLE history ADD COLUMN schedule_id INTEGER")
        conn.commit()


def save_run(
    user_input: str,
    success: bool,
    elapsed_sec: Optional[int] = None,
    research_result: Optional[str] = None,
    code_result: Optional[str] = None,
    execution_result: Optional[dict] = None,
    error_analysis: Optional[str] = None,
    final_output: Optional[str] = None,
    retry_count: int = 0,
    session_id: Optional[str] = None,
    schedule_id: Optional[int] = None,
) -> int:
    """단일 실행 결과를 저장하고 row id 반환.

    schedule_id가 None이면 수동 실행(사이드바 히스토리에 노출), 값이 있으면
    스케줄러 자동 실행(스케줄 페이지의 "최근 실행" 섹션에만 노출).
    """
    init_db()
    created_at = datetime.now().isoformat(timespec="seconds")
    exec_json = json.dumps(execution_result, ensure_ascii=False) if execution_result else None

    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO history
               (session_id, created_at, user_input, success, elapsed_sec,
                research_result, code_result, execution_result,
                error_analysis, final_output, retry_count, schedule_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                created_at,
                user_input,
                1 if success else 0,
                elapsed_sec,
                research_result,
                code_result,
                exec_json,
                error_analysis,
                final_output,
                retry_count,
                schedule_id,
            ),
        )
        conn.commit()
        return cur.lastrowid or 0


def list_history(limit: int = 100) -> list[dict]:
    """수동 실행(schedule_id IS NULL)만 최신순으로 조회. 사이드바 히스토리용."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """SELECT id, session_id, created_at, user_input, success,
                      elapsed_sec, retry_count
               FROM history
               WHERE schedule_id IS NULL
               ORDER BY id DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def list_schedule_runs(limit: int = 50, schedule_id: Optional[int] = None) -> list[dict]:
    """스케줄러 자동 실행만 최신순으로 조회. schedule_id 지정 시 해당 스케줄만."""
    init_db()
    with _connect() as conn:
        if schedule_id is None:
            rows = conn.execute(
                """SELECT id, schedule_id, created_at, user_input, success,
                          elapsed_sec, retry_count
                   FROM history
                   WHERE schedule_id IS NOT NULL
                   ORDER BY id DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, schedule_id, created_at, user_input, success,
                          elapsed_sec, retry_count
                   FROM history
                   WHERE schedule_id = ?
                   ORDER BY id DESC
                   LIMIT ?""",
                (schedule_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]


def get_history(history_id: int) -> Optional[dict]:
    """단일 항목 상세 조회."""
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM history WHERE id = ?", (history_id,)
        ).fetchone()
        if not row:
            return None
        item = dict(row)
        if item.get("execution_result"):
            try:
                item["execution_result"] = json.loads(item["execution_result"])
            except json.JSONDecodeError:
                pass
        return item


def clear_history() -> int:
    """수동 실행만 삭제(사이드바 히스토리 대상). 스케줄러 자동 실행은 보존.

    Why: '히스토리 전체 삭제' 버튼은 사이드바 히스토리 정리용이므로 스케줄
    페이지에서 따로 관리되는 자동 실행 기록까지 지우면 곤란하다.
    """
    init_db()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM history WHERE schedule_id IS NULL")
        conn.commit()
        return cur.rowcount


def save_run_from_state(state: dict, elapsed_sec: Optional[int] = None) -> int:
    """파이프라인 state 딕셔너리에서 직접 저장."""
    exec_r = state.get("execution_result")
    if exec_r and isinstance(exec_r, dict):
        success = bool(exec_r.get("success"))
    else:
        success = bool(state.get("final_output"))

    sid = state.get("schedule_id")
    return save_run(
        user_input=state.get("user_input", ""),
        success=success,
        elapsed_sec=elapsed_sec,
        research_result=state.get("research_result"),
        code_result=state.get("code_result"),
        execution_result=exec_r if isinstance(exec_r, dict) else None,
        error_analysis=state.get("error_analysis"),
        final_output=state.get("final_output"),
        retry_count=state.get("retry_count", 0) or 0,
        schedule_id=int(sid) if sid else None,
    )

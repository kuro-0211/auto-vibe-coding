"""SQLite 기반 멀티스텝 프로젝트 관리 모듈.

기존 history.db / checkpoints.db와 별도의 DB(projects.db)를 사용해
하나의 프로젝트 안에서 여러 세션(파이프라인 실행)을 누적·연결한다.
"""
import json
import os
import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = "/app/data/projects.db"


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """projects/sessions 테이블이 없으면 생성."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                description TEXT,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'active'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id       INTEGER NOT NULL,
                session_number   INTEGER NOT NULL,
                user_input       TEXT,
                research_result  TEXT,
                code_result      TEXT,
                execution_result TEXT,
                error_analysis   TEXT,
                final_output     TEXT,
                success          INTEGER NOT NULL DEFAULT 0,
                created_at       TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id)"
        )
        conn.commit()


def create_project(name: str, description: str = "") -> int:
    """새 프로젝트 생성. 생성된 project_id 반환."""
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO projects (name, description, created_at, updated_at, status)
               VALUES (?, ?, ?, ?, 'active')""",
            (name.strip(), (description or "").strip(), now, now),
        )
        conn.commit()
        return cur.lastrowid or 0


def get_projects() -> list[dict]:
    """프로젝트 목록(최근 수정순). 각 항목에 session_count, last_session_at 포함."""
    init_db()
    with _connect() as conn:
        rows = conn.execute("""
            SELECT
                p.id, p.name, p.description, p.created_at, p.updated_at, p.status,
                COUNT(s.id) AS session_count,
                MAX(s.created_at) AS last_session_at
            FROM projects p
            LEFT JOIN sessions s ON s.project_id = p.id
            GROUP BY p.id
            ORDER BY p.updated_at DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_project(project_id: int) -> Optional[dict]:
    """단일 프로젝트 상세 + 세션 수."""
    init_db()
    with _connect() as conn:
        row = conn.execute("""
            SELECT p.*,
                   COUNT(s.id) AS session_count,
                   MAX(s.created_at) AS last_session_at
            FROM projects p
            LEFT JOIN sessions s ON s.project_id = p.id
            WHERE p.id = ?
            GROUP BY p.id
        """, (project_id,)).fetchone()
        return dict(row) if row else None


def update_project_status(project_id: int, status: str) -> None:
    """프로젝트 상태 변경 (active/completed/paused)."""
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute(
            "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, project_id),
        )
        conn.commit()


def delete_project(project_id: int) -> None:
    """프로젝트 + 연결된 세션 삭제."""
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()


def get_sessions(project_id: int) -> list[dict]:
    """프로젝트의 세션 목록(오래된 순 = 1단계 → N단계)."""
    init_db()
    with _connect() as conn:
        rows = conn.execute("""
            SELECT id, project_id, session_number, user_input, success, created_at
            FROM sessions
            WHERE project_id = ?
            ORDER BY session_number ASC
        """, (project_id,)).fetchall()
        return [dict(r) for r in rows]


def get_session(session_id: int) -> Optional[dict]:
    """단일 세션 상세. execution_result는 JSON 디코딩."""
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
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


def get_latest_session(project_id: int) -> Optional[dict]:
    """가장 최근(가장 큰 session_number) 세션."""
    init_db()
    with _connect() as conn:
        row = conn.execute("""
            SELECT * FROM sessions
            WHERE project_id = ?
            ORDER BY session_number DESC
            LIMIT 1
        """, (project_id,)).fetchone()
        if not row:
            return None
        item = dict(row)
        if item.get("execution_result"):
            try:
                item["execution_result"] = json.loads(item["execution_result"])
            except json.JSONDecodeError:
                pass
        return item


def _next_session_number(conn: sqlite3.Connection, project_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(session_number), 0) AS n FROM sessions WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    return int(row["n"]) + 1


def save_session(project_id: int, state: dict) -> int:
    """파이프라인 state를 새 세션으로 저장하고 session_id 반환."""
    init_db()
    now = datetime.now().isoformat(timespec="seconds")
    exec_r = state.get("execution_result")
    exec_json = json.dumps(exec_r, ensure_ascii=False) if isinstance(exec_r, dict) else None

    if isinstance(exec_r, dict):
        success = bool(exec_r.get("success"))
    else:
        success = bool(state.get("final_output"))

    with _connect() as conn:
        n = _next_session_number(conn, project_id)
        cur = conn.execute(
            """INSERT INTO sessions
               (project_id, session_number, user_input, research_result,
                code_result, execution_result, error_analysis, final_output,
                success, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                n,
                state.get("user_input", ""),
                state.get("research_result"),
                state.get("code_result"),
                exec_json,
                state.get("error_analysis"),
                state.get("final_output"),
                1 if success else 0,
                now,
            ),
        )
        # 프로젝트 updated_at 갱신
        conn.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (now, project_id),
        )
        conn.commit()
        return cur.lastrowid or 0


def get_project_context(project_id: int) -> dict:
    """이어서 작업할 때 파이프라인에 주입할 컨텍스트.

    반환:
      {
        "previous_code": <마지막 세션의 코드 or None>,
        "previous_context": <마지막 세션의 리서치 요약 or None>,
        "session_number": <다음 세션 번호>,
      }
    """
    init_db()
    latest = get_latest_session(project_id)
    if not latest:
        return {
            "previous_code": None,
            "previous_context": None,
            "session_number": 1,
        }
    return {
        "previous_code": latest.get("code_result"),
        "previous_context": latest.get("research_result"),
        "session_number": int(latest.get("session_number") or 0) + 1,
    }

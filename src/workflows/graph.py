import sys
sys.path.insert(0, "/app/src")
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Optional
from agents.research_agent import run_research
from agents.code_agent import run_code_generation, run_code_review, run_error_analysis
from agents.output_agent import run_output
from agents.email_agent import run_email
from sandbox.executor import execute_code
import sqlite3
import os

# ── 상태 정의 ──────────────────────────────────────────────
class AgentState(TypedDict):
    user_input: str
    send_email: bool
    research_result: Optional[str]
    code_result: Optional[str]
    execution_result: Optional[dict]
    final_output: Optional[str]
    error: Optional[str]
    retry_count: int
    needs_code: Optional[bool]
    human_approved: Optional[bool]

# ── 노드 함수 ──────────────────────────────────────────────
def research_node(state: AgentState) -> AgentState:
    print("🔍 Research Agent 실행 중...")
    result = run_research(state["user_input"])
    return {**state, "research_result": result}

def code_decision_node(state: AgentState) -> AgentState:
    keywords = ["코드", "만들어", "구현", "작성", "짜줘", "개발", "프로그램", "스크립트", "함수", "클래스"]
    needs_code = any(k in state["user_input"] for k in keywords)
    print(f"💡 코드 생성 필요: {needs_code}")
    return {**state, "needs_code": needs_code}

def code_generation_node(state: AgentState) -> AgentState:
    print("🦙 Ollama 코드 생성 중...")
    code = run_code_generation(
        user_input=state["user_input"],
        research_result=state["research_result"]
    )
    return {**state, "code_result": code, "error": None, "human_approved": None}

def code_review_node(state: AgentState) -> AgentState:
    print("🔍 qwen2.5-coder 코드 리뷰 중...")
    reviewed = run_code_review(
        code=state["code_result"],
        user_input=state["user_input"]
    )
    return {**state, "code_result": reviewed}

def human_approval_node(state: AgentState) -> AgentState:
    """Human-in-the-Loop: 사용자 승인 대기"""
    print("⏳ 사용자 승인 대기 중...")
    return {**state, "human_approved": None}

def execution_node(state: AgentState) -> AgentState:
    print("🐳 Docker 샌드박스 실행 중...")
    result = execute_code(state["code_result"])
    return {**state, "execution_result": result}

def error_analysis_node(state: AgentState) -> AgentState:
    print(f"⚠️  에러 분석 중... (재시도 {state['retry_count'] + 1}/3)")
    fixed_code = run_error_analysis(
        code=state["code_result"],
        error=state["execution_result"].get("error", ""),
        user_input=state["user_input"]
    )
    return {
        **state,
        "code_result": fixed_code,
        "retry_count": state["retry_count"] + 1
    }

def output_node(state: AgentState) -> AgentState:
    print("📄 Output Agent 결과 정리 중...")
    output = run_output(state)
    return {**state, "final_output": output}

def email_node(state: AgentState) -> AgentState:
    print("📧 이메일 발송 중...")
    run_email(state["final_output"])
    return state

# ── 분기 조건 ──────────────────────────────────────────────
def should_generate_code(state: AgentState) -> str:
    return "code_generation" if state["needs_code"] else "output"

def check_human_approval(state: AgentState) -> str:
    approved = state.get("human_approved")
    if approved is True:
        return "execution"
    elif approved is False:
        return "code_generation"
    else:
        return "human_approval"

def check_execution(state: AgentState) -> str:
    if state["execution_result"]["success"]:
        return "output"
    elif state["retry_count"] >= 3:
        return "output"
    else:
        return "error_analysis"

def should_send_email(state: AgentState) -> str:
    return "email" if state["send_email"] else END

def _get_checkpointer():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/checkpoints.db", check_same_thread=False)
    return SqliteSaver(conn)

# ── 그래프 빌드 ────────────────────────────────────────────
def build_graph(session_id: str = "default"):
    # SQLite Checkpointer
    db_path = "data/checkpoints.db"
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    graph = StateGraph(AgentState)

    graph.add_node("research", research_node)
    graph.add_node("code_decision", code_decision_node)
    graph.add_node("code_generation", code_generation_node)
    graph.add_node("code_review", code_review_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("execution", execution_node)
    graph.add_node("error_analysis", error_analysis_node)
    graph.add_node("output", output_node)
    graph.add_node("email", email_node)

    graph.set_entry_point("research")
    graph.add_edge("research", "code_decision")
    graph.add_conditional_edges("code_decision", should_generate_code)
    graph.add_edge("code_generation", "code_review")
    graph.add_edge("code_review", "human_approval")
    graph.add_conditional_edges("human_approval", check_human_approval)
    graph.add_conditional_edges("execution", check_execution)
    graph.add_edge("error_analysis", "code_generation")
    graph.add_conditional_edges("output", should_send_email)
    graph.add_edge("email", END)

    return graph.compile(checkpointer=checkpointer)


def build_phase1_graph():
    """1단계: 리서치 → 코드 생성 → 코드 리뷰"""
    checkpointer = _get_checkpointer()
    graph = StateGraph(AgentState)

    graph.add_node("research", research_node)
    graph.add_node("code_decision", code_decision_node)
    graph.add_node("code_generation", code_generation_node)
    graph.add_node("code_review", code_review_node)

    graph.set_entry_point("research")
    graph.add_edge("research", "code_decision")
    graph.add_conditional_edges("code_decision", should_generate_code, {
        "code_generation": "code_generation",
        "output": END
    })
    graph.add_edge("code_generation", "code_review")
    graph.add_edge("code_review", END)

    return graph.compile(checkpointer=checkpointer)

def build_phase2_graph():
    """2단계: 실행 → 에러 분석 → 결과 출력 → 이메일"""
    checkpointer = _get_checkpointer()
    graph = StateGraph(AgentState)

    graph.add_node("execution", execution_node)
    graph.add_node("error_analysis", error_analysis_node)
    graph.add_node("code_generation", code_generation_node)
    graph.add_node("code_review", code_review_node)
    graph.add_node("output", output_node)
    graph.add_node("email", email_node)

    graph.set_entry_point("execution")
    graph.add_conditional_edges("execution", check_execution)
    graph.add_edge("error_analysis", "code_generation")
    graph.add_edge("code_generation", "code_review")
    graph.add_edge("code_review", "execution")
    graph.add_conditional_edges("output", should_send_email)
    graph.add_edge("email", END)

    return graph.compile(checkpointer=checkpointer)

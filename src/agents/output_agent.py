import os
from dotenv import load_dotenv
load_dotenv("/app/.env")
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from utils.logger import pipeline_logger

def run_output(state: dict) -> str:
    pipeline_logger.log_step("Output Agent", "running")

    llm = ChatOllama(
        model=os.getenv("GEMMA_MODEL", "gemma3:4b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        temperature=0.3
    )

    research = state.get("research_result", "")
    code = state.get("code_result", "")
    execution = state.get("execution_result", {})
    retry_count = state.get("retry_count", 0)

    if execution:
        if execution.get("success"):
            exec_summary = f"✅ 실행 성공\n{execution.get('output', '')}"
        else:
            exec_summary = f"❌ 실행 실패 ({retry_count}회 시도)\n{execution.get('error', '')}"
    else:
        exec_summary = "코드 실행 없음"

    prompt = f"""
다음 내용을 바탕으로 최종 결과 문서를 작성해주세요.

## 리서치 결과
{research}

## 생성된 코드
{code if code else "코드 생성 없음"}

## 실행 결과
{exec_summary}

## 출력 형식
# 결과 요약
(핵심 내용 3~5줄)

## 리서치 내용
(정리된 내용)

## 코드
(생성된 코드, 있는 경우)

## 실행 결과
(실행 결과, 있는 경우)

한국어로 작성하세요.
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    pipeline_logger.log_llm(
        model="gemma3:4b",
        prompt=prompt,
        response=response.content,
        tokens=0
    )
    pipeline_logger.log_step("Output Agent", "done", output_data=response.content)

    return response.content

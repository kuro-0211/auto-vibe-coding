import os
from dotenv import load_dotenv
load_dotenv("/app/.env")
from openai import OpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from utils.logger import pipeline_logger

def _get_ollama_coder():
    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        temperature=0.2
    )

def _get_ollama_gemma():
    return ChatOllama(
        model=os.getenv("GEMMA_MODEL", "gemma3:4b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        temperature=0.3
    )

def _get_school_client():
    return OpenAI(
        api_key=os.getenv("SCHOOL_API_KEY"),
        base_url=os.getenv("SCHOOL_API_BASE_URL")
    )

def run_code_generation(user_input: str, research_result: str) -> str:
    pipeline_logger.log_step("Code Generation", "running", input_data=user_input)

    llm = _get_ollama_coder()

    prompt = f"""
다음 요청에 맞는 코드를 작성해주세요.

## 사용자 요청
{user_input}

## 리서치 결과 (참고용)
{research_result}

## 요구사항
- 실행 가능한 완성된 코드만 작성
- 주석 포함
- 코드 블록 없이 순수 코드만 출력
- Python으로 작성
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    pipeline_logger.log_llm(
        model="qwen2.5-coder",
        prompt=prompt,
        response=response.content,
        tokens=0
    )
    pipeline_logger.log_step("Code Generation", "done", output_data=response.content)

    return response.content.strip()

def run_code_review(code: str, user_input: str) -> str:
    pipeline_logger.log_step("Code Review", "running", input_data=code)

    llm = _get_ollama_coder()

    prompt = f"""
다음 코드를 리뷰해주세요.

## 사용자 의도
{user_input}

## 코드
{code}

## 검토 항목
1. 사용자 의도와 코드가 일치하는가?
2. 문법 오류가 있는가?
3. 보안 문제가 있는가?
4. 로직 오류가 있는가?

문제가 있으면 수정된 코드를, 없으면 원본 코드를 그대로 반환하세요.
코드만 반환하고 설명은 제외하세요.
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    pipeline_logger.log_llm(
        model="qwen2.5-coder",
        prompt=prompt,
        response=response.content,
        tokens=0
    )
    pipeline_logger.log_step("Code Review", "done", output_data=response.content)

    return response.content.strip()

def run_error_analysis(code: str, error: str, user_input: str) -> str:
    pipeline_logger.log_step("Error Analysis", "running", input_data=error)

    # Gemma로 에러 분석
    gemma = _get_ollama_gemma()

    analysis_prompt = f"""
다음 코드 실행 중 에러가 발생했습니다.

## 코드
{code}

## 에러 메시지
{error}

에러 원인을 분석하고 수정 방법을 간단히 설명해주세요. (3줄 이내)
"""
    analysis = gemma.invoke([HumanMessage(content=analysis_prompt)])

    pipeline_logger.log_llm(
        model="gemma3:4b",
        prompt=analysis_prompt,
        response=analysis.content,
        tokens=0
    )

    # qwen2.5-coder로 수정 코드 생성
    coder = _get_ollama_coder()
    fix_prompt = f"""
다음 코드의 에러를 수정해주세요.

## 사용자 요청
{user_input}

## 기존 코드
{code}

## 에러 분석
{analysis.content}

수정된 완성 코드만 반환하세요. 설명 없이 코드만 출력하세요.
"""
    fixed = coder.invoke([HumanMessage(content=fix_prompt)])

    pipeline_logger.log_step("Error Analysis", "done", output_data=fixed.content)

    return fixed.content.strip()

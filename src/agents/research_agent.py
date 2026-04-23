import os
from tavily import TavilyClient
from google import genai
from utils.logger import pipeline_logger

def run_research(user_input: str) -> str:
    pipeline_logger.log_step("Research Agent", "running", input_data=user_input)

    # ── Tavily 웹 검색 ──────────────────────────────────────
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    search_results = tavily.search(
        query=user_input,
        max_results=5,
        search_depth="advanced"
    )

    raw_content = "\n\n".join([
        f"[{r['title']}]\n{r['content']}"
        for r in search_results.get("results", [])
    ])

    # ── Gemini Flash 정리 ───────────────────────────────────
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = f"""
다음은 "{user_input}"에 대한 웹 검색 결과입니다.

{raw_content}

위 내용을 바탕으로:
1. 핵심 개념 요약
2. 주요 기술/방법론
3. 코드 예제 또는 구현 방법 (있는 경우)
4. 참고할 최신 정보

위 형식으로 명확하게 정리해주세요. 한국어로 작성하세요.
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt
    )

    pipeline_logger.log_llm(
        model="gemini-2.5-flash",
        prompt=prompt,
        response=response.text,
        tokens=len(prompt.split()) + len(response.text.split())
    )

    pipeline_logger.log_step(
        "Research Agent", "done",
        input_data=user_input,
        output_data=response.text
    )

    return response.text

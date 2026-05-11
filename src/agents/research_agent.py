import os
from dotenv import load_dotenv
load_dotenv('/app/.env')
from tavily import TavilyClient
from openai import OpenAI
from utils.logger import pipeline_logger

def run_research(user_input: str) -> str:
    pipeline_logger.log_step("Research Agent", "running", input_data=user_input)

    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    search_results = tavily.search(
        query=user_input,
        max_results=5,
        search_depth="basic",
        include_domains=[
            "docs.python.org", "github.com", "stackoverflow.com",
            "medium.com", "dev.to", "realpython.com", "fastapi.tiangolo.com"
        ]
    )

    results = search_results.get("results", [])

    # 출처 URL 포함해서 정제
    raw_content = ""
    sources = []
    for r in results:
        title = r.get("title", "")
        content = r.get("content", "")[:300]
        url = r.get("url", "")
        raw_content += f"[{title}]\n{content}\n\n"
        sources.append(f"- {title}: {url}")

    raw_content = raw_content[:1500]
    sources_text = "\n".join(sources)

    client = OpenAI(
        api_key=os.getenv("SCHOOL_API_KEY"),
        base_url=os.getenv("SCHOOL_API_BASE_URL")
    )

    prompt = f"""다음 웹 검색 결과를 바탕으로 "{user_input}"에 대해 정리해주세요.

검색 결과:
{raw_content}

다음 형식으로 한국어로 작성하세요:

## 핵심 요약
(3~5줄로 핵심 내용 요약)

## 주요 내용
(중요한 개념, 방법론, 예제 코드 포함)

## 참고 출처
{sources_text}
"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("SCHOOL_MODEL", "gpt-5.4-mini"),
            temperature=1,
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
    except Exception as e:
        print(f"학교 API 에러: {e}")
        raise

    pipeline_logger.log_llm(
        model="gpt-5.4-mini",
        prompt=prompt,
        response=result,
        tokens=tokens
    )
    pipeline_logger.log_step("Research Agent", "done",
        input_data=user_input, output_data=result)

    return result
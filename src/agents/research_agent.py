import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv('/app/.env')
from tavily import TavilyClient
from openai import OpenAI
from utils.logger import pipeline_logger

def run_research(user_input: str) -> str:
    pipeline_logger.log_step("Research Agent", "running", input_data=user_input)

    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    # 도메인 제한 없이 advanced 모드로 검색 — 시사·뉴스성 쿼리도 잡히게.
    search_results = tavily.search(
        query=user_input,
        max_results=7,
        search_depth="advanced",
    )

    results = search_results.get("results", [])

    # 출처 URL + 게시일 포함해서 정제
    raw_content = ""
    sources = []
    for r in results:
        title = r.get("title", "")
        content = r.get("content", "")[:400]
        url = r.get("url", "")
        published = r.get("published_date") or ""
        date_tag = f" ({published[:10]})" if published else ""
        raw_content += f"[{title}{date_tag}]\n{content}\n\n"
        sources.append(f"- {title}{date_tag}: {url}")

    raw_content = raw_content[:2500]
    sources_text = "\n".join(sources)

    client = OpenAI(
        api_key=os.getenv("SCHOOL_API_KEY"),
        base_url=os.getenv("SCHOOL_API_BASE_URL")
    )

    today = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""당신은 검색 결과 정리 보조입니다.

# 현재 날짜
{today}

# 규칙 (반드시 준수)
1. 아래 "검색 결과"에 명시된 사실만 사용합니다.
2. 검색 결과에 없는 정보는 절대 추측·보완·창작하지 않습니다.
   알 수 없으면 "검색 결과에 해당 정보가 없습니다"라고 명시하세요.
3. 학습 데이터(과거 지식)로 빈칸을 메우지 마세요.
4. 각 항목 끝에 출처 [제목] 표기를 남기세요.
5. 게시일이 표시된 항목은 우선 활용하고, 현재 날짜와의 차이를 고려하세요.

# 사용자 질의
{user_input}

# 검색 결과
{raw_content}

# 출력 형식 (한국어)
## 핵심 요약
(3~5줄, 검색 결과에 근거)

## 주요 내용
(개념·방법론·예시, 출처 [제목] 인용 포함)

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
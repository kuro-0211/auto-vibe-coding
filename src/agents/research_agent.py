import os
from dotenv import load_dotenv
load_dotenv('/app/.env')
from tavily import TavilyClient
from openai import OpenAI
from utils.logger import pipeline_logger

def run_research(user_input: str) -> str:
    pipeline_logger.log_step('Research Agent', 'running', input_data=user_input)

    tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
    search_results = tavily.search(query=user_input, max_results=2, search_depth='basic')

    raw_content = ' '.join([r['content'][:200] for r in search_results.get('results', [])])

    client = OpenAI(
        api_key=os.getenv('SCHOOL_API_KEY'),
        base_url=os.getenv('SCHOOL_API_BASE_URL')
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv('SCHOOL_MODEL', 'gpt-5.4-mini'),
            temperature=1,
            messages=[
                {'role': 'user', 'content': f'{user_input}에 대해 요약해줘: {raw_content[:500]}'}
            ]
        )
    except Exception as e:
        print(f'학교 API 에러: {type(e).__name__}: {str(e)[:200]}')
        raise

    result = response.choices[0].message.content
    tokens = response.usage.total_tokens if response.usage else 0

    pipeline_logger.log_llm(model='gpt-5.4-mini', prompt=user_input, response=result, tokens=tokens)
    pipeline_logger.log_step('Research Agent', 'done', input_data=user_input, output_data=result)

    return result

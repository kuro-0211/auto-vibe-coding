"""사용자 요청에 코드 생성이 필요한지 판단하는 에이전트.

GPT-5.4-mini로 의도를 분석하고, API 오류 시 키워드 매칭으로 폴백한다.
이전엔 workflows/graph.py 안에서 인라인으로 처리하던 로직을 분리한 것 — 다른
LLM 호출(`run_research`, `run_code_generation` 등)과 동일한 위치 규약을 따른다.
"""
import os
import json
from dotenv import load_dotenv
load_dotenv("/app/.env")
from openai import OpenAI
from utils.logger import pipeline_logger


_KEYWORDS = [
    "코드", "만들어", "구현", "작성", "짜줘",
    "개발", "프로그램", "스크립트", "함수", "클래스",
]


def _fallback_by_keyword(user_input: str) -> bool:
    return any(k in user_input for k in _KEYWORDS)


def decide_needs_code(user_input: str) -> bool:
    """사용자 요청이 코드 생성을 필요로 하는지 bool로 반환.

    LLM(JSON 또는 자연어로 true/false) 우선, 실패 시 키워드 폴백.
    """
    pipeline_logger.log_step("Code Decision", "running", input_data=user_input)

    try:
        client = OpenAI(
            api_key=os.getenv("SCHOOL_API_KEY"),
            base_url=os.getenv("SCHOOL_API_BASE_URL"),
        )

        response = client.chat.completions.create(
            model=os.getenv("SCHOOL_MODEL", "gpt-5.4-mini"),
            temperature=1,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "사용자 요청이 코드 생성이 필요한지 판단하세요. "
                        "반드시 JSON으로만 응답: "
                        "{\"needs_code\": true} 또는 {\"needs_code\": false}"
                    ),
                },
                {"role": "user", "content": f"요청: {user_input}"},
            ],
        )

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("응답이 None")

        content = content.strip()
        if "true" in content.lower():
            needs_code = True
        elif "false" in content.lower():
            needs_code = False
        else:
            parsed = json.loads(content)
            needs_code = bool(parsed.get("needs_code", False))

    except Exception as e:
        print(f"⚠️ code_decision 오류, 키워드 방식으로 폴백: {e}")
        needs_code = _fallback_by_keyword(user_input)

    pipeline_logger.log_step(
        "Code Decision", "done",
        input_data=user_input, output_data=str(needs_code),
    )
    return needs_code

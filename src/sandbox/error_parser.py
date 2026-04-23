import re

def parse_error(error_log: str) -> dict:
    """에러 로그를 분석하여 구조화된 정보 반환"""

    result = {
        "error_type": "Unknown",
        "error_message": error_log,
        "line_number": None,
        "summary": error_log[:300]
    }

    if not error_log:
        return result

    # 에러 타입 추출 (예: SyntaxError, NameError 등)
    type_match = re.search(
        r"(SyntaxError|NameError|TypeError|ValueError|ImportError|"
        r"AttributeError|IndexError|KeyError|RuntimeError|ModuleNotFoundError)"
        r"[:\s](.+)",
        error_log
    )
    if type_match:
        result["error_type"] = type_match.group(1)
        result["error_message"] = type_match.group(2).strip()

    # 라인 번호 추출
    line_match = re.search(r"line (\d+)", error_log)
    if line_match:
        result["line_number"] = int(line_match.group(1))

    # 요약 (마지막 3줄)
    lines = [l for l in error_log.strip().split("\n") if l.strip()]
    result["summary"] = "\n".join(lines[-3:]) if len(lines) >= 3 else error_log

    return result


def format_error_for_agent(error_log: str) -> str:
    """에이전트에게 전달할 형식으로 에러 정제"""
    parsed = parse_error(error_log)

    return f"""
에러 타입: {parsed['error_type']}
에러 메시지: {parsed['error_message']}
발생 라인: {parsed['line_number'] if parsed['line_number'] else '알 수 없음'}
요약:
{parsed['summary']}
""".strip()

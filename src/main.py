import os
from dotenv import load_dotenv
from workflows.graph import build_graph

load_dotenv()

def main():
    graph = build_graph()

    print("🚀 Auto Vibe Coding Engine 시작")
    print("=" * 50)

    user_input = input("키워드 또는 목적을 입력하세요: ").strip()
    if not user_input:
        print("입력이 없습니다.")
        return

    # 이메일 발송 여부 확인
    email_request = input("결과를 이메일로 받으시겠습니까? (y/n): ").strip().lower()
    send_email = email_request == "y"

    initial_state = {
        "user_input": user_input,
        "send_email": send_email,
        "email_format": "none",
        "research_result": None,
        "code_result": None,
        "execution_result": None,
        "final_output": None,
        "error": None,
        "error_analysis": None,
        "retry_count": 0,
        "needs_code": None,
        "human_approved": None,
        "edited_code": None,
        "start_time": None,
        # 멀티스텝 프로젝트 컨텍스트 (CLI는 프로젝트 미사용)
        "project_id": None,
        "previous_code": None,
        "previous_context": None,
        "session_number": 1,
    }

    print("\n⚙️  파이프라인 실행 중...\n")
    result = graph.invoke(initial_state)

    print("\n" + "=" * 50)
    print("✅ 완료!")
    print("=" * 50)
    if result.get("final_output"):
        print(result["final_output"])

if __name__ == "__main__":
    main()

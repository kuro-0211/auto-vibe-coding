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
        "research_result": None,
        "code_result": None,
        "execution_result": None,
        "final_output": None,
        "error": None,
        "retry_count": 0,
        "needs_code": None,
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

from langchain_core.messages import HumanMessage
from typing import Any
from lab03.harness import PermissionGuard
from lab03.agents import ReActFlightAgent, PlanThenExecuteFlightAgent, HybridFlightAgent


def create_initial_state(user_session: str = "user_valid_session"):
    return {
        "messages": [HumanMessage(content="Tôi muốn tìm vé và đặt vé từ SGN đi HAN vào ngày 2026-10-10 cho hành khách Nguyen Van A.")],
        "plan": None,
        "current_step": 0,
        "pnr": None,
        "handoff": False,
        "user_session": user_session,
        "execution_metrics": {"steps": 0, "tool_calls": 0}
    }

def extract_text_content(content: Any) -> str:
    """Trích xuất text thuần nếu content là dạng block [{'type': 'text', 'text': ...}]."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
        return "\n".join(text_parts)
    return str(content)


def print_agent_summary(agent_title: str, result: dict):
    user_prompt = extract_text_content(result["messages"][0].content)
    final_bot_response = extract_text_content(result["messages"][-1].content)
    metrics = result.get("execution_metrics", {})

    print("\n" + "=" * 65)
    print(f"💬 KẾT QUẢ HỘI THOẠI & THỰC THI: {agent_title.upper()}")
    print("=" * 65)
    print(f'👤 User: "{user_prompt}"')

    print("\n📊 Thống kê thực thi:")
    print(f"  • Số bước suy luận / thực thi : {metrics.get('steps', 0)}")
    print(f"  • Tổng số lần gọi Tool        : {metrics.get('tool_calls', 0)}")
    print(f"  • Mã đặt chỗ (PNR)            : {result.get('pnr', 'N/A')}")
    print(f"  • Kích hoạt bàn giao CSKH     : {result.get('handoff', False)}")

    print("\n🤖 Agent:")
    print(f"{final_bot_response}")
    print("=" * 65 + "\n")

def run_demo():
    guard = PermissionGuard()

    print("=" * 70)
    print("🚀 BẮT ĐẦU CHẠY THỬ NGHIỆM 3 MẪU THIẾT KẾ AGENT")
    print("=" * 70)

    # 1. REACT AGENT
    print("\n[1] TEST REACT AGENT...")
    react_agent = ReActFlightAgent(permission_guard=guard)
    app_react = react_agent.build_graph()
    result_react = app_react.invoke(create_initial_state(user_session="USER_SESSION_8899"))
    print_agent_summary("ReAct Agent", result_react)

    # 2. PLAN-THEN-EXECUTE AGENT
    print("-" * 70)
    print("[2] TEST PLAN-THEN-EXECUTE AGENT...")
    plan_agent = PlanThenExecuteFlightAgent(permission_guard=guard)
    app_plan = plan_agent.build_graph()
    result_plan = app_plan.invoke(create_initial_state(user_session="USER_SESSION_8899"))
    print_agent_summary("Plan-then-Execute Agent", result_plan)

    # 3. HYBRID AGENT
    print("-" * 70)
    print("[3] TEST HYBRID AGENT (Có Handoff)...")
    hybrid_agent = HybridFlightAgent(permission_guard=guard)
    app_hybrid = hybrid_agent.build_graph()
    result_hybrid = app_hybrid.invoke(create_initial_state(user_session="unauthorized_session"))
    print_agent_summary("Hybrid Agent", result_hybrid)


if __name__ == "__main__":
    run_demo()
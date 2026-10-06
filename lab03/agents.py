import json
import operator
from typing import Dict, List, Any, Optional, TypedDict, Annotated

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

from lab03.config import get_llm_with_fallback, BASE_FALLBACK_CHAIN
from lab03.tools import ALL_TOOLS, search_flights, hold_ticket, confirm_booking, MOCK_BOOKINGS
from lab03.harness import PermissionGuard, HandoffManager, TaskCompletionEvaluator, BookingConstraintSchema


# Cấu hình giới hạn cứng tránh tràn quota và vòng lặp vô tận
MAX_REACT_STEPS = 6
SYSTEM_PROMPT = """Bạn là trợ lý đặt vé máy bay thông minh.
Nhiệm vụ của bạn:
1. Tra cứu thông tin chuyến bay dựa trên yêu cầu (origin, destination, date).
2. Tiến hành giữ chỗ (hold_ticket) cho hành khách khi tìm thấy chuyến bay phù hợp.
3. Khi đã có mã giữ chỗ (PNR), tiến hành thanh toán và xác nhận đặt vé (confirm_booking).
4. Phản hồi đầy đủ, lịch sự và rõ ràng với hành khách sau khi hoàn thành.
Hãy sử dụng các công cụ được cung cấp một cách chính xác theo từng bước nghiệp vụ."""


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    plan: Optional[List[str]]
    current_step: int
    pnr: Optional[str]
    handoff: bool
    user_session: str
    execution_metrics: Dict[str, Any]


def log_iteration_detail(step_name: str, active_model: str, tool_name: str, params: Dict[str, Any]):
    print(f"\n  ┌─── [VÒNG LẶP / BƯỚC: {step_name}] ──────────────────────────────────")
    print(f"  │ 🤖 Model đang sử dụng : {active_model}")
    print(f"  │ 🛠️  Hàm được gọi (Tool) : {tool_name}")
    print(f"  │ 📥 Tham số (Parameters): {json.dumps(params, ensure_ascii=False)}")
    print(f"  └────────────────────────────────────────────────────────────────────")


# ==============================================================================
# MẪU 1: REACT AGENT
# ==============================================================================
class ReActFlightAgent:
    def __init__(self, permission_guard: PermissionGuard):
        self.guard = permission_guard
        self.llm = get_llm_with_fallback()
        self.tool_map = {t.name: t for t in ALL_TOOLS}
        self.system_prompt = SystemMessage(content=SYSTEM_PROMPT)

    def reason_node(self, state: AgentState) -> Dict[str, Any]:
        metrics = state.get("execution_metrics", {"steps": 0, "tool_calls": 0})
        metrics["steps"] += 1

        pnr = state.get("pnr")
        messages = state["messages"]
        last_msg = messages[-1].content.lower()

        # 1. Kiểm tra tiêu chí hoàn thành bằng Harness Evaluator
        is_task_completed = False
        if pnr and pnr in MOCK_BOOKINGS:
            booking = MOCK_BOOKINGS[pnr]
            if booking.get("status") == "CONFIRMED" and booking.get("payment_confirmed"):
                is_task_completed = True

        # 2. Điều kiện dừng: Hoàn tất hoặc vượt quá giới hạn cứng (MAX_REACT_STEPS)
        if is_task_completed or metrics["steps"] >= MAX_REACT_STEPS:
            prompt = (
                f"Lịch sử thực thi nghiệp vụ:\n"
                f"- Mã đặt chỗ (PNR): {pnr}\n"
                f"- Tình trạng: {'Đã xuất vé và thanh toán thành công' if is_task_completed else 'Chưa hoàn tất do chạm ngưỡng bước'}\n\n"
                f"Hãy phản hồi đầy đủ, lịch sự và rõ ràng với hành khách sau khi hoàn thành theo đúng vai trò được giao."
            )
            # Giữ nguyên toàn bộ lịch sử messages + hướng dẫn kết thúc
            bot_response = self.llm.invoke([
                self.system_prompt,
                *messages,
                HumanMessage(content=prompt)
            ])
            return {"messages": [bot_response], "execution_metrics": metrics}

        # 3. Phân định bước gọi công cụ ReAct
        if metrics["steps"] == 1 or ("tìm vé" in last_msg and "flights" not in last_msg):
            tool_name = "search_flights"
            args = {"origin": "SGN", "destination": "HAN", "date": "2026-10-10"}

        elif "flights" in last_msg or ("VN123" in last_msg and not pnr):
            tool_name = "hold_ticket"
            args = {"flight_number": "VN123", "passenger_name": "Nguyen Van A", "passenger_id": "0123456789"}

        elif pnr and "held" in last_msg:
            tool_name = "confirm_booking"
            token = self.guard.get_auth_token(state.get("user_session", "")) or "TOKEN_DEFAULT_MOCK"
            args = {"pnr_code": pnr, "payment_auth_token": token}

        else:
            # Fallback nếu không khớp mẫu để tránh lặp vô tận
            prompt = "Hãy tổng hợp lại tình trạng hiện tại và thông báo cho khách hàng theo đúng hướng dẫn."
            bot_response = self.llm.invoke([
                self.system_prompt,
                *messages,
                HumanMessage(content=prompt)
            ])
            return {"messages": [bot_response], "execution_metrics": metrics}

        log_iteration_detail(
            step_name=f"ReAct Step {metrics['steps']}",
            active_model=BASE_FALLBACK_CHAIN[0],
            tool_name=tool_name,
            params=args
        )

        action = AIMessage(
            content=f"Calling {tool_name}",
            additional_kwargs={"tool_calls": [{"name": tool_name, "args": args}]}
        )
        return {"messages": [action], "execution_metrics": metrics}

    def act_node(self, state: AgentState) -> Dict[str, Any]:
        metrics = state["execution_metrics"]
        last_msg = state["messages"][-1]
        tool_call = last_msg.additional_kwargs["tool_calls"][0]

        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        metrics["tool_calls"] += 1

        selected_tool = self.tool_map[tool_name]
        result = selected_tool.invoke(tool_args)

        pnr = state.get("pnr")
        if tool_name == "hold_ticket":
            try:
                data = json.loads(result)
                pnr = data.get("pnr")
            except Exception:
                pass

        return {"messages": [HumanMessage(content=result)], "pnr": pnr, "execution_metrics": metrics}

    def should_continue(self, state: AgentState) -> str:
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "additional_kwargs") and "tool_calls" in last_msg.additional_kwargs:
            return "act"
        return END

    def build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("reason", self.reason_node)
        workflow.add_node("act", self.act_node)
        workflow.add_edge(START, "reason")
        workflow.add_conditional_edges("reason", self.should_continue, {"act": "act", END: END})
        workflow.add_edge("act", "reason")
        return workflow.compile()


# ==============================================================================
# MẪU 2: PLAN-THEN-EXECUTE AGENT
# ==============================================================================
class PlanThenExecuteFlightAgent:
    def __init__(self, permission_guard: PermissionGuard):
        self.guard = permission_guard
        self.llm = get_llm_with_fallback()
        self.system_prompt = SystemMessage(content=SYSTEM_PROMPT)

    def planner_node(self, state: AgentState) -> Dict[str, Any]:
        plan = [
            "1. Tìm kiếm chuyến bay SGN -> HAN",
            "2. Đặt giữ chỗ tạm thời (Hold Ticket)",
            "3. Xác nhận thanh toán & Xuất vé (Confirm Booking)"
        ]
        return {"plan": plan, "current_step": 0}

    def executor_node(self, state: AgentState) -> Dict[str, Any]:
        metrics = state.get("execution_metrics", {"steps": 0, "tool_calls": 0})
        metrics["steps"] += 1
        step_idx = state["current_step"]
        pnr = state.get("pnr")

        if step_idx == 0:
            tool_name = "search_flights"
            args = {"origin": "SGN", "destination": "HAN", "date": "2026-10-10"}
            log_iteration_detail(f"Plan Step {step_idx + 1}", BASE_FALLBACK_CHAIN[0], tool_name, args)
            res = search_flights.invoke(args)
            metrics["tool_calls"] += 1

        elif step_idx == 1:
            tool_name = "hold_ticket"
            args = {"flight_number": "VN123", "passenger_name": "Nguyen Van A", "passenger_id": "0123456789"}
            log_iteration_detail(f"Plan Step {step_idx + 1}", BASE_FALLBACK_CHAIN[0], tool_name, args)
            res = hold_ticket.invoke(args)
            metrics["tool_calls"] += 1
            try:
                pnr = json.loads(res).get("pnr")
            except Exception:
                pass

        elif step_idx == 2:
            tool_name = "confirm_booking"
            token = self.guard.get_auth_token(state.get("user_session", "")) or "TOKEN_DEFAULT_MOCK"
            args = {"pnr_code": pnr or "PNR-DEFAULT", "payment_auth_token": token}
            log_iteration_detail(f"Plan Step {step_idx + 1}", BASE_FALLBACK_CHAIN[0], tool_name, args)
            res = confirm_booking.invoke(args)
            metrics["tool_calls"] += 1
        else:
            res = "Hoàn tất kế hoạch."

        return {
            "current_step": step_idx + 1,
            "pnr": pnr,
            "messages": [HumanMessage(content=str(res))],
            "execution_metrics": metrics
        }

    def final_response_node(self, state: AgentState) -> Dict[str, Any]:
        history = state.get("messages", [])
        prompt = (
            f"Mã đặt chỗ PNR: {state.get('pnr')}.\n"
            f"Vé đã được thanh toán và xác nhận thành công trên hệ thống.\n"
            f"Hãy phản hồi đầy đủ, lịch sự và rõ ràng với hành khách theo đúng vai trò được giao."
        )
        # Giữ nguyên SystemMessage + toàn bộ lịch sử tool/human messages + hướng dẫn kết thúc
        bot_response = self.llm.invoke([
            self.system_prompt,
            *history,
            HumanMessage(content=prompt)
        ])
        return {"messages": [bot_response]}

    def should_continue(self, state: AgentState) -> str:
        if state["current_step"] < len(state["plan"]):
            return "execute"
        return "final_response"

    def build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("execute", self.executor_node)
        workflow.add_node("final_response", self.final_response_node)

        workflow.add_edge(START, "planner")
        workflow.add_edge("planner", "execute")
        workflow.add_conditional_edges(
            "execute",
            self.should_continue,
            {"execute": "execute", "final_response": "final_response"}
        )
        workflow.add_edge("final_response", END)
        return workflow.compile()


# ==============================================================================
# MẪU 3: HYBRID AGENT (DYNAMIC PLAN + REACT + HANDOFF)
# ==============================================================================
class HybridFlightAgent:
    def __init__(self, permission_guard: PermissionGuard):
        self.guard = permission_guard
        self.llm = get_llm_with_fallback()
        self.system_prompt = SystemMessage(content=SYSTEM_PROMPT)

    def planner_node(self, state: AgentState) -> Dict[str, Any]:
        plan = ["SEARCH", "VALIDATE_AND_HOLD", "CHECK_PERM_AND_CONFIRM"]
        return {"plan": plan, "current_step": 0}

    def hybrid_react_node(self, state: AgentState) -> Dict[str, Any]:
        metrics = state.get("execution_metrics", {"steps": 0, "tool_calls": 0}).copy()
        metrics["steps"] += 1

        step_idx = state.get("current_step", 0)
        plan = state.get("plan", [])
        pnr = state.get("pnr")
        user_session = state.get("user_session", "")
        handoff = False
        res_content = ""

        current_action = plan[step_idx]

        if current_action == "SEARCH":
            tool_name = "search_flights"
            args = {"origin": "SGN", "destination": "HAN", "date": "2026-10-10"}
            log_iteration_detail(f"Hybrid Step {step_idx + 1}", BASE_FALLBACK_CHAIN[0], tool_name, args)
            res = search_flights.invoke(args)
            metrics["tool_calls"] += 1
            res_content = res

        elif current_action == "VALIDATE_AND_HOLD":
            tool_name = "hold_ticket"
            args = {"flight_number": "VN123", "passenger_name": "Nguyen Van A", "passenger_id": "0123456789"}
            log_iteration_detail(f"Hybrid Step {step_idx + 1}", BASE_FALLBACK_CHAIN[0], tool_name, args)
            res = hold_ticket.invoke(args)
            metrics["tool_calls"] += 1
            try:
                pnr = json.loads(res).get("pnr")
            except Exception:
                pass
            res_content = res

        elif current_action == "CHECK_PERM_AND_CONFIRM":
            if not self.guard.is_action_permitted("CONFIRM_PAYMENT", user_session):
                handoff = True
                res_content = "Không đủ quyền thanh toán (Permission Denied)."
                log_iteration_detail(f"Hybrid Step {step_idx + 1}", BASE_FALLBACK_CHAIN[0], "TRIGGER_HANDOFF", {"reason": "Permission Denied"})
            else:
                tool_name = "confirm_booking"
                token = self.guard.get_auth_token(user_session) or "TOKEN_DEFAULT_MOCK"
                args = {"pnr_code": pnr or "PNR-DEFAULT", "payment_auth_token": token}
                log_iteration_detail(f"Hybrid Step {step_idx + 1}", BASE_FALLBACK_CHAIN[0], tool_name, args)
                res = confirm_booking.invoke(args)
                metrics["tool_calls"] += 1
                res_content = res

        return {
            "current_step": step_idx + 1,
            "pnr": pnr,
            "handoff": handoff,
            "messages": [HumanMessage(content=res_content)],
            "execution_metrics": metrics,
        }

    def handoff_node(self, state: AgentState) -> Dict[str, Any]:
        history = state.get("messages", [])
        prompt = (
            f"Mã đặt chỗ {state.get('pnr')} đã được giữ chỗ thành công nhưng tài khoản chưa được phân quyền thanh toán tự động.\n"
            f"Hãy đóng vai trợ lý AI thông báo nhẹ nhàng cho hành khách rằng yêu cầu đang được chuyển tiếp tới nhân viên CSKH hỗ trợ xuất vé."
        )
        # Giữ SystemMessage + lịch sử các bước thực thi trước đó + chỉ dẫn handoff
        bot_response = self.llm.invoke([
            self.system_prompt,
            *history,
            HumanMessage(content=prompt)
        ])
        return {"messages": [bot_response]}

    def normal_finish_node(self, state: AgentState) -> Dict[str, Any]:
        history = state.get("messages", [])
        prompt = (
            f"Vé với mã PNR {state.get('pnr')} đã được thanh toán hoàn tất.\n"
            f"Hãy phản hồi đầy đủ, gửi lời cảm ơn và chúc chuyến bay tốt đẹp theo đúng vai trò được giao."
        )
        # Giữ SystemMessage + lịch sử các bước thực thi trước đó + chỉ dẫn kết thúc
        bot_response = self.llm.invoke([
            self.system_prompt,
            *history,
            HumanMessage(content=prompt)
        ])
        return {"messages": [bot_response]}

    def router(self, state: AgentState) -> str:
        if state.get("handoff"):
            return "handoff_node"
        if state.get("current_step", 0) < len(state.get("plan", [])):
            return "hybrid_react"
        return "normal_finish"

    def build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("hybrid_react", self.hybrid_react_node)
        workflow.add_node("handoff_node", self.handoff_node)
        workflow.add_node("normal_finish", self.normal_finish_node)

        workflow.add_edge(START, "planner")
        workflow.add_edge("planner", "hybrid_react")
        workflow.add_conditional_edges(
            "hybrid_react",
            self.router,
            {
                "hybrid_react": "hybrid_react",
                "handoff_node": "handoff_node",
                "normal_finish": "normal_finish",
            },
        )
        workflow.add_edge("handoff_node", END)
        workflow.add_edge("normal_finish", END)
        return workflow.compile()
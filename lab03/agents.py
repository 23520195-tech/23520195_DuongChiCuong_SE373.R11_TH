import json
import operator
from typing import Dict, List, Any, Optional, TypedDict, Annotated

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END

from lab03.config import get_llm_with_fallback, BASE_FALLBACK_CHAIN
from lab03.tools import ALL_TOOLS, search_flights, hold_ticket, confirm_booking
from lab03.harness import PermissionGuard, HandoffManager


# Định nghĩa State chung cho các Agent trong LangGraph
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    plan: Optional[List[str]]
    current_step: int
    pnr: Optional[str]
    handoff: bool
    user_session: str
    execution_metrics: Dict[str, Any]


# Hàm hỗ trợ in Output chi tiết từng vòng lặp
def log_iteration_detail(step_name: str, active_model: str, tool_name: str, params: Dict[str, Any]):
    print(f"\n  ┌─── [VÒNG LẶP / BƯỚC: {step_name}] ──────────────────────────────────")
    print(f"  │ 🤖 Model đang sử dụng : {active_model}")
    print(f"  │ 🛠️  Hàm được gọi (Tool) : {tool_name}")
    print(f"  │ 📥 Tham số (Parameters): {json.dumps(params, ensure_ascii=False)}")
    print(f"  └────────────────────────────────────────────────────────────────────")


# ==============================================================================
# MẪU THIẾT KẾ 1: REACT AGENT
# ==============================================================================
class ReActFlightAgent:
    def __init__(self, permission_guard: PermissionGuard):
        self.guard = permission_guard
        self.llm = get_llm_with_fallback().bind_tools(ALL_TOOLS)
        self.tool_map = {t.name: t for t in ALL_TOOLS}

    def reason_node(self, state: AgentState) -> Dict[str, Any]:
        metrics = state.get("execution_metrics", {"steps": 0, "tool_calls": 0})
        metrics["steps"] += 1
        
        messages = state["messages"]
        last_msg = messages[-1].content
        
        # Mô phỏng quyết định suy luận của Agent
        if "Đặt vé" in last_msg or "Tìm vé" in last_msg:
            tool_name = "search_flights"
            args = {"origin": "SGN", "destination": "HAN", "date": "2026-10-10"}
        elif "flights" in last_msg:
            tool_name = "hold_ticket"
            args = {"flight_number": "VN123", "passenger_name": "Nguyen Van A", "passenger_id": "0123456789"}
        elif "PNR-" in last_msg:
            tool_name = "confirm_booking"
            token = self.guard.get_auth_token(state["user_session"])
            pnr = json.loads(last_msg).get("pnr")
            args = {"pnr_code": pnr, "payment_auth_token": token}
        else:
            action = AIMessage(content="Đã hoàn thành toàn bộ quy trình.")
            return {"messages": [action], "execution_metrics": metrics}

        log_iteration_detail(
            step_name=f"ReAct Step {metrics['steps']}",
            active_model=BASE_FALLBACK_CHAIN[0],
            tool_name=tool_name,
            params=args
        )

        action = AIMessage(
            content=f"Thực thi {tool_name}",
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
            pnr = json.loads(result).get("pnr")

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
# MẪU THIẾT KẾ 2: PLAN-THEN-EXECUTE AGENT
# ==============================================================================
class PlanThenExecuteFlightAgent:
    def __init__(self, permission_guard: PermissionGuard):
        self.guard = permission_guard

    def planner_node(self, state: AgentState) -> Dict[str, Any]:
        plan = [
            "1. Tìm kiếm chuyến bay SGN -> HAN",
            "2. Đặt giữ chỗ tạm thời (Hold Ticket)",
            "3. Xác nhận thanh toán & Xuất vé (Confirm Booking)"
        ]
        print(f"\n📋 [PLANNER] Đã lập kế hoạch gồm {len(plan)} bước:")
        for p in plan:
            print(f"   • {p}")
        return {"plan": plan, "current_step": 0, "messages": [AIMessage(content="Đã hoàn tất lập kế hoạch.")]}

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
            pnr = json.loads(res).get("pnr")

        elif step_idx == 2:
            tool_name = "confirm_booking"
            token = self.guard.get_auth_token(state["user_session"])
            args = {"pnr_code": pnr, "payment_auth_token": token}
            log_iteration_detail(f"Plan Step {step_idx + 1}", BASE_FALLBACK_CHAIN[0], tool_name, args)
            res = confirm_booking.invoke(args)
            metrics["tool_calls"] += 1

        else:
            res = "Đã thực hiện xong toàn bộ kế hoạch."

        return {
            "current_step": step_idx + 1,
            "pnr": pnr,
            "messages": [HumanMessage(content=res)],
            "execution_metrics": metrics
        }

    def should_continue(self, state: AgentState) -> str:
        if state["current_step"] < len(state["plan"]):
            return "execute"
        return END

    def build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("execute", self.executor_node)
        workflow.add_edge(START, "planner")
        workflow.add_edge("planner", "execute")
        workflow.add_conditional_edges("execute", self.should_continue, {"execute": "execute", END: END})
        return workflow.compile()


# ==============================================================================
# MẪU THIẾT KẾ 3: HYBRID AGENT (MẪU LAI: DYNAMIC PLAN + REACT + HANDOFF)
# ==============================================================================
class HybridFlightAgent:
    def __init__(self, permission_guard: PermissionGuard):
        self.guard = permission_guard

    def planner_node(self, state: AgentState) -> Dict[str, Any]:
        plan = ["SEARCH", "VALIDATE_AND_HOLD", "CHECK_PERM_AND_CONFIRM"]
        return {"plan": plan, "current_step": 0}

    def hybrid_react_node(self, state: AgentState) -> Dict[str, Any]:
        metrics = state.get("execution_metrics", {"steps": 0, "tool_calls": 0})
        metrics["steps"] += 1
        
        step_idx = state["current_step"]
        plan = state["plan"]
        pnr = state.get("pnr")
        handoff = False
        
        current_action = plan[step_idx]
        
        if current_action == "SEARCH":
            tool_name = "search_flights"
            args = {"origin": "SGN", "destination": "HAN", "date": "2026-10-10"}
            log_iteration_detail(f"Hybrid Dynamic Step {step_idx + 1}", BASE_FALLBACK_CHAIN[0], tool_name, args)
            res = search_flights.invoke(args)
            metrics["tool_calls"] += 1

        elif current_action == "VALIDATE_AND_HOLD":
            tool_name = "hold_ticket"
            args = {"flight_number": "VN123", "passenger_name": "Nguyen Van A", "passenger_id": "0123456789"}
            log_iteration_detail(f"Hybrid Dynamic Step {step_idx + 1}", BASE_FALLBACK_CHAIN[0], tool_name, args)
            res = hold_ticket.invoke(args)
            metrics["tool_calls"] += 1
            pnr = json.loads(res).get("pnr")

        elif current_action == "CHECK_PERM_AND_CONFIRM":
            if not self.guard.is_action_permitted("CONFIRM_PAYMENT", state["user_session"]):
                handoff = True
                res = "Không đủ quyền thanh toán."
                log_iteration_detail(f"Hybrid Step {step_idx + 1}", BASE_FALLBACK_CHAIN[0], "TRIGGER_HANDOFF", {"reason": "Permission Denied"})
            else:
                tool_name = "confirm_booking"
                token = self.guard.get_auth_token(state["user_session"])
                args = {"pnr_code": pnr, "payment_auth_token": token}
                log_iteration_detail(f"Hybrid Step {step_idx + 1}", BASE_FALLBACK_CHAIN[0], tool_name, args)
                res = confirm_booking.invoke(args)
                metrics["tool_calls"] += 1
        else:
            res = "Thành công"

        return {
            "current_step": step_idx + 1,
            "pnr": pnr,
            "handoff": handoff,
            "messages": [HumanMessage(content=res)],
            "execution_metrics": metrics
        }

    def router(self, state: AgentState) -> str:
        if state.get("handoff"):
            return "handoff_node"
        if state["current_step"] < len(state["plan"]):
            return "hybrid_react"
        return END

    def handoff_node(self, state: AgentState) -> Dict[str, Any]:
        handoff_data = HandoffManager.trigger_handoff("Chưa xác thực quyền thanh toán", state)
        return {"messages": [AIMessage(content=json.dumps(handoff_data, ensure_ascii=False))]}

    def build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("hybrid_react", self.hybrid_react_node)
        workflow.add_node("handoff_node", self.handoff_node)
        
        workflow.add_edge(START, "planner")
        workflow.add_edge("planner", "hybrid_react")
        workflow.add_conditional_edges("hybrid_react", self.router, {
            "hybrid_react": "hybrid_react",
            "handoff_node": "handoff_node",
            END: END
        })
        workflow.add_edge("handoff_node", END)
        return workflow.compile()
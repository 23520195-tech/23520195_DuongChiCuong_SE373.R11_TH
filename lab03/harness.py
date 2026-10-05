from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError
from lab03.tools import MOCK_BOOKINGS


# --- 1. RÀNG BUỘC DỮ LIỆU (DATA CONSTRAINTS) ---
class BookingConstraintSchema(BaseModel):
    """Mô hình Pydantic kiểm tra tính hợp lệ dữ liệu đầu vào."""
    origin: str = Field(..., min_length=3, max_length=3, description="Mã sân bay đi (VD: SGN)")
    destination: str = Field(..., min_length=3, max_length=3, description="Mã sân bay đến (VD: HAN)")
    max_budget: float = Field(..., gt=0, description="Ngân sách tối đa của khách hàng")
    passenger_name: str = Field(..., min_length=2, description="Tên hành khách")
    passenger_id: str = Field(..., min_length=6, description="Số CCCD/Hộ chiếu")


class FlightDataValidator:
    """Lớp kiểm tra dữ liệu đầu vào theo ràng buộc nghiệp vụ."""
    @staticmethod
    def validate_request(request_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        try:
            BookingConstraintSchema(**request_data)
            return True, None
        except ValidationError as e:
            return False, str(e)


# --- 2. KIỂM QUYỀN (PERMISSION CHECK) ---
class PermissionGuard:
    """Quản lý và kiểm tra quyền thao tác (đặc biệt đối với tác vụ thanh toán/tài chính)."""
    def __init__(self):
        self.authorized_tokens = {"USER_SESSION_8899": "AUTH_APPROVED_USER_TOKEN"}

    def is_action_permitted(self, action_type: str, user_session: str) -> bool:
        if action_type in ["SEARCH", "CHECK_DETAILS", "HOLD_TICKET"]:
            return True
        if action_type == "CONFIRM_PAYMENT":
            return user_session in self.authorized_tokens
        return False

    def get_auth_token(self, user_session: str) -> Optional[str]:
        return self.authorized_tokens.get(user_session, None)


# --- 3. BÀN GIAO (HANDOFF MECHANISM) ---
class HandoffManager:
    """Bàn giao quy trình cho nhân viên chăm sóc khách hàng (Human-in-the-loop) khi gặp sự cố."""
    @staticmethod
    def trigger_handoff(reason: str, state_summary: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "HANDOFF_TO_HUMAN",
            "reason": reason,
            "context": state_summary,
            "action_required": "Yêu cầu chuyên viên CSKH tiếp nhận và xử lý thủ công."
        }


# --- 4. TIÊU CHÍ HOÀN THÀNH KIỂM BẰNG CODE (CODE-BASED EVALUATOR) ---
class TaskCompletionEvaluator:
    """Kiểm tra hoàn thành nhiệm vụ tự động bằng mã nguồn (Code-based verification)."""
    @staticmethod
    def evaluate(pnr_code: str, target_constraints: BookingConstraintSchema) -> Dict[str, Any]:
        if not pnr_code or pnr_code not in MOCK_BOOKINGS:
            return {"success": False, "score": 0.0, "reason": f"Mã PNR '{pnr_code}' không hợp lệ hoặc không tồn tại trong CSDL."}
        
        booking = MOCK_BOOKINGS[pnr_code]
        
        # 1. Trạng thái thanh toán
        if booking.get("status") != "CONFIRMED" or not booking.get("payment_confirmed"):
            return {"success": False, "score": 0.3, "reason": "Chưa hoàn tất xác nhận thanh toán."}
        
        # 2. Kiểm tra ràng buộc ngân sách
        if booking["price"] > target_constraints.max_budget:
            return {"success": False, "score": 0.5, "reason": f"Giá vé ({booking['price']:,} VNĐ) vượt quá ngân sách ({target_constraints.max_budget:,} VNĐ)."}
        
        # 3. Kiểm tra đúng tên người bay
        if booking["passenger_name"].upper() != target_constraints.passenger_name.upper():
            return {"success": False, "score": 0.7, "reason": "Thông tin tên hành khách không khớp."}

        return {"success": True, "score": 1.0, "reason": "Hoàn thành đặt vé thành công và đáp ứng đầy đủ tất cả ràng buộc!"}
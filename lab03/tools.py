import json
import time
from typing import Dict, Any
from langchain_core.tools import tool

# Cơ sở dữ liệu giả lập chuyến bay
FLIGHT_DATABASE = [
    {
        "flight_number": "VN123",
        "airline": "Vietnam Airlines",
        "origin": "SGN",
        "destination": "HAN",
        "departure_time": "2026-10-10 08:00",
        "arrival_time": "2026-10-10 10:10",
        "price": 2100000,
        "seats_available": 5,
        "class": "Economy"
    },
    {
        "flight_number": "VJ456",
        "airline": "Vietjet Air",
        "origin": "SGN",
        "destination": "HAN",
        "departure_time": "2026-10-10 09:30",
        "arrival_time": "2026-10-10 11:40",
        "price": 1400000,
        "seats_available": 2,
        "class": "Economy"
    },
    {
        "flight_number": "QH789",
        "airline": "Bamboo Airways",
        "origin": "SGN",
        "destination": "DAD",
        "departure_time": "2026-10-10 14:00",
        "arrival_time": "2026-10-10 15:20",
        "price": 1800000,
        "seats_available": 10,
        "class": "Economy"
    }
]

# Lưu trữ các giao dịch giữ chỗ
MOCK_BOOKINGS: Dict[str, Dict[str, Any]] = {}


@tool
def search_flights(origin: str, destination: str, date: str) -> str:
    """Tìm kiếm chuyến bay theo mã sân bay đi (origin), sân bay đến (destination) và ngày khởi hành (date)."""
    results = [
        f for f in FLIGHT_DATABASE
        if f["origin"].upper() == origin.upper() and f["destination"].upper() == destination.upper()
    ]
    if not results:
        return json.dumps({"status": "error", "message": f"Không tìm thấy chuyến bay từ {origin} đến {destination}."})
    return json.dumps({"status": "success", "flights": results}, ensure_ascii=False)


@tool
def check_flight_details(flight_number: str) -> str:
    """Xem thông tin chi tiết và tình trạng ghế của một chuyến bay theo mã chuyến bay."""
    for f in FLIGHT_DATABASE:
        if f["flight_number"].upper() == flight_number.upper():
            return json.dumps({"status": "success", "flight": f}, ensure_ascii=False)
    return json.dumps({"status": "error", "message": f"Không tìm thấy chuyến bay {flight_number}."})


@tool
def hold_ticket(flight_number: str, passenger_name: str, passenger_id: str) -> str:
    """Giữ chỗ tạm thời cho khách hàng. Trả về pnr_code (mã đặt chỗ). Chưa trừ tiền."""
    for f in FLIGHT_DATABASE:
        if f["flight_number"].upper() == flight_number.upper():
            if f["seats_available"] <= 0:
                return json.dumps({"status": "error", "message": "Chuyến bay đã hết ghế."})
            
            pnr_code = f"PNR-{int(time.time() * 1000) % 1000000}"
            booking = {
                "pnr": pnr_code,
                "flight_number": flight_number,
                "passenger_name": passenger_name,
                "passenger_id": passenger_id,
                "price": f["price"],
                "status": "HELD",
                "payment_confirmed": False
            }
            MOCK_BOOKINGS[pnr_code] = booking
            return json.dumps({"status": "success", "pnr": pnr_code, "price": f["price"], "message": "Giữ chỗ thành công."}, ensure_ascii=False)
            
    return json.dumps({"status": "error", "message": "Mã chuyến bay không hợp lệ."})


@tool
def confirm_booking(pnr_code: str, payment_auth_token: str) -> str:
    """Xác nhận thanh toán và xuất vé chính thức. Yêu cầu mã thanh toán payment_auth_token hợp lệ."""
    if pnr_code not in MOCK_BOOKINGS:
        return json.dumps({"status": "error", "message": f"Mã PNR {pnr_code} không tồn tại."})
    
    if payment_auth_token != "AUTH_APPROVED_USER_TOKEN":
        return json.dumps({"status": "unauthorized", "message": "Thanh toán thất bại: Thiếu quyền thanh toán hoặc token không hợp lệ."})
    
    booking = MOCK_BOOKINGS[pnr_code]
    booking["status"] = "CONFIRMED"
    booking["payment_confirmed"] = True
    return json.dumps({"status": "success", "pnr": pnr_code, "message": "Đặt vé thành công và đã xuất vé!"}, ensure_ascii=False)


# Danh sách công cụ dùng chung
ALL_TOOLS = [search_flights, check_flight_details, hold_ticket, confirm_booking]
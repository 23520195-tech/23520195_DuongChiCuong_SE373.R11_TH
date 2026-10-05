# Cấu trúc thư mục

```
.
├── .env                        # File cấu hình API Key và Model mặc định (ở gốc dự án)
└── lab3/
    ├── __init__.py             # Đánh dấu module Python
    ├── config.py               # Tải .env và khởi tạo LLM với chính sách Fallback
    ├── harness.py              # Lớp Harness: Ràng buộc, kiểm quyền, bàn giao, kiểm định bằng code
    ├── tools.py                # Mock database & LangChain Tools
    ├── agents.py               # 3 Mẫu thiết kế Agent (ReAct, Plan-then-Execute, Lai) + In log chi tiết
    └── main.py                 # File thực thi benchmark & in kết quả so sánh
```
# Chạy code như sau.
Tạo và kích hoạt môi trường ảo (Virtual Environment)

```
python -m venv venv
.\venv\Scripts\activate
```

Sau đó tiến hành cài đặt môi trường bằng lệnh:

```
pip install -r requirements.txt
```

Kiểm tra và chạy thử dự án
```
python -m lab3.main
```
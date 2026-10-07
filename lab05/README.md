# BÁO CÁO BÀI TẬP: AGENTIC AI ENGINEERING - BT buổi 5
**Đề tài:** Bổ sung Tool tìm tài liệu (`list_files`) và Xây dựng Skill tra cứu chính sách (`refund-policy`)

---

## 📌 1. Vị trí file báo cáo và minh chứng thực nghiệm

Toàn bộ phân tích chi tiết, bảng đối chiếu trace sự kiện, dữ liệu token/thời gian chạy và ảnh chụp màn hình minh chứng cho từng trường hợp kiểm thử được lưu trữ tại:

* **Đường dẫn file báo cáo:** `./agent-tools-skills-lab/ANALYSIS/analysis.md`
[Xem chi tiết báo cáo tại analysis.md](./agent-tools-skills-lab/ANALYSIS/analysis.md)
* **Thư mục minh chứng hình ảnh:** `./agent-tools-skills-lab/ANALYSIS/` (`image-1.png` đến `image-14.png`)

---

## 📂 2. Cấu trúc thư mục nộp bài

Dự án được triển khai trên bản sao các stage theo đúng yêu cầu đề bài:

```text
agent-tools-skills-lab/
├── ANALYSIS/                       # Báo cáo thực nghiệm và minh chứng
│   ├── analysis.md                 # Báo cáo chi tiết kết quả chạy và trả lời câu hỏi
│   └── image-*.png                 # Ảnh chụp màn hình kết quả chat và trace
├── stage-00-chat/                  # Baseline: Xác định giới hạn ban đầu của Agent
├── stage-01-files/                 # Stage bổ sung & kiểm thử tool list_files
│   ├── tools/                      # Mã nguồn tool list_files và đăng ký schema
│   ├── test_tools.py               # Script unit test trực tiếp 4 kịch bản của tool
│   └── workspace/data/policies/    # Tài liệu chính sách mẫu
├── stage-02-skills/                # Stage tích hợp Tool + Skill refund-policy
│   ├── tools/                      # Tool list_files đã hoàn thiện
│   └── workspace/
│       ├── data/policies/          # 2 file chính sách (và kịch bản đổi tên file)
│       │   ├── policy-before-oct.md
│       │   └── policy-from-oct.md
│       └── skills/refund-policy/   # Thư mục Skill hoàn tiền
│           ├── SKILL.md            # Quy trình kiểm tra, tìm kiếm và áp dụng chính sách
│           └── references/
│               └── answer-template.md  # Template định

```

# Hướng dẫn thiết lập môi trường và chạy thực nghiệm

Lưu ý cấu hình biến môi trường (.env):
Trước khi chạy Agent, vui lòng tạo tệp .env tại thư mục gốc và cung cấp API Key:

## 🛠️ Cài đặt Môi trường & Thư viện

Dự án sử dụng Python 3.10+ và quản lý gói qua `pyproject.toml` / `uv.lock`. Thầy/Cô có thể cài đặt thư viện theo một trong hai cách dưới đây:

### Cách 1: Sử dụng `uv` (Khuyên dùng - Nhanh và đúng chuẩn theo project)
Nếu máy đã cài sẵn công cụ `uv`:
```bash
# 1. Đồng bộ và cài đặt toàn bộ thư viện từ file uv.lock
uv sync
```
Bước 1: Kích hoạt môi trường ảo

```
cd ./lab05/agent-tools-skills-lab
# Trên Windows (Git Bash)
source ./.venv/Scripts/activate

# Trên Linux / macOS
source ./.venv/bin/activate
```
Bước 3: Khởi chạy giao diện và kiểm thử Agent

Di chuyển vào stage hoàn thiện:
ví dụ:
```
cd ../stage-02-skills
streamlit run app.py
```


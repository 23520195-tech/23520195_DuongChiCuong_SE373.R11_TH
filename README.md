# BÁO CÁO TỔNG HỢP CÁC BÀI THỰC HÀNH AGENTIC AI ENGINEERING
**Môn học:** Agentic AI Engineering  
**Học viên thực hiện:** Dương Chí Cường  

---

## 🧭 LỜI MỞ ĐẦU & ĐIỀU HƯỚNG NHANH

Kính gửi Quý Thầy/Cô, repository này chứa toàn bộ mã nguồn, tài liệu thực nghiệm và báo cáo kết quả của các bài tập thực hành (Labs). Để thuận tiện cho việc kiểm tra và chấm điểm, Thầy/Cô có thể bấm trực tiếp vào các liên kết bên dưới để nhảy nhanh tới từng bài tập, tài liệu báo cáo hoặc file đính kèm:

* 📂 **Lab 03:** [Truy cập thư mục Lab 03](./lab03/) | [Xem Hướng dẫn & Báo cáo Lab 03](./lab03/README.md)
* 📂 **Lab 05:** [Truy cập thư mục Lab 05](./lab05/) | [Xem Hướng dẫn chạy Lab 05](./lab05/README.md) | [👉 Xem Báo cáo thực nghiệm (analysis.md)](./lab05/agent-tools-skills-lab/ANALYSIS/analysis.md)

---

## 🗂️ CẤU TRÚC TỔNG THỂ DỰ ÁN

```text
├── lab03/                                   # Bài thực hành Lab 03
│   ├── docs/                                # Tài liệu đề bài, slide hoặc PDF hướng dẫn
│   ├── README.md                            # Báo cáo và hướng dẫn chi tiết Lab 03
│   └── ...                                  # Mã nguồn của Lab 03
├── lab05/                                   # Bài thực hành Lab 05 (Tools & Skills)
│   └── agent-tools-skills-lab/
│       ├── ANALYSIS/                        # Thư mục lưu báo cáo & minh chứng Lab 05
│       │   ├── analysis.md                  # 👉 Báo cáo phân tích chi tiết các Stage
│       │   └── image-*.png                  # Ảnh chụp màn hình minh chứng (1 -> 14)
│       ├── stage-00-chat/                   # Baseline Agent (chưa có Tool & Skill)
│       ├── stage-01-files/                  # Agent tích hợp Tool list_files
│       ├── stage-02-skills/                 # Agent hoàn thiện Tool + Skill refund-policy
│       ├── pyproject.toml                   # Cấu hình gói và phụ thuộc (uv)
│       ├── uv.lock                          # Khóa phiên bản dependencies
│       └── README.md                        # Hướng dẫn chi tiết chạy Lab 05
├── .env.example                             # Mẫu khai báo biến môi trường (API Key)
├── requirements.txt                         # Danh sách thư viện Python tổng
└── README.md                                # File này (Báo cáo điều hướng tổng)
```
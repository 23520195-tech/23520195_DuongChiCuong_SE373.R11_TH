import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Tải các biến môi trường từ file .env ở gốc thư mục
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Danh sách danh định thứ tự fallback ưu tiên (3.5 -> 3.1 -> 2.5)
RAW_FALLBACK_CHAIN = [
    PRIMARY_MODEL,
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash",
    "gemini-2.5-flash",
]

# Loại bỏ các model trùng lặp nhưng vẫn giữ nguyên thứ tự ưu tiên
BASE_FALLBACK_CHAIN = []
for model_name in RAW_FALLBACK_CHAIN:
    if model_name not in BASE_FALLBACK_CHAIN:
        BASE_FALLBACK_CHAIN.append(model_name)


def get_llm_with_fallback():
    """
    Khởi tạo LLM chính cùng chuỗi Fallback tự động trong LangChain.
    Nếu model chính lỗi, hệ thống sẽ tự động thử các model tiếp theo theo đúng thứ tự ưu tiên.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("AIzaSy...your"):
        print("⚠️ [CẢNH BÁO] Chưa cấu hình GEMINI_API_KEY hợp lệ trong file .env!")

    llm_instances = [
        ChatGoogleGenerativeAI(
            model=m,
            google_api_key=GEMINI_API_KEY
        )
        for m in BASE_FALLBACK_CHAIN
    ]

    primary_llm = llm_instances[0]
    
    if len(llm_instances) > 1:
        # Cấu hình chuỗi Fallback tự động
        return primary_llm.with_fallbacks(llm_instances[1:])
    
    return primary_llm
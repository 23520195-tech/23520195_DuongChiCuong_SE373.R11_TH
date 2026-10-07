# Import hàm list_files từ file tool bạn đã viết
from tools import list_files

print("--- TH 1: Thư mục hợp lệ ---")
print(list_files.invoke({"path": "data/policies"}))

print("\n--- TH 2: Đường dẫn là File ---")
print(list_files.invoke({"path": "data/policies/policy-before-oct.md"}))

print("\n--- TH 3: Thư mục không tồn tại ---")
print(list_files.invoke({"path": "data/not_exist_folder"}))

print("\n--- TH 4: Đường dẫn vượt workspace ---")
print(list_files.invoke({"path": "../"}))
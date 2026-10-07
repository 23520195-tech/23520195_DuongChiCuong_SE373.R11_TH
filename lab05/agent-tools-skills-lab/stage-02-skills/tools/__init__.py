"""Tools đăng ký cho agent của project này."""

from tools.files import read_file, write_file
from tools.list_files import list_files  # <--- Bổ sung import này

__all__ = ["read_file", "write_file", "list_files"]  # <--- Thêm "list_files" vào đây
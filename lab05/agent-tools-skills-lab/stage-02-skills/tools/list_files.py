import os
from pathlib import Path
from langchain_core.tools import tool
from paths import WORKSPACE_DIR, resolve_workspace_path

@tool
def list_files(path: str) -> str:
    """Liệt kê các file và thư mục con trực tiếp trong một thư mục thuộc workspace.

    Args:
        path: Đường dẫn thư mục tương đối với workspace (ví dụ: 'data/policies').
    """
    try:
        # Giải mã và kiểm tra an toàn đường dẫn thuộc workspace
        target_path = resolve_workspace_path(path)

        if not target_path.exists():
            return f"Lỗi: Đường dẫn '{path}' không tồn tại."

        if not target_path.is_dir():
            return f"Lỗi: Đường dẫn '{path}' không phải là thư mục."

        items = []
        for entry in os.scandir(target_path):
            entry_path = Path(entry.path)
            rel_path = str(entry_path.relative_to(WORKSPACE_DIR)).replace("\\", "/")
            file_type = "directory" if entry.is_dir() else "file"
            items.append(f"- {entry.name} ({file_type}): {rel_path}")

        items.sort()
        return "\n".join(items) if items else "Thư mục rỗng."

    except ValueError as e:
        return f"Lỗi: Truy cập ngoài workspace bị từ chối ({str(e)})."
    except Exception as e:
        return f"Lỗi truy cập thư mục: {str(e)}"
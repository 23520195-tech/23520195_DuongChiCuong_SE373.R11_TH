"""Đường dẫn của project, resolve từ vị trí file này (không phụ thuộc thư mục terminal)."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
TRACES_DIR = PROJECT_ROOT / "traces"
FIXTURES_DIR = PROJECT_ROOT / "fixtures"
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
OUTPUT_SUBDIR = "output"
WORKSPACE_MARKER = ".lab-workspace"


def resolve_workspace_path(relative_path: str | Path) -> Path:
  """Chuyển đổi đường dẫn tương đối thành đường dẫn tuyệt đối an toàn trong workspace."""
  path = (WORKSPACE_DIR / relative_path).resolve()
  if not str(path).startswith(str(WORKSPACE_DIR.resolve())):
    raise ValueError(f"Đường dẫn '{relative_path}' nằm ngoài workspace!")
  return path
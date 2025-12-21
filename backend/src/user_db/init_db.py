"""Create all tables in the database."""

from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (three levels up from user_db/)
_project_root = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_project_root / ".env")

from . import models  # noqa: F401, E402 ensures models load so metadata has tables
from .user_db import Base, engine  # noqa: E402


def main() -> None:
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    main()

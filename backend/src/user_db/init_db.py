"""Create all tables in the database."""

from dotenv import load_dotenv

load_dotenv()  # Load .env before importing modules that require env vars

from . import models  # noqa: F401, E402 ensures models load so metadata has tables
from .user_db import Base, engine  # noqa: E402


def main() -> None:
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    main()

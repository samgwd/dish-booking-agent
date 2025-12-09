"""Create all tables in the database."""

from . import models  # noqa: F401 ensures models load so metadata has tables
from .user_db import Base, engine


def main() -> None:
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    main()

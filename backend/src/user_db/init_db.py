"""Create all tables in the database."""

from .user_db import Base, engine


def main() -> None:
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    main()

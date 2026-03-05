from __future__ import annotations

from app import db


def main() -> None:
    db_path = db.default_db_path()
    if db_path.exists():
        db_path.unlink()

    conn = db.connect(db_path)
    try:
        db.init_db(conn)
        db.seed_if_empty(conn)
    finally:
        conn.close()

    print(f"Database reset at {db_path}")


if __name__ == "__main__":
    main()

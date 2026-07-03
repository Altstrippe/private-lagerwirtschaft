from sqlalchemy import text

from app.db.session import engine


def main() -> None:
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "select table_name "
                "from information_schema.tables "
                "where table_schema = 'public' "
                "order by table_name"
            )
        ).fetchall()

    print(result)


if __name__ == "__main__":
    main()
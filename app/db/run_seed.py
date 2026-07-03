from app.db.seed import run_seed
from app.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as session:
        run_seed(session)


if __name__ == "__main__":
    main()
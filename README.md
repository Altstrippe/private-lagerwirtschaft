\# Private Lagerwirtschaft



Schlanke private Lager-App mit Streamlit, SQLAlchemy und Neon/PostgreSQL.



\## Stack



\- Python 3.12

\- Streamlit

\- PostgreSQL / Neon

\- SQLAlchemy

\- Alembic

\- pytest

\- ruff

\- black



\## Start lokal



```bash

pip install -r requirements.txt

alembic upgrade head

python -m app.db.run\_seed

streamlit run app/app.py


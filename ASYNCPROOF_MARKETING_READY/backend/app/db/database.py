import os
from pathlib import Path
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is required. Configure PostgreSQL before starting the backend.")
    # Render/Heroku sometimes provide postgres://, psycopg2 accepts it but postgresql:// is clearer.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def get_conn():
    return psycopg2.connect(_database_url(), cursor_factory=RealDictCursor)


def init_db():
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)


def row_to_dict(row):
    return dict(row) if row else None

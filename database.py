"""Conexión a PostgreSQL (Aiven) y creación de tablas."""
import os

import psycopg
from psycopg.rows import dict_row

# La URI completa la da Aiven ("Service URI") y se guarda en una variable de entorno.
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta la variable de entorno DATABASE_URL")

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id            SERIAL PRIMARY KEY,
    nombre        TEXT NOT NULL,
    correo        TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sesiones (
    token      TEXT PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS series (
    id                 SERIAL PRIMARY KEY,
    usuario_id         INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo             TEXT NOT NULL,
    genero             TEXT NOT NULL,
    plataforma         TEXT NOT NULL DEFAULT '',
    temporadas_totales INTEGER NOT NULL,
    temporadas_vistas  INTEGER NOT NULL DEFAULT 0,
    favorita           BOOLEAN NOT NULL DEFAULT FALSE
);
"""


def init_db() -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(SCHEMA)


def get_db():
    """Dependencia de FastAPI: una conexión por petición (cada fila llega como diccionario)."""
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn


import os
import ssl
from urllib.parse import unquote, urlparse

import pymysql
from pymysql.cursors import DictCursor


DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta la variable de entorno DATABASE_URL")

_url = urlparse(DATABASE_URL)

TABLAS = [
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        nombre        VARCHAR(60)  NOT NULL,
        correo        VARCHAR(254) NOT NULL UNIQUE,
        password_hash VARCHAR(200) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sesiones (
        token      VARCHAR(64) PRIMARY KEY,
        usuario_id INT NOT NULL,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS series (
        id                 INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id         INT NOT NULL,
        titulo             VARCHAR(100) NOT NULL,
        genero             VARCHAR(40)  NOT NULL,
        plataforma         VARCHAR(40)  NOT NULL DEFAULT '',
        temporadas_totales INT NOT NULL,
        temporadas_vistas  INT NOT NULL DEFAULT 0,
        favorita           BOOLEAN NOT NULL DEFAULT FALSE,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    )
    """,
]


def _contexto_ssl() -> ssl.SSLContext:
    """Aiven exige SSL. Si defines DB_CA_CERT (ruta al ca.pem) se verifica el certificado."""
    ca = os.environ.get("DB_CA_CERT")
    if ca:
        return ssl.create_default_context(cafile=ca)
    contexto = ssl.create_default_context()
    contexto.check_hostname = False
    contexto.verify_mode = ssl.CERT_NONE
    return contexto


def _conectar() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=_url.hostname,
        port=_url.port or 3306,
        user=unquote(_url.username or ""),
        password=unquote(_url.password or ""),
        database=_url.path.lstrip("/"),
        cursorclass=DictCursor,
        charset="utf8mb4",
        ssl=_contexto_ssl(),
        autocommit=False,
        connect_timeout=30,
    )


def init_db() -> None:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            for sentencia in TABLAS:
                cur.execute(sentencia)
        conn.commit()
    finally:
        conn.close()


def get_db():
    """Dependencia de FastAPI: una conexión por petición (cada fila llega como diccionario)."""
    conn = _conectar()
    try:
        yield conn
    finally:
        conn.close()
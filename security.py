"""Contraseñas, tokens y usuario autenticado."""
import hashlib
import hmac
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymysql.connections import Connection

from database import get_db

_ITERACIONES = 100_000
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), _ITERACIONES
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, almacenado: str) -> bool:
    salt, digest = almacenado.split("$")
    candidato = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), _ITERACIONES
    ).hex()
    return hmac.compare_digest(candidato, digest)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def get_current_user(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Connection = Depends(get_db),
) -> dict:
    """Devuelve el usuario dueño del token Bearer o responde 401."""
    if credenciales is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token")
    with db.cursor() as cur:
        cur.execute(
            "SELECT u.* FROM usuarios u JOIN sesiones s ON s.usuario_id = u.id "
            "WHERE s.token = %s",
            (credenciales.credentials,),
        )
        usuario = cur.fetchone()
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")
    return usuario
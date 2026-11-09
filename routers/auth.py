"""POST /register y POST /login."""
from fastapi import APIRouter, Depends, HTTPException, status
from pymysql.connections import Connection
from pymysql.err import IntegrityError

from database import get_db
from schemas import AuthOut, LoginIn, RegisterIn
from security import hash_password, new_token, verify_password

router = APIRouter(tags=["auth"])


def _respuesta_con_token(db: Connection, usuario: dict) -> AuthOut:
    token = new_token()
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO sesiones (token, usuario_id) VALUES (%s, %s)",
            (token, usuario["id"]),
        )
    db.commit()
    return AuthOut(
        token=token,
        user={"id": usuario["id"], "nombre": usuario["nombre"], "correo": usuario["correo"]},
    )


@router.post("/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def register(datos: RegisterIn, db: Connection = Depends(get_db)):
    correo = datos.correo.strip().lower()
    nombre = datos.nombre.strip()
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO usuarios (nombre, correo, password_hash) VALUES (%s, %s, %s)",
                (nombre, correo, hash_password(datos.contrasena)),
            )
            nuevo_id = cur.lastrowid
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya está registrado")
    return _respuesta_con_token(db, {"id": nuevo_id, "nombre": nombre, "correo": correo})


@router.post("/login", response_model=AuthOut)
def login(datos: LoginIn, db: Connection = Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            "SELECT * FROM usuarios WHERE correo = %s", (datos.correo.strip().lower(),)
        )
        usuario = cur.fetchone()
    if usuario is None or not verify_password(datos.contrasena, usuario["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o contraseña incorrectos")
    return _respuesta_con_token(db, usuario)
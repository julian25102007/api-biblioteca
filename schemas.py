"""Modelos de entrada y salida de la API (validación con Pydantic)."""
from pydantic import BaseModel, Field, model_validator

CORREO_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


# ---------- Autenticación ----------
class RegisterIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=60)
    correo: str = Field(pattern=CORREO_REGEX)
    contrasena: str = Field(min_length=8)


class LoginIn(BaseModel):
    correo: str
    contrasena: str


class UserOut(BaseModel):
    id: int
    nombre: str
    correo: str


class AuthOut(BaseModel):
    token: str
    user: UserOut


# ---------- Series ----------
class SerieIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=100)
    genero: str = Field(min_length=1, max_length=40)
    plataforma: str = Field(default="", max_length=40)
    temporadas_totales: int = Field(ge=1, le=50)
    temporadas_vistas: int = Field(default=0, ge=0)
    favorita: bool = False

    @model_validator(mode="after")
    def vistas_no_mayor_que_totales(self):
        if self.temporadas_vistas > self.temporadas_totales:
            raise ValueError("temporadas_vistas no puede superar temporadas_totales")
        return self


class SerieOut(SerieIn):
    id: int

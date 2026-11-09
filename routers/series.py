"""CRUD de series. Cada usuario solo ve y modifica sus propias series."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pymysql.connections import Connection

from database import get_db
from schemas import SerieIn, SerieOut
from security import get_current_user

router = APIRouter(prefix="/series", tags=["series"])


def _a_salida(fila: dict) -> SerieOut:
    return SerieOut(**{**fila, "favorita": bool(fila["favorita"])})


def _o_404(fila: dict | None) -> dict:
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Serie no encontrada")
    return fila


def _leer(db: Connection, serie_id: int, usuario_id: int) -> dict | None:
    with db.cursor() as cur:
        cur.execute(
            "SELECT * FROM series WHERE id = %s AND usuario_id = %s", (serie_id, usuario_id)
        )
        return cur.fetchone()


@router.get("", response_model=list[SerieOut])
def listar(db: Connection = Depends(get_db), usuario=Depends(get_current_user)):
    with db.cursor() as cur:
        cur.execute(
            "SELECT * FROM series WHERE usuario_id = %s ORDER BY id DESC", (usuario["id"],)
        )
        filas = cur.fetchall()
    return [_a_salida(f) for f in filas]


@router.get("/{serie_id}", response_model=SerieOut)
def obtener(serie_id: int, db: Connection = Depends(get_db), usuario=Depends(get_current_user)):
    return _a_salida(_o_404(_leer(db, serie_id, usuario["id"])))


@router.post("", response_model=SerieOut, status_code=status.HTTP_201_CREATED)
def crear(datos: SerieIn, db: Connection = Depends(get_db), usuario=Depends(get_current_user)):
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO series (usuario_id, titulo, genero, plataforma, "
            "temporadas_totales, temporadas_vistas, favorita) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (usuario["id"], datos.titulo.strip(), datos.genero.strip(), datos.plataforma.strip(),
            datos.temporadas_totales, datos.temporadas_vistas, datos.favorita),
        )
        nuevo_id = cur.lastrowid
    db.commit()
    return _a_salida(_o_404(_leer(db, nuevo_id, usuario["id"])))


@router.put("/{serie_id}", response_model=SerieOut)
def actualizar(serie_id: int, datos: SerieIn, db: Connection = Depends(get_db),
            usuario=Depends(get_current_user)):
    with db.cursor() as cur:
        cur.execute(
            "UPDATE series SET titulo = %s, genero = %s, plataforma = %s, "
            "temporadas_totales = %s, temporadas_vistas = %s, favorita = %s "
            "WHERE id = %s AND usuario_id = %s",
            (datos.titulo.strip(), datos.genero.strip(), datos.plataforma.strip(),
            datos.temporadas_totales, datos.temporadas_vistas, datos.favorita,
            serie_id, usuario["id"]),
        )
    db.commit()
    return _a_salida(_o_404(_leer(db, serie_id, usuario["id"])))


@router.delete("/{serie_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(serie_id: int, db: Connection = Depends(get_db), usuario=Depends(get_current_user)):
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM series WHERE id = %s AND usuario_id = %s", (serie_id, usuario["id"])
        )
        borradas = cur.rowcount
    db.commit()
    if borradas == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Serie no encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
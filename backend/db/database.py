import sqlite3
from pathlib import Path
from contextlib import closing

from backend.config import settings
from backend.modules.review.schemas import ReviewCorrection
from backend.modules.triage.schemas import TriageRequest, TriageResult


def connect_database(
    database_path: str | Path | None = None,
) -> sqlite3.Connection:
    # Utilizamos la ruta recibida o la configurada en el archivo .env.
    path = Path(database_path or settings.database_path).resolve()

    # Abrimos una conexión con la base de datos SQLite.
    connection = sqlite3.connect(path)

    # Esto permite consultar las columnas por nombre.
    connection.row_factory = sqlite3.Row

    return connection

# Definimos la estructura de la tabla donde guardaremos las solicitudes.
CREATE_TRIAGE_REQUESTS_TABLE = """
CREATE TABLE IF NOT EXISTS triage_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    message TEXT NOT NULL,
    user_role TEXT NOT NULL,

    llm_category TEXT NOT NULL,
    llm_urgency TEXT NOT NULL,
    llm_responsible_party TEXT NOT NULL,
    llm_summary TEXT NOT NULL,
    llm_justification TEXT NOT NULL,
    llm_department TEXT,

    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    attempts INTEGER NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    latency_ms REAL NOT NULL,
    estimated_cost_usd REAL NOT NULL,

    review_status TEXT NOT NULL DEFAULT 'pending',

    final_category TEXT,
    final_urgency TEXT,
    final_responsible_party TEXT,
    final_summary TEXT,
    final_justification TEXT,
    final_department TEXT,
    review_notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TEXT
)
"""

# Guardamos cada notificación o derivación realizada después de la revisión.
CREATE_DISPATCHES_TABLE = """
CREATE TABLE IF NOT EXISTS dispatches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    dispatch_type TEXT NOT NULL,
    destination TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES triage_requests(id)
)
"""


def initialize_database(
    database_path: str | Path | None = None,
) -> None:
    # Cerramos la conexión después de crear y confirmar la tabla.
    with closing(connect_database(database_path)) as connection:
        connection.execute(CREATE_TRIAGE_REQUESTS_TABLE)
        connection.execute(CREATE_DISPATCHES_TABLE)

        # Añadimos las columnas nuevas también a bases de datos ya existentes.
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(triage_requests)"
            ).fetchall()
        }

        if "llm_justification" not in columns:
            connection.execute(
                """
                ALTER TABLE triage_requests
                ADD COLUMN llm_justification TEXT NOT NULL
                DEFAULT 'Justificación no disponible para registros anteriores.'
                """
            )

        if "final_justification" not in columns:
            connection.execute(
                """
                ALTER TABLE triage_requests
                ADD COLUMN final_justification TEXT
                """
            )

        connection.commit()

def save_triage_request(
    request: TriageRequest,
    result: TriageResult,
    database_path: str | Path | None = None,
) -> int:
    # Nos aseguramos de que la tabla exista antes de guardar la solicitud.
    initialize_database(database_path)

    # Las métricas están agrupadas dentro del resultado del triaje.
    metrics = result.metrics

    with closing(connect_database(database_path)) as connection:
        cursor = connection.execute(
            """
            INSERT INTO triage_requests (
                message,
                user_role,
                llm_category,
                llm_urgency,
                llm_responsible_party,
                llm_summary,
                llm_justification,
                llm_department,
                provider,
                model,
                attempts,
                input_tokens,
                output_tokens,
                latency_ms,
                estimated_cost_usd
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.message,
                request.user_role,
                result.category,
                result.urgency,
                result.responsible_party,
                result.summary,
                result.justification,
                result.department,
                metrics.provider,
                metrics.model,
                metrics.attempts,
                metrics.input_tokens,
                metrics.output_tokens,
                metrics.latency_ms,
                metrics.estimated_cost_usd,
            ),
        )

        connection.commit()
        request_id = cursor.lastrowid

    # Devolvemos el identificador asignado por SQLite.
    return int(request_id)


def get_triage_request(
    request_id: int,
    database_path: str | Path | None = None,
) -> dict | None:
    # Comprobamos que la tabla exista antes de buscar la solicitud.
    initialize_database(database_path)

    with closing(connect_database(database_path)) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM triage_requests
            WHERE id = ?
            """,
            (request_id,),
        ).fetchone()

    # Si el identificador no existe, devolvemos None.
    if row is None:
        return None

    # Si existe, convertimos la fila en un diccionario.
    return dict(row)


def list_pending_requests(
    database_path: str | Path | None = None,
) -> list[dict]:
    # Comprobamos que la tabla exista antes de consultar sus registros.
    initialize_database(database_path)

    with closing(connect_database(database_path)) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM triage_requests
            WHERE review_status = 'pending'
            ORDER BY created_at ASC, id ASC
            """
        ).fetchall()

    # Convertimos todas las filas de SQLite en diccionarios.
    return [dict(row) for row in rows]


def list_completed_requests(
    database_path: str | Path | None = None,
) -> list[dict]:
    """Devuelve las solicitudes que ya han sido revisadas."""

    # Nos aseguramos de que la tabla exista antes de consultarla.
    initialize_database(database_path)

    with closing(connect_database(database_path)) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM triage_requests
            WHERE review_status IN ('approved', 'corrected')
            ORDER BY reviewed_at DESC, id DESC
            """
        ).fetchall()

    # Convertimos las filas de SQLite en diccionarios.
    return [dict(row) for row in rows]


def approve_triage_request(
    request_id: int,
    database_path: str | Path | None = None,
) -> bool:
    initialize_database(database_path)

    with closing(connect_database(database_path)) as connection:
        cursor = connection.execute(
            """
            UPDATE triage_requests
            SET
                review_status = 'approved',
                final_category = llm_category,
                final_urgency = llm_urgency,
                final_responsible_party = llm_responsible_party,
                final_summary = llm_summary,
                final_justification = llm_justification,
                final_department = llm_department,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND review_status = 'pending'
            """,
            (request_id,),
        )

        connection.commit()
        was_updated = cursor.rowcount == 1

    return was_updated


def correct_triage_request(
    request_id: int,
    correction: ReviewCorrection,
    database_path: str | Path | None = None,
) -> bool:
    initialize_database(database_path)

    with closing(connect_database(database_path)) as connection:
        cursor = connection.execute(
            """
            UPDATE triage_requests
            SET
                review_status = 'corrected',
                final_category = ?,
                final_urgency = ?,
                final_responsible_party = ?,
                final_summary = ?,
                final_justification = ?,
                final_department = ?,
                review_notes = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND review_status = 'pending'
            """,
            (
                correction.category,
                correction.urgency,
                correction.responsible_party,
                correction.summary,
                correction.justification,
                correction.department,
                correction.review_notes,
                request_id,
            ),
        )

        connection.commit()
        was_updated = cursor.rowcount == 1

    return was_updated


def save_dispatch(
    request_id: int,
    dispatch_type: str,
    destination: str,
    message: str,
    status: str = "new",
    database_path: str | Path | None = None,
) -> int:
    # Guardamos una notificación al anfitrión o una derivación interna.
    initialize_database(database_path)

    with closing(connect_database(database_path)) as connection:
        cursor = connection.execute(
            """
            INSERT INTO dispatches (
                request_id,
                dispatch_type,
                destination,
                message,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                request_id,
                dispatch_type,
                destination,
                message,
                status,
            ),
        )

        connection.commit()
        return cursor.lastrowid

def list_dispatches(
    database_path: str | Path | None = None,
) -> list[dict]:
    # Recuperamos las derivaciones más recientes primero.
    initialize_database(database_path)

    with closing(connect_database(database_path)) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM dispatches
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def update_dispatch_status(
    dispatch_id: int,
    status: str,
    database_path: str | Path | None = None,
) -> bool:
    # Actualizamos el estado de una solicitud dentro de su bandeja.
    initialize_database(database_path)

    with closing(connect_database(database_path)) as connection:
        cursor = connection.execute(
            """
            UPDATE dispatches
            SET status = ?
            WHERE id = ?
            """,
            (
                status,
                dispatch_id,
            ),
        )

        connection.commit()

    return cursor.rowcount == 1
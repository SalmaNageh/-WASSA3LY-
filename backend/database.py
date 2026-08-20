
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent / "parking.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        # Vehicles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER UNIQUE,
                plate_number TEXT,
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Parking Spaces
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_spaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                space_number INTEGER UNIQUE,
                coordinates TEXT,
                status TEXT DEFAULT 'available'
            )
        """)

        # Parking Sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER,
                plate_number TEXT,
                parking_space_id INTEGER,
                entry_time TEXT,
                exit_time TEXT,
                duration_minutes REAL,
                fee REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
                FOREIGN KEY (parking_space_id) REFERENCES parking_spaces(id)
            )
        """)

        # VIP
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vip (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT UNIQUE,
                name TEXT,
                phone TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def add_vehicle(vehicle_id, plate_number=None, confidence=None):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO vehicles (vehicle_id, plate_number, confidence)
            VALUES (?, ?, ?)
            ON CONFLICT(vehicle_id)
            DO UPDATE SET
                plate_number = excluded.plate_number,
                confidence = excluded.confidence
        """, (vehicle_id, plate_number, confidence))

def add_parking_space(space_number, coordinates, status="available"):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO parking_spaces
            (space_number, coordinates, status)
            VALUES (?, ?, ?)
            ON CONFLICT(space_number)
            DO UPDATE SET
                coordinates = excluded.coordinates,
                status = excluded.status
        """, (space_number, coordinates, status))

def update_space_status(space_number, status):
    with get_connection() as conn:
        conn.execute("""
            UPDATE parking_spaces
            SET status = ?
            WHERE space_number = ?
        """, (status, space_number))


def add_parking_session(
    vehicle_id,
    plate_number,
    parking_space_id=None,
    entry_time=None,
    status="active"
):
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO parking_sessions
            (
                vehicle_id,
                plate_number,
                parking_space_id,
                entry_time,
                status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            vehicle_id,
            plate_number,
            parking_space_id,
            entry_time,
            status
        ))

        return cursor.lastrowid


def close_parking_session(session_id, exit_time, duration_minutes, fee):
    with get_connection() as conn:
        conn.execute("""
            UPDATE parking_sessions
            SET
                exit_time = ?,
                duration_minutes = ?,
                fee = ?,
                status = 'completed'
            WHERE id = ?
        """, (
            exit_time,
            duration_minutes,
            fee,
            session_id
        ))


def add_vip(plate_number, name=None, phone=None):
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO vip
            (plate_number, name, phone)
            VALUES (?, ?, ?)
        """, (plate_number, name, phone))


def is_vip(plate_number):
    with get_connection() as conn:
        result = conn.execute("""
            SELECT 1
            FROM vip
            WHERE plate_number = ?
            LIMIT 1
        """, (plate_number,)).fetchone()

        return result is not None


def get_active_sessions():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT *
            FROM parking_sessions
            WHERE status = 'active'
            ORDER BY entry_time
        """).fetchall()

        return [dict(row) for row in rows]


def get_parking_history():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT *
            FROM parking_sessions
            ORDER BY entry_time DESC
        """).fetchall()

        return [dict(row) for row in rows]


def get_revenue():
    with get_connection() as conn:
        result = conn.execute("""
            SELECT COALESCE(SUM(fee), 0)
            FROM parking_sessions
            WHERE status = 'completed'
        """).fetchone()

        return result[0]


def get_occupancy():
    with get_connection() as conn:
        total = conn.execute("""
            SELECT COUNT(*)
            FROM parking_spaces
        """).fetchone()[0]

        occupied = conn.execute("""
            SELECT COUNT(*)
            FROM parking_spaces
            WHERE status = 'occupied'
        """).fetchone()[0]

        available = total - occupied

        occupancy_rate = (
            (occupied / total) * 100
            if total > 0
            else 0
        )

        return {
            "total": total,
            "occupied": occupied,
            "available": available,
            "occupancy_rate": round(occupancy_rate, 2)
        }


# Initialize database when this file is imported
init_db()
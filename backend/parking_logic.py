from datetime import datetime
from database import get_connection


# ============================================================
# CONFIGURATION
# ============================================================

REGULAR_FEE_PER_HOUR = 20
VIP_FEE_PER_HOUR = 0


# ============================================================
# VIP
# ============================================================

def is_vip(plate_number):
    """Check whether a plate number belongs to a VIP vehicle."""

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM vip
            WHERE plate_number = ?
            LIMIT 1
            """,
            (plate_number,)
        )

        result = cursor.fetchone()

    return result is not None


# ============================================================
# ENTER
# ============================================================

def start_parking_session(
    vehicle_id,
    plate_number,
    parking_space
):
    """Start a new parking session."""

    now = datetime.now().isoformat()

    vip = is_vip(plate_number)

    with get_connection() as conn:
        cursor = conn.cursor()

        # ----------------------------------------------------
        # Check if vehicle already has an active session
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM parking_sessions
            WHERE plate_number = ?
            AND exit_time IS NULL
            AND status = 'active'
            """,
            (plate_number,)
        )

        existing_session = cursor.fetchone()

        if existing_session:
            return {
                "success": False,
                "message": "Vehicle already has an active parking session.",
                "plate_number": plate_number
            }

        # ----------------------------------------------------
        # Check parking space
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id, status
            FROM parking_spaces
            WHERE space_number = ?
            """,
            (parking_space,)
        )

        space = cursor.fetchone()

        if not space:
            return {
                "success": False,
                "message": "Parking space does not exist.",
                "parking_space": parking_space
            }

        space_id = space["id"]

        if space["status"] == "occupied":
            return {
                "success": False,
                "message": "Parking space is already occupied.",
                "parking_space": parking_space
            }

        # ----------------------------------------------------
        # Add / Update vehicle
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO vehicles (
                vehicle_id,
                plate_number
            )
            VALUES (?, ?)
            ON CONFLICT(vehicle_id)
            DO UPDATE SET
                plate_number = excluded.plate_number
            """,
            (
                vehicle_id,
                plate_number
            )
        )

        # ----------------------------------------------------
        # Create parking session
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO parking_sessions (
                vehicle_id,
                plate_number,
                parking_space_id,
                entry_time,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                vehicle_id,
                plate_number,
                space_id,
                now,
                "active"
            )
        )

        session_id = cursor.lastrowid

        # ----------------------------------------------------
        # Mark parking space as occupied
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE parking_spaces
            SET status = 'occupied'
            WHERE id = ?
            """,
            (space_id,)
        )

    return {
        "success": True,
        "session_id": session_id,
        "vehicle_id": vehicle_id,
        "plate_number": plate_number,
        "parking_space": parking_space,
        "entry_time": now,
        "vip": vip,
        "status": "active"
    }


# ============================================================
# EXIT
# ============================================================

def end_parking_session(plate_number):
    """End active parking session and calculate duration and fee."""

    exit_time = datetime.now()

    with get_connection() as conn:
        cursor = conn.cursor()

        # ----------------------------------------------------
        # Find active session
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                vehicle_id,
                parking_space_id,
                entry_time
            FROM parking_sessions
            WHERE plate_number = ?
            AND exit_time IS NULL
            AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
            """,
            (plate_number,)
        )

        session = cursor.fetchone()

        if not session:
            return {
                "success": False,
                "message": "No active parking session found.",
                "plate_number": plate_number
            }

        session_id = session["id"]
        vehicle_id = session["vehicle_id"]
        parking_space_id = session["parking_space_id"]

        entry_time = datetime.fromisoformat(
            session["entry_time"]
        )

        # ----------------------------------------------------
        # Get parking space number
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT space_number
            FROM parking_spaces
            WHERE id = ?
            """,
            (parking_space_id,)
        )

        space = cursor.fetchone()

        if space:
            parking_space = space["space_number"]
        else:
            parking_space = None

        # ----------------------------------------------------
        # Check VIP
        # ----------------------------------------------------

        vip = is_vip(plate_number)

        # ----------------------------------------------------
        # Calculate duration
        # ----------------------------------------------------

        duration_seconds = (
            exit_time - entry_time
        ).total_seconds()

        duration_minutes = duration_seconds / 60

        # ----------------------------------------------------
        # Calculate fee
        # ----------------------------------------------------

        if vip:
            fee = VIP_FEE_PER_HOUR

        else:
            # Minimum one hour charge
            hours = max(
                1,
                duration_seconds / 3600
            )

            fee = round(
                hours * REGULAR_FEE_PER_HOUR
            )

        exit_time_str = exit_time.isoformat()

        # ----------------------------------------------------
        # Update parking session
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE parking_sessions
            SET
                exit_time = ?,
                duration_minutes = ?,
                fee = ?,
                status = 'completed'
            WHERE id = ?
            """,
            (
                exit_time_str,
                duration_minutes,
                fee,
                session_id
            )
        )

        # ----------------------------------------------------
        # Free parking space
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE parking_spaces
            SET status = 'available'
            WHERE id = ?
            """,
            (parking_space_id,)
        )

    return {
        "success": True,
        "session_id": session_id,
        "vehicle_id": vehicle_id,
        "plate_number": plate_number,
        "parking_space": parking_space,
        "entry_time": entry_time.isoformat(),
        "exit_time": exit_time_str,
        "duration_minutes": round(
            duration_minutes,
            2
        ),
        "vip": vip,
        "fee": fee,
        "status": "completed"
    }


# ============================================================
# PARKING STATUS
# ============================================================

def get_parking_status():

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM parking_spaces
            """
        )

        total = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM parking_spaces
            WHERE status = 'occupied'
            """
        )

        occupied = cursor.fetchone()[0]

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
        "occupancy_rate": round(
            occupancy_rate,
            2
        )
    }


# ============================================================
# PARKING HISTORY
# ============================================================

def get_parking_history(limit=100):

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                ps.id,
                ps.vehicle_id,
                ps.plate_number,
                spaces.space_number,
                ps.entry_time,
                ps.exit_time,
                ps.duration_minutes,
                ps.fee,
                ps.status
            FROM parking_sessions ps
            LEFT JOIN parking_spaces spaces
                ON ps.parking_space_id = spaces.id
            ORDER BY ps.id DESC
            LIMIT ?
            """,
            (limit,)
        )

        rows = cursor.fetchall()

    history = []

    for row in rows:

        plate_number = row["plate_number"]

        history.append({
            "session_id": row["id"],
            "vehicle_id": row["vehicle_id"],
            "plate_number": plate_number,
            "parking_space": row["space_number"],
            "entry_time": row["entry_time"],
            "exit_time": row["exit_time"],
            "duration_minutes": row["duration_minutes"],
            "vip": is_vip(plate_number),
            "fee": row["fee"],
            "status": row["status"]
        })

    return history


# ============================================================
# REVENUE
# ============================================================

def get_total_revenue():

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COALESCE(SUM(fee), 0)
            FROM parking_sessions
            WHERE status = 'completed'
            """
        )

        revenue = cursor.fetchone()[0]

    return revenue


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n===== PARKING STATUS =====")

    status = get_parking_status()

    print("Total:", status["total"])
    print("Occupied:", status["occupied"])
    print("Available:", status["available"])
    print(
        "Occupancy Rate:",
        status["occupancy_rate"],
        "%"
    )

    print("\n===== TOTAL REVENUE =====")

    revenue = get_total_revenue()

    print("Revenue:", revenue)
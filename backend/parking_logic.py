from datetime import datetime
from backend.database import get_connection

# ============================================================
# CONFIGURATION
# ============================================================

REGULAR_FEE_PER_HOUR = 20
VIP_FEE_PER_HOUR = 40


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
# VEHICLE ID
# ============================================================

def get_or_create_vehicle_id(plate_number):
    """
    Return the existing vehicle ID for a plate.
    If the vehicle does not exist, create a new ID.
    """

    plate_number = str(
        plate_number
    ).strip().upper()

    with get_connection() as conn:

        cursor = conn.cursor()

        # ----------------------------------------------------
        # Check existing vehicle
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT vehicle_id
            FROM vehicles
            WHERE plate_number = ?
            LIMIT 1
            """,
            (plate_number,)
        )

        vehicle = cursor.fetchone()

        if vehicle:

            return vehicle["vehicle_id"]

        # ----------------------------------------------------
        # Generate new vehicle ID
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT COALESCE(MAX(vehicle_id), 0) + 1
            FROM vehicles
            """
        )

        vehicle_id = cursor.fetchone()[0]

        # ----------------------------------------------------
        # Create vehicle
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO vehicles (
                vehicle_id,
                plate_number
            )
            VALUES (?, ?)
            """,
            (
                vehicle_id,
                plate_number
            )
        )

    return vehicle_id


# ============================================================
# FIND AVAILABLE PARKING SPACE
# ============================================================

def get_available_parking_space():
    """
    Return the first available parking space.
    """

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                space_number
            FROM parking_spaces
            WHERE status = 'available'
            ORDER BY id ASC
            LIMIT 1
            """
        )

        space = cursor.fetchone()

    if not space:
        return None

    return {
        "id": space["id"],
        "space_number": space["space_number"]
    }


# ============================================================
# ENTER
# ============================================================

def start_parking_session(plate_number):
    """
    Start a new parking session automatically.

    Vehicle ID:
        Automatically assigned based on license plate.

    Parking Space:
        Automatically assigned from available spaces.
    """

    plate_number = str(
        plate_number
    ).strip().upper()

    if not plate_number:

        return {
            "success": False,
            "message": "License plate is required."
        }

    now = datetime.now().isoformat()

    vip = is_vip(
        plate_number
    )

    # --------------------------------------------------------
    # Check existing active session
    # --------------------------------------------------------

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                vehicle_id,
                parking_space_id
            FROM parking_sessions
            WHERE plate_number = ?
            AND exit_time IS NULL
            AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
            """,
            (plate_number,)
        )

        existing_session = cursor.fetchone()

    if existing_session:

        return {
            "success": False,
            "message": (
                "Vehicle already has "
                "an active parking session."
            ),
            "plate_number": plate_number,
            "vehicle_id": existing_session["vehicle_id"]
        }

    # --------------------------------------------------------
    # Get / create vehicle ID
    # --------------------------------------------------------

    vehicle_id = get_or_create_vehicle_id(
        plate_number
    )

    # --------------------------------------------------------
    # Find available parking space
    # --------------------------------------------------------

    space = get_available_parking_space()

    if not space:

        return {
            "success": False,
            "message": "No available parking spaces.",
            "plate_number": plate_number,
            "vehicle_id": vehicle_id
        }

    space_id = space["id"]

    parking_space = space[
        "space_number"
    ]

    # --------------------------------------------------------
    # Create session
    # --------------------------------------------------------

    with get_connection() as conn:

        cursor = conn.cursor()

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
        # Mark space occupied
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
    """
    End active parking session using license plate.
    """

    plate_number = str(
        plate_number
    ).strip().upper()

    exit_time = datetime.now()

    # --------------------------------------------------------
    # Find active session
    # --------------------------------------------------------

    with get_connection() as conn:

        cursor = conn.cursor()

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
            "message": (
                "No active parking session found."
            ),
            "plate_number": plate_number
        }

    session_id = session["id"]

    vehicle_id = session[
        "vehicle_id"
    ]

    parking_space_id = session[
        "parking_space_id"
    ]

    entry_time = datetime.fromisoformat(
        session["entry_time"]
    )

    # --------------------------------------------------------
    # Get parking space number
    # --------------------------------------------------------

    with get_connection() as conn:

        cursor = conn.cursor()

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

        parking_space = space[
            "space_number"
        ]

    else:

        parking_space = None

    # --------------------------------------------------------
    # VIP
    # --------------------------------------------------------

    vip = is_vip(
        plate_number
    )

    # --------------------------------------------------------
    # Duration
    # --------------------------------------------------------

    duration_seconds = (
        exit_time - entry_time
    ).total_seconds()

    duration_minutes = (
        duration_seconds / 60
    )

    # --------------------------------------------------------
    # Fee
    # --------------------------------------------------------

    hours = max(
        1,
        duration_seconds / 3600
    )

    if vip:

        fee = round(
            hours * VIP_FEE_PER_HOUR
        )

    else:

        fee = round(
            hours * REGULAR_FEE_PER_HOUR
        )

    exit_time_str = (
        exit_time.isoformat()
    )

    # --------------------------------------------------------
    # Update session
    # --------------------------------------------------------

    with get_connection() as conn:

        cursor = conn.cursor()

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
        occupied / total * 100
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

        plate_number = row[
            "plate_number"
        ]

        history.append({

            "session_id":
                row["id"],

            "vehicle_id":
                row["vehicle_id"],

            "plate_number":
                plate_number,

            "parking_space":
                row["space_number"],

            "entry_time":
                row["entry_time"],

            "exit_time":
                row["exit_time"],

            "duration_minutes":
                row["duration_minutes"],

            "vip":
                is_vip(plate_number),

            "fee":
                row["fee"],

            "status":
                row["status"]
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
# SYNC PARKING OCCUPANCY
# ============================================================

def sync_parking_occupancy(occupied_spaces):
    """
    Synchronize parking space status with YOLO.
    """

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT space_number
            FROM parking_spaces
            """
        )

        spaces = cursor.fetchall()

        for space in spaces:

            space_number = space[
                "space_number"
            ]

            if space_number in occupied_spaces:

                status = "occupied"

            else:

                status = "available"

            cursor.execute(
                """
                UPDATE parking_spaces
                SET status = ?
                WHERE space_number = ?
                """,
                (
                    status,
                    space_number
                )
            )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n===== PARKING STATUS ====="
    )

    status = get_parking_status()

    print(
        "Total:",
        status["total"]
    )

    print(
        "Occupied:",
        status["occupied"]
    )

    print(
        "Available:",
        status["available"]
    )

    print(
        "Occupancy Rate:",
        status["occupancy_rate"],
        "%"
    )

    print(
        "\n===== TOTAL REVENUE ====="
    )

    revenue = get_total_revenue()

    print(
        "Revenue:",
        revenue
    )
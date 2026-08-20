from backend.parking_logic import (
    start_parking_session,
    end_parking_session,
    get_parking_status,
    get_parking_history,
    get_total_revenue,
    sync_parking_occupancy
)

from backend.database import get_connection
# ============================================================
# VEHICLE ENTRY
# ============================================================

def process_member2_entry(plate_number):
    """
    Process vehicle entry.

    Plate number:
        Detected automatically by ALPR.

    Vehicle ID:
        Generated automatically.

    Parking Space:
        Selected automatically.
    """

    if not plate_number:

        return {
            "success": False,
            "message": "License plate number is required."
        }

    plate_number = str(
        plate_number
    ).strip().upper()

    return start_parking_session(
        plate_number
    )


# ============================================================
# VEHICLE EXIT
# ============================================================

def process_member2_exit(plate_number):
    """
    Process vehicle exit using license plate.
    """

    if not plate_number:

        return {
            "success": False,
            "message": "License plate number is required."
        }

    plate_number = str(
        plate_number
    ).strip().upper()

    return end_parking_session(
        plate_number
    )


# ============================================================
# PARKING OCCUPANCY
# ============================================================

def update_parking_occupancy(
    occupied_spaces
):

    return sync_parking_occupancy(
        occupied_spaces
    )


# ============================================================
# PARKING STATUS
# ============================================================

def get_current_status():

    return get_parking_status()


# ============================================================
# PARKING HISTORY
# ============================================================

def get_history(
    limit=100
):

    return get_parking_history(
        limit=limit
    )


# ============================================================
# REVENUE
# ============================================================

def get_revenue():

    return get_total_revenue()


# ============================================================
# ACTIVE VEHICLES
# ============================================================

def get_active_vehicles():

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                ps.id AS session_id,
                ps.vehicle_id,
                ps.plate_number,
                spaces.space_number,
                ps.entry_time,
                ps.status

            FROM parking_sessions ps

            LEFT JOIN parking_spaces spaces
                ON ps.parking_space_id = spaces.id

            WHERE ps.status = 'active'
            AND ps.exit_time IS NULL

            ORDER BY ps.entry_time DESC
            """
        )

        rows = cursor.fetchall()

    vehicles = []

    for row in rows:

        vehicles.append(
            {
                "session_id":
                    row["session_id"],

                "vehicle_id":
                    row["vehicle_id"],

                "plate_number":
                    row["plate_number"],

                "parking_space":
                    row["space_number"],

                "entry_time":
                    row["entry_time"],

                "status":
                    row["status"]
            }
        )

    return vehicles


# ============================================================
# GET VEHICLE BY PLATE
# ============================================================

def get_vehicle_by_plate(
    plate_number
):

    if not plate_number:
        return None

    plate_number = str(
        plate_number
    ).strip().upper()

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                vehicle_id,
                plate_number

            FROM vehicles

            WHERE plate_number = ?

            LIMIT 1
            """,
            (plate_number,)
        )

        vehicle = cursor.fetchone()

    if not vehicle:
        return None

    return {
        "vehicle_id":
            vehicle["vehicle_id"],

        "plate_number":
            vehicle["plate_number"]
    }


# ============================================================
# GET CURRENT VEHICLE SESSION
# ============================================================

def get_vehicle_current_session(
    plate_number
):

    if not plate_number:
        return None

    plate_number = str(
        plate_number
    ).strip().upper()

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                ps.id AS session_id,
                ps.vehicle_id,
                ps.plate_number,
                spaces.space_number,
                ps.entry_time,
                ps.status

            FROM parking_sessions ps

            LEFT JOIN parking_spaces spaces
                ON ps.parking_space_id = spaces.id

            WHERE ps.plate_number = ?

            AND ps.status = 'active'

            AND ps.exit_time IS NULL

            ORDER BY ps.id DESC

            LIMIT 1
            """,
            (plate_number,)
        )

        session = cursor.fetchone()

    if not session:
        return None

    return {
        "session_id":
            session["session_id"],

        "vehicle_id":
            session["vehicle_id"],

        "plate_number":
            session["plate_number"],

        "parking_space":
            session["space_number"],

        "entry_time":
            session["entry_time"],

        "status":
            session["status"]
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n===== CURRENT STATUS ====="
    )

    print(
        get_current_status()
    )

    print(
        "\n===== AVAILABLE SPACE ====="
    )

    print(
        get_available_parking_space()
    )

    print(
        "\n===== ACTIVE VEHICLES ====="
    )

    print(
        get_active_vehicles()
    )

    print(
        "\n===== TEST ENTRY ====="
    )

    result = process_member2_entry(
        "TEST123"
    )

    print(
        result
    )

    print(
        "\n===== STATUS AFTER ENTRY ====="
    )

    print(
        get_current_status()
    )

    print(
        "\n===== TEST CURRENT SESSION ====="
    )

    print(
        get_vehicle_current_session(
            "TEST123"
        )
    )

    print(
        "\n===== TEST EXIT ====="
    )

    result = process_member2_exit(
        "TEST123"
    )

    print(
        result
    )

    print(
        "\n===== FINAL STATUS ====="
    )

    print(
        get_current_status()
    )
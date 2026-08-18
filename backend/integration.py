from parking_logic import (
    start_parking_session,
    end_parking_session,
    get_parking_status,
    get_parking_history,
    get_total_revenue
)


# ============================================================
# MEMBER 2 → MEMBER 3
# VEHICLE ENTRY
# ============================================================

def process_member2_entry(
    vehicle_id,
    plate_number,
    parking_space
):
    """
    Process vehicle entry data received from Member 2 / Integration.

    Parameters:
        vehicle_id: Tracking ID of the vehicle
        plate_number: Plate number detected by OCR
        parking_space: Selected available parking space
    """

    return start_parking_session(
        vehicle_id=vehicle_id,
        plate_number=plate_number,
        parking_space=parking_space
    )


# ============================================================
# MEMBER 2 → MEMBER 3
# VEHICLE EXIT
# ============================================================

def process_member2_exit(plate_number):
    """
    Process vehicle exit using the detected plate number.
    """

    return end_parking_session(
        plate_number=plate_number
    )


# ============================================================
# PARKING STATUS
# ============================================================

def get_current_status():
    """
    Return current parking occupancy information.
    """

    return get_parking_status()


# ============================================================
# PARKING HISTORY
# ============================================================

def get_history(limit=100):
    """
    Return parking history.
    """

    return get_parking_history(limit=limit)


# ============================================================
# REVENUE
# ============================================================

def get_revenue():
    """
    Return total parking revenue.
    """

    return get_total_revenue()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n===== CURRENT PARKING STATUS =====")

    print(get_current_status())

    print("\n===== TEST ENTER =====")

    enter_result = process_member2_entry(
        vehicle_id=999,
        plate_number="TEST123",
        parking_space=1
    )

    print(enter_result)

    print("\n===== STATUS AFTER ENTER =====")

    print(get_current_status())

    print("\n===== TEST EXIT =====")

    exit_result = process_member2_exit(
        plate_number="TEST123"
    )

    print(exit_result)

    print("\n===== FINAL STATUS =====")

    print(get_current_status())

    print("\n===== PARKING HISTORY =====")

    print(get_history())

    print("\n===== TOTAL REVENUE =====")

    print(get_revenue())
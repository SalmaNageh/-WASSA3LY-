import json
from database import add_parking_space


def load_parking_spaces(json_path="parking_spots.json"):

    with open(json_path, "r", encoding="utf-8") as file:
        spots = json.load(file)

    for i, coordinates in enumerate(spots, start=1):

        add_parking_space(
            space_number=i,
            coordinates=json.dumps(coordinates),
            status="available"
        )

    print(f"✅ Added {len(spots)} parking spaces to database.")


if __name__ == "__main__":
    load_parking_spaces()
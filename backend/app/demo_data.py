from datetime import datetime, timedelta, timezone
from decimal import Decimal


LANES = [
    ("Kansas City, MO", "Minneapolis, MN", "Dry Van", Decimal("1900"), 438, "Paper products", "FCFS pickup."),
    ("Dallas, TX", "Atlanta, GA", "Dry Van", Decimal("2400"), 781, "Packaged food", "No-touch freight. Appointment required."),
    ("Chicago, IL", "Denver, CO", "Reefer", Decimal("2850"), 1004, "Dairy", "Temp setpoint 34F."),
    ("Houston, TX", "New Orleans, LA", "Flatbed", Decimal("1500"), 347, "Industrial equipment", "Straps required."),
    ("Indianapolis, IN", "Nashville, TN", "Dry Van", Decimal("1400"), 290, "Beverages", "Pallet exchange."),
    ("Los Angeles, CA", "Phoenix, AZ", "Dry Van", Decimal("1650"), 372, "Consumer goods", "Drop and hook."),
    ("Memphis, TN", "Charlotte, NC", "Flatbed", Decimal("2200"), 625, "Steel coils", "Tarp required."),
    ("Columbus, OH", "Newark, NJ", "Dry Van", Decimal("2050"), 526, "Retail freight", "Live unload."),
    ("Seattle, WA", "Sacramento, CA", "Reefer", Decimal("2750"), 755, "Fresh produce", "Continuous run."),
    ("Salt Lake City, UT", "Las Vegas, NV", "Reefer", Decimal("1700"), 420, "Frozen food", "Frozen goods at -10F."),
    ("Atlanta, GA", "Orlando, FL", "Dry Van", Decimal("1850"), 438, "Home goods", "No-touch freight."),
    ("St. Louis, MO", "Omaha, NE", "Dry Van", Decimal("1600"), 432, "Retail displays", "Live load."),
    ("Cleveland, OH", "Pittsburgh, PA", "Flatbed", Decimal("1250"), 135, "Machinery", "Chains required."),
    ("Portland, OR", "Boise, ID", "Reefer", Decimal("2100"), 430, "Produce", "Pre-cool required."),
    ("San Antonio, TX", "Oklahoma City, OK", "Dry Van", Decimal("1750"), 467, "Packaged goods", "Drop trailer available."),
    ("Phoenix, AZ", "Albuquerque, NM", "Dry Van", Decimal("1550"), 418, "Electronics", "Appointment delivery."),
    ("Detroit, MI", "Milwaukee, WI", "Dry Van", Decimal("1700"), 374, "Auto parts", "Driver assist unload."),
    ("Raleigh, NC", "Richmond, VA", "Reefer", Decimal("1450"), 171, "Pharma", "Temp setpoint 40F."),
    ("Birmingham, AL", "Jacksonville, FL", "Flatbed", Decimal("1900"), 438, "Lumber", "Tarp required."),
    ("Denver, CO", "Cheyenne, WY", "Dry Van", Decimal("1200"), 102, "Office supplies", "Same day delivery."),
    ("Fresno, CA", "Reno, NV", "Reefer", Decimal("2300"), 310, "Fresh fruit", "Continuous temp tracking."),
    ("Louisville, KY", "Cincinnati, OH", "Dry Van", Decimal("1100"), 99, "Parcel freight", "Drop and hook."),
]


def build_demo_loads(base_time: datetime | None = None) -> list[dict]:
    now = base_time or datetime.now(timezone.utc)
    loads: list[dict] = []

    # Preserve original demo IDs for known lanes.
    original_ids = {
        0: "LD-1007",
        1: "LD-1001",
        2: "LD-1002",
        3: "LD-1008",
        4: "LD-1009",
        5: "LD-1003",
        6: "LD-1004",
        7: "LD-1005",
        8: "LD-1006",
        9: "LD-1010",
    }

    for lane_index, lane in enumerate(LANES):
        origin, destination, equipment, base_rate, miles, commodity, notes = lane
        copies = 5 if lane_index < 5 else 2
        for copy_index in range(copies):
            if copy_index == 0 and lane_index in original_ids:
                load_id = original_ids[lane_index]
            else:
                load_id = f"LD-{2000 + lane_index * 10 + copy_index}"

            pickup = now + timedelta(days=1 + ((lane_index + copy_index) % 5), hours=6 + copy_index * 2)
            delivery = pickup + timedelta(hours=max(8, int(miles / 45) + 8))
            rate = base_rate + Decimal(copy_index * 35) + Decimal((lane_index % 3) * 25)
            weight = 24000 + ((lane_index * 1700 + copy_index * 2200) % 19000)

            loads.append(
                {
                    "load_id": load_id,
                    "origin": origin,
                    "destination": destination,
                    "pickup_datetime": pickup,
                    "delivery_datetime": delivery,
                    "equipment_type": equipment,
                    "loadboard_rate": rate,
                    "notes": notes,
                    "weight": weight,
                    "commodity_type": commodity,
                    "num_of_pieces": 10 + ((lane_index + copy_index) % 24),
                    "miles": miles,
                    "dimensions": "53ft trailer" if equipment in {"Dry Van", "Reefer"} else "48ft flatbed",
                    "status": "available",
                }
            )

    return loads

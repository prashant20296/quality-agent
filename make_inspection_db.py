import sqlite3, random, datetime

random.seed(42)

stations = {
    "Welding Cell 1": ("Loader frame cross member", "Porosity"),
    "Welding Cell 2": ("Rear axle housing", "Incomplete penetration"),
    "CNC-1": ("Transmission shaft", "Diameter out of tolerance"),
    "CNC-2": ("Hydraulic pump housing", "Burrs"),
    "Paint Line": ("Front fender", "Paint adhesion failure"),
    "Assembly A": ("Wiring harness connector", "Connector not seated"),
    "Hydraulic Test": ("Lift cylinder hose assembly", "Oil leak"),
}

start = datetime.date(2026, 9, 1)
rows = []
for d in range(60):
    day = start + datetime.timedelta(days=d)
    for station, (part, defect) in stations.items():
        for shift in ("A", "B", "C"):
            inspected = random.randint(80, 120)
            rate = 0.015
            if station == "Paint Line":
                rate = 0.03
            if station == "Welding Cell 2" and shift == "C" and d >= 40:
                rate = 0.08  # the hidden problem
            rejected = sum(random.random() < rate for _ in range(inspected))
            rows.append((day.isoformat(), station, part, shift,
                         inspected, rejected, defect))

conn = sqlite3.connect("inspection.db")
conn.execute("DROP TABLE IF EXISTS inspections")
conn.execute("""CREATE TABLE inspections (
    id INTEGER PRIMARY KEY, date TEXT, station TEXT, part_name TEXT,
    shift TEXT, inspected INTEGER, rejected INTEGER, defect_type TEXT)""")
conn.executemany(
    "INSERT INTO inspections (date, station, part_name, shift, inspected, rejected, defect_type) "
    "VALUES (?,?,?,?,?,?,?)", rows)
conn.commit()
print("created inspection.db with", len(rows), "rows")
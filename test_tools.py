from tools import search_ncr, query_inspection_data

print("--- Reject rate by station, last 30 days ---")
print(query_inspection_data.invoke({"sql": """
SELECT station, ROUND(SUM(rejected)*100.0/SUM(inspected), 2) AS reject_pct
FROM inspections
WHERE date > date((SELECT MAX(date) FROM inspections), '-30 day')
GROUP BY station ORDER BY reject_pct DESC"""}))

print("\n--- Welding Cell 2 by shift since 2026-10-11 ---")
print(query_inspection_data.invoke({"sql": """
SELECT shift, ROUND(SUM(rejected)*100.0/SUM(inspected), 2) AS reject_pct
FROM inspections
WHERE station = 'Welding Cell 2' AND date >= '2026-10-11'
GROUP BY shift"""}))

print("\n--- Safety check: this must be refused ---")
print(query_inspection_data.invoke({"sql": "DELETE FROM inspections"}))

print("\n--- NCR search ---")
print(search_ncr.invoke({"query": "weld penetration problem"})[:400])
import os, json, time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

PROMPT = """Generate 5 realistic but FICTIONAL non-conformance reports (NCR) for a
tractor manufacturing plant (areas: welding, machining, painting, assembly,
hydraulics, supplier parts). Return a JSON list. Each item has keys:
ncr_id, date, area, part_name, defect_description, quantity_affected,
containment_action, root_cause, corrective_action, preventive_action.
Make root causes specific (e.g. worn fixture, wrong torque setting, supplier
heat-treatment variation). Use a different mix of areas and defects each time.
Batch number: {batch}"""

def get_batch(batch, max_tries=6):
    for attempt in range(1, max_tries + 1):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=PROMPT.format(batch=batch),
                config={"response_mime_type": "application/json"},
            )
            return json.loads(resp.text)
        except Exception as e:
            wait = 10 * attempt  # 10s, 20s, 30s...
            print(f"  batch {batch} attempt {attempt} failed: {str(e)[:80]}")
            if attempt == max_tries:
                raise
            print(f"  retrying in {wait}s...")
            time.sleep(wait)

os.makedirs("data", exist_ok=True)
records = []
for batch in range(1, 9):  # 8 calls x 5 = 40 records
    records.extend(get_batch(batch))
    print(f"batch {batch} done, total {len(records)}")
    time.sleep(5)

for i, r in enumerate(records, 1):
    r["ncr_id"] = f"NCR-2026-{i:03d}"

with open("data/ncr_records.json", "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2)
print("saved", len(records), "records")
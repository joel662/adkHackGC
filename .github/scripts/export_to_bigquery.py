import os
from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client()

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
table_id = f"{project_id}.devops_logs.test_results"

with open("test_output.log", "r") as f:
    output = f.read()

row = {
    "file_path": "CI Workflow Bootstrap",
    "language": "mixed",
    "test_output": output[:5000],
    "deps": "auto",
    "review_summary": "{}",
    "timestamp": datetime.utcnow()
}

errors = client.insert_rows_json(table_id, [row])
if errors:
    print("❌ BigQuery insert failed:", errors)
else:
    print("✅ BigQuery logging successful.")
    print("📊 Logged to BigQuery.")
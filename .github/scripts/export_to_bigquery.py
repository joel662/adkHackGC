import os
from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client()
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
table_id = f"{project_id}.devops_logs.test_results"

row = {
    "file_path": "CI Pipeline",
    "language": "n/a",
    "test_output": "CI completed without test execution.",
    "deps": "none",
    "review_summary": "{}",
    "timestamp": datetime.utcnow()
}

errors = client.insert_rows_json(table_id, [row])
if errors:
    print("❌ BigQuery insert failed:", errors)
else:
    print("✅ Logged CI event to BigQuery.")


from google.cloud import bigquery
from datetime import datetime, timezone
import json
from config import PROJECT_ID

bq_client = bigquery.Client()

def log_to_bigquery(finding: dict):
    table_id = f"{PROJECT_ID}.devops_logs.security_findings"
    row = {
        "file_path": finding["file_path"],
        "language": finding["language"],
        "vulnerabilities": json.dumps(finding.get("vulnerabilities", {})),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    errors = bq_client.insert_rows_json(table_id, [row])
    if errors:
        print("❌ Failed to log to BigQuery:", errors)
    else:
        print("✅ Logged finding to BigQuery.")

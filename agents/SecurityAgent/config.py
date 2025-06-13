import os
from dotenv import load_dotenv
from google.cloud import bigquery
from datetime import datetime
import json

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env.local'))
load_dotenv(dotenv_path=env_path)

PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
SECURITY_SUBSCRIPTION_ID = os.getenv("SECURITY_SUBSCRIPTION_ID", "security_agent_sub")

if not PROJECT_ID:
    raise EnvironmentError("❌ PROJECT_ID is not set in .env.local")

# BigQuery client for logging
bq_client = bigquery.Client()

def log_to_bigquery(finding: dict):
    table_id = f"{PROJECT_ID}.devops_logs.security_findings"
    row = {
        "file_path": finding["file_path"],
        "language": finding["language"],
        "vulnerabilities": json.dumps(finding.get("vulnerabilities", {})),
        "timestamp": datetime.utcnow()
    }
    errors = bq_client.insert_rows_json(table_id, [row])
    if errors:
        print("❌ Failed to log to BigQuery:", errors)
    else:
        print("✅ Logged finding to BigQuery.")

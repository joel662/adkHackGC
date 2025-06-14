import json
from datetime import datetime, timezone
from google.cloud import bigquery
from config import PROJECT_ID

bq_client = bigquery.Client()

def log_test_result(data: dict):
    """Logs a detailed test result with optional LLM summary."""
    table_id = f"{PROJECT_ID}.devops_logs.test_results"
    row = {
        "file_path": data.get("file_path"),
        "language": data.get("language"),
        "test_output": data.get("test_output", "")[:5000],
        "deps": ", ".join(data.get("dependencies", [])),
        "review_summary": json.dumps(data.get("review_summary", {})),
        "llm_summary": data.get("summary", ""),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    errors = bq_client.insert_rows_json(table_id, [row])
    if errors:
        print("❌ Failed to log test result:", errors)
    else:
        print("📊 Test result logged to BigQuery.")

def log_cicd_event(meta: dict):
    """Logs a high-level CI/CD event for tracking deployments or workflows."""
    table_id = f"{PROJECT_ID}.devops_logs.cicd_events"
    row = {
        "file_path": meta.get("file_path"),
        "language": meta.get("language"),
        "status": meta.get("status"),
        "triggered_by": meta.get("triggered_by", "Unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    errors = bq_client.insert_rows_json(table_id, [row])
    if errors:
        print("❌ Failed to log CI/CD event:", errors)
    else:
        print("📈 CI/CD event logged to BigQuery.")

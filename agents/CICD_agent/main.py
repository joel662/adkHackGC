import os
import json
from datetime import datetime, timezone
import requests
from google.cloud import pubsub_v1, bigquery
from config import PROJECT_ID, CICD_SUBSCRIPTION_ID, GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH

# Initialize BigQuery client
bq_client = bigquery.Client()

def log_to_cicd_table(data: dict):
    """Log the CI/CD status to the `cicd_events` BigQuery table."""
    table_id = f"{PROJECT_ID}.devops_logs.cicd_events"
    row = {
        "file_path": data.get("file_path"),
        "language": data.get("language"),
        "status": "passed" if "FAIL" not in data.get("test_output", "") else "failed",
        "triggered_by": "Test Generator",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    errors = bq_client.insert_rows_json(table_id, [row])
    if errors:
        print("❌ BigQuery insert errors (CI/CD):", errors)
    else:
        print("📊 CI/CD status logged to BigQuery.")

def trigger_github_workflow():
    """Optionally trigger a GitHub Actions deploy workflow."""
    if not all([GITHUB_TOKEN, GITHUB_REPO]):
        print("⚠️ GitHub token or repo not set. Skipping workflow trigger.")
        return

    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/deploy.yml/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "ref": GITHUB_BRANCH,
        "inputs": {
            "branch": GITHUB_BRANCH
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 204:
        print("🚀 GitHub Actions workflow triggered.")
    else:
        print("❌ GitHub Actions trigger failed:", response.text)

def process_test_result(data: dict):
    print("\n🧩 CI/CD Agent: Received Test Result")
    print(f"📄 File: {data.get('file_path')}")
    print(f"🌐 Language: {data.get('language')}")
    print("🧪 Test Output:\n", data.get("test_output"))

    log_to_cicd_table(data)
    trigger_github_workflow()

    if "FAIL" in data.get("test_output", "") or "Traceback" in data.get("test_output", ""):
        print("⚠️ Detected test failure or error!")
    else:
        print("✅ Test passed successfully.")

def callback(message):
    try:
        print("📥 New message received from Pub/Sub")
        data = json.loads(message.data.decode("utf-8"))
        process_test_result(data)
        message.ack()
    except Exception as e:
        print("❌ Failed to process message:", e)
        message.nack()

def listen_for_test_results():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, CICD_SUBSCRIPTION_ID)
    subscriber.subscribe(subscription_path, callback=callback)
    print(f"🔁 Listening for test results on '{CICD_SUBSCRIPTION_ID}'...")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("🛑 CI/CD Agent stopped.")

if __name__ == "__main__":
    print("🚀 Starting CI/CD Agent...")
    listen_for_test_results()

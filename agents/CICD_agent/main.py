import os
import json
from datetime import datetime
import requests
from google.cloud import pubsub_v1, bigquery
from config import PROJECT_ID, CICD_SUBSCRIPTION_ID, GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH

# BigQuery client
bq_client = bigquery.Client()

def log_to_bigquery(data: dict):
    row = {
        "file_path": data.get("file_path"),
        "language": data.get("language"),
        "test_output": data.get("test_output", "")[:5000],
        "deps": ", ".join(data.get("dependencies", [])),
        "review_summary": json.dumps(data.get("review_summary", {})),
        "timestamp": datetime.utcnow()
    }
    table_id = f"{PROJECT_ID}.devops_logs.test_results"
    errors = bq_client.insert_rows_json(table_id, [row])
    if errors:
        print("❌ BigQuery insert errors:", errors)
    else:
        print("📊 Logged to BigQuery.")

def trigger_github_workflow():
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
        print("❌ GitHub Actions failed:", response.text)

def process_test_result(data: dict):
    print("\n🧩 CI/CD Agent: Received Test Result")
    print("📄 File:", data.get("file_path"))
    print("🌐 Language:", data.get("language"))
    print("🧪 Test Output:\n", data.get("test_output"))

    log_to_bigquery(data)
    trigger_github_workflow()
    print("✅ CI/CD process completed.\n")

def callback(message):
    try:
        print("📥 New message received")
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
    listen_for_test_results()
    print("🚀 Starting CI/CD Agent...")
import os
import json
from datetime import datetime, timezone
import requests
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from config import PROJECT_ID, CICD_SUBSCRIPTION_ID, GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH
from utils import summarize_test_result
from logger import log_test_result, log_cicd_event

def trigger_github_workflow():
    """Optionally trigger a GitHub Actions deploy workflow."""
    if not all([GITHUB_TOKEN, GITHUB_REPO]):
        print("⚠️ GitHub token or repo not set. Skipping workflow trigger.")
        return False

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
        return True
    else:
        print("❌ GitHub Actions failed:", response.text)
        return False

def process_test_result(data: dict):
    print("\n🧩 CI/CD Agent: Received Test Result")

    file_path = data.get("file_path")
    language = data.get("language")
    test_output = data.get("test_output", "")
    dependencies = data.get("dependencies", [])
    review_summary = data.get("review_summary", {})

    print(f"📄 File: {file_path}")
    print(f"🌐 Language: {language}")
    print("🧪 Test Output:\n", test_output[:1000], "\n...")

    # Determine pass/fail status
    passed = all(term not in test_output for term in ["FAIL", "Traceback", "Error"])
    status = "PASSED" if passed else "FAILED"

    # 🧠 Summarize test output using Gemini
    summary = summarize_test_result(test_output, passed)

    # 📊 Log test result
    log_test_result({
        "file_path": file_path,
        "language": language,
        "test_output": test_output,
        "dependencies": dependencies,
        "review_summary": review_summary,
        "summary": summary,
    })

    # 🚀 Optionally trigger deployment and log CI/CD event
    triggered = trigger_github_workflow()
    log_cicd_event({
        "file_path": file_path,
        "language": language,
        "status": status,
        "triggered_by": "CI/CD Agent" if triggered else "Manual Review",
    })

    print(f"✅ CI/CD process {status} and logged successfully.\n")

def callback(message):
    try:
        print("📥 New message received from Pub/Sub")
        data = json.loads(message.data.decode("utf-8"))
        process_test_result(data)
        message.ack()
    except Exception as e:
        print("❌ Failed to process message:", e)
        message.nack()

def listen_for_test_results(timeout_seconds=20):
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, CICD_SUBSCRIPTION_ID)
    future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"🔁 Listening for test results on '{CICD_SUBSCRIPTION_ID}'...")

    try:
        future.result(timeout=timeout_seconds)
    except TimeoutError:
        print("⏳ CI/CD Agent timeout reached. Exiting.")
        future.cancel()

if __name__ == "__main__":
    print("🚀 Starting CI/CD Agent...")
    listen_for_test_results()

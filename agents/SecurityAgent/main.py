import json
import os
import time
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from scanner import scan_for_secrets_and_vulnerabilities
from config import PROJECT_ID, SECURITY_SUBSCRIPTION_ID
from utils import explain_security_findings
from logger import log_to_bigquery  # moved here for cleaner config separation

CURRENT_RUN_ID = os.getenv("RUN_ID", "manual")
def callback(message):
    try:
        print("📥 Security Agent received message")
        data = json.loads(message.data.decode("utf-8"))
        print("🔍 Payload:", json.dumps(data, indent=2))

        # 🧾 Filter only current run
        if data.get("run_id") != CURRENT_RUN_ID:
            print(f"⚠️ Skipping message with stale run_id: {data.get('run_id')}")
            message.ack()
            return

        file_path = data.get("file_path")
        language = data.get("language")
        test_output = data.get("test_output", "")
        deps = data.get("dependencies", [])
        review_summary = data.get("review_summary", {})

        findings = scan_for_secrets_and_vulnerabilities(file_path, deps)

        if findings:
            print("⚠️ Security issues found:", findings)

            # 🔍 Get LLM explanation for context
            explanation = explain_security_findings(findings)

            # 📝 Log to BigQuery
            log_to_bigquery({
                "file_path": file_path,
                "language": language,
                "vulnerabilities": findings,
                "llm_explanation": explanation,
                "run_id": CURRENT_RUN_ID  # include run_id in BigQuery logging
            })

        message.ack()
    except Exception as e:
        print("❌ Error in Security Agent:", e)
        message.nack()

def listen(timeout_seconds=20):
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SECURITY_SUBSCRIPTION_ID)
    future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"🛡️ Listening on subscription: {SECURITY_SUBSCRIPTION_ID}...")

    try:
        # Properly handle the timeout with pubsub's exception
        future.result(timeout=timeout_seconds)
    except TimeoutError:
        print("⏳ Timeout reached. Shutting down Security Agent.")
        future.cancel()

if __name__ == "__main__":
    listen()

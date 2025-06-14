import json
from google.cloud import pubsub_v1
from scanner import scan_for_secrets_and_vulnerabilities
from config import PROJECT_ID, SECURITY_SUBSCRIPTION_ID
from utils import explain_security_findings
from logger import log_to_bigquery  # moved here for cleaner config separation

def callback(message):
    try:
        print("📥 Security Agent received message")
        data = json.loads(message.data.decode("utf-8"))
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
                "llm_explanation": explanation
            })

        message.ack()
    except Exception as e:
        print("❌ Error in Security Agent:", e)
        message.nack()

def listen():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SECURITY_SUBSCRIPTION_ID)
    subscriber.subscribe(subscription_path, callback=callback)
    print(f"🛡️ Listening on subscription: {SECURITY_SUBSCRIPTION_ID}")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("🛑 Security Agent stopped.")

if __name__ == "__main__":
    listen()

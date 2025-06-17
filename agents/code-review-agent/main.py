import subprocess
import os
import json
from vertexai import init
from vertexai.preview.generative_models import GenerativeModel
from google.cloud import pubsub_v1
from utils import read_local_file, detect_language_from_extension
from prompts import build_code_review_prompt
from config import PROJECT_ID, LOCATION, PUBSUB_TOPIC

SUPPORTED_EXTENSIONS = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".sh", ".sql", ".jsx", ".tsx"]

# Initialize Gemini
init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.0-flash-lite-001")

def get_git_root() -> str:
    try:
        root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL)
        return root.decode("utf-8").strip()
    except subprocess.CalledProcessError:
        raise RuntimeError("❌ Not inside a Git repository.")

def publish_to_pubsub(data: dict):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
    message = json.dumps(data).encode("utf-8")
    future = publisher.publish(topic_path, data=message)
    print(f"📬 Published review to Pub/Sub (message ID: {future.result()})")

def review_code(source_path: str):
    try:
        print(f"💡 Reviewing file: {source_path}")
        code = read_local_file(source_path)
        language = detect_language_from_extension(source_path)
        prompt = build_code_review_prompt(code, language)
        response = model.generate_content(prompt)

        print(f"\n📄 Review Output for {source_path}:")
        print(response.text)

        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text.removeprefix("```json").removesuffix("```").strip()

        parsed_json = json.loads(cleaned_text)

        review_result = {
            "file_path": source_path,
            "language": language,
            "code": code,
            "review_summary": parsed_json
        }

        with open("agent_state.json", "w") as f:
            json.dump({"last_review": review_result}, f, indent=2)

        publish_to_pubsub(review_result)

    except Exception as e:
        print(f"❌ Error reviewing {source_path}:", e)

def review_all_code_in_repo(repo_root: str):
    for root, dirs, files in os.walk(repo_root):
        for file in files:
            if any(file.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                full_path = os.path.join(root, file)
                print(f"🔍 Scanning: {full_path}")
                review_code(full_path)

if __name__ == "__main__":
    try:
        repo_root = get_git_root()
        print(f"📁 Git root detected at: {repo_root}")
        review_all_code_in_repo(repo_root)
        print("✅ Code review completed for all supported files in the repository.")
    except Exception as e:
        print(e)
        print("Please ensure you are running this script inside a Git repository.")

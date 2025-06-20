import os
import sys
import json
import re
import shutil
import subprocess
from datetime import datetime
from git import Repo # type: ignore
from vertexai import init
from vertexai.preview.generative_models import GenerativeModel
from google.cloud import pubsub_v1, bigquery

from utils import read_local_file, detect_language_from_extension
from prompts import build_test_generator_prompt
from config import PROJECT_ID, LOCATION, PUBLISH_TOPIC, SUBSCRIPTION_ID

# Initialize Gemini and BigQuery
init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.0-flash-lite")

def extract_python_dependencies(code: str, project_dir: str) -> list:
    std_libs = {
        'os', 'sys', 're', 'math', 'time', 'datetime', 'json', 'random', 'unittest',
        'typing', 'io', 'tempfile', 'shutil', 'contextlib', 'csv', 'collections', 'itertools',
        'functools', 'argparse', 'logging', 'subprocess', 'threading', 'multiprocessing',
        'socket', 'ssl', 'hashlib', 'base64', 'pickle', 'struct', 'copy', 'traceback',
        'http', 'html', 'xml', 'email', 'pathlib', 'statistics', 'operator', 'queue'
    }
    local_modules = set()
    for root, _, files in os.walk(project_dir):
        for f in files:
            if f.endswith(".py"):
                local_modules.add(os.path.splitext(f)[0])
    imports = re.findall(r'^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)', code, re.MULTILINE)
    top_level = set(i.split('.')[0] for i in imports if not i.startswith(('__', 'test')))
    return list(top_level - std_libs - local_modules)

def write_requirements(requirements: list, path: str):
    with open(path, "w") as f:
        f.write("\n".join(requirements))

def install_dependencies(requirements_path: str):
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_path], check=True)

def uninstall_dependencies(packages: list):
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", *packages], check=False)

def get_git_root() -> str:
    try:
        root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL)
        return root.decode("utf-8").strip()
    except subprocess.CalledProcessError:
        raise RuntimeError("❌ Not inside a Git repository.")

def run_python_test(test_file_path: str):
    test_dir = os.path.dirname(test_file_path)
    with open(test_file_path, encoding="utf-8", errors="replace") as f:
        test_code = f.read()
    temp_path = test_file_path + ".temp.py"
    injected_code = f"import sys\nsys.path.insert(0, r'{test_dir}')\n" + test_code
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(injected_code)
    result = subprocess.run([sys.executable, temp_path], capture_output=True, text=True)
    os.remove(temp_path)
    return result.stdout + result.stderr

def run_test(language: str, test_path: str):
    return run_python_test(test_path) if language == "python" else f"⚠️ Language '{language}' not supported."

def publish_test_result(data: dict):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, PUBLISH_TOPIC)
    publisher.publish(topic_path, data=json.dumps(data).encode("utf-8"))
    print("📤 Published test result to Pub/Sub.")

def log_to_bigquery(result: dict):
    client = bigquery.Client()
    table_id = f"{PROJECT_ID}.devops_logs.test_results"
    row = {
        "file_path": result["file_path"],
        "language": result["language"],
        "test_output": result["test_output"][:5000],
        "deps": ", ".join(result.get("dependencies", [])),
        "review_summary": json.dumps(result.get("review_summary", {})),
        "timestamp": datetime.utcnow().isoformat()
    }
    errors = client.insert_rows_json(table_id, [row])
    if errors:
        print("❌ BigQuery insert failed:", errors)
    else:
        print("✅ Logged test result to BigQuery.")

def generate_test_for_file(source_path: str, output_dir: str, root_dir: str, review: dict = None, run_id: str = "manual"):

    try:
        code = read_local_file(source_path)
        language = detect_language_from_extension(source_path)

        prompt = build_test_generator_prompt(code, language, os.path.basename(source_path), review=review)
        response = model.generate_content(prompt)
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.splitlines()[1:-1]).strip()

        os.makedirs(output_dir, exist_ok=True)

        test_filename = f"test_{os.path.basename(source_path)}"
        test_path = os.path.join(output_dir, test_filename)
        root_test_path = os.path.join(root_dir, test_filename)

        with open(test_path, "w", encoding="utf-8") as f:
            f.write(raw)

        print(f"✅ Test generated and saved to: {test_path}")

        deps = extract_python_dependencies(raw, root_dir) if language == "python" else []
        if deps:
            req_path = os.path.join(output_dir, "requirements.txt")
            write_requirements(deps, req_path)
            install_dependencies(req_path)

        shutil.copy2(test_path, root_test_path)
        result = run_test(language, root_test_path)

        test_result = {
            "file_path": source_path,
            "language": language,
            "test_output": result,
            "dependencies": deps,
            "review_summary": review,
        }

        publish_test_result(test_result)
        log_to_bigquery(test_result)

        # if language == "python" and deps:
        #     uninstall_dependencies(deps)

        os.remove(root_test_path)

    except Exception as e:
        print(f"❌ Test generation failed for {source_path}: {e}")

def callback(message):
    try:
        print("📥 Received message")
        data = json.loads(message.data.decode("utf-8"))
        file_path = data["file_path"]
        review_summary = data.get("review_summary", {})

        root_dir = get_git_root()
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "generated_tests")
        os.makedirs(output_dir, exist_ok=True)

        generate_test_for_file(file_path, output_dir, root_dir, review=review_summary)
        message.ack()
    except Exception as e:
        print(f"❌ Callback error: {e}")
        message.nack()

def listen_for_messages():
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    subscriber.subscribe(sub_path, callback=callback)
    print(f"🔁 Listening on subscription: {SUBSCRIPTION_ID}")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("🛑 Subscriber stopped.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        run_id = os.getenv("RUN_ID", "manual")  # 👈 inject run_id from env

        root_dir = get_git_root()
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "generated_tests")
        os.makedirs(output_dir, exist_ok=True)

        generate_test_for_file(input_file, output_dir, root_dir, review={}, run_id=run_id)  # 👈 pass run_id
    else:
        listen_for_messages()
import os
import sys
import json
import re
import shutil
import subprocess
from datetime import datetime
from git import Repo # type: ignore
from vertexai import init
from vertexai.preview.generative_models import GenerativeModel
from google.cloud import pubsub_v1, bigquery

from utils import read_local_file, detect_language_from_extension
from prompts import build_test_generator_prompt
from config import PROJECT_ID, LOCATION, PUBLISH_TOPIC, SUBSCRIPTION_ID

# Initialize Gemini and BigQuery
init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.0-flash-lite")

def extract_python_dependencies(code: str, project_dir: str) -> list:
    std_libs = {
        'os', 'sys', 're', 'math', 'time', 'datetime', 'json', 'random', 'unittest',
        'typing', 'io', 'tempfile', 'shutil', 'contextlib', 'csv', 'collections', 'itertools',
        'functools', 'argparse', 'logging', 'subprocess', 'threading', 'multiprocessing',
        'socket', 'ssl', 'hashlib', 'base64', 'pickle', 'struct', 'copy', 'traceback',
        'http', 'html', 'xml', 'email', 'pathlib', 'statistics', 'operator', 'queue'
    }
    local_modules = set()
    for root, _, files in os.walk(project_dir):
        for f in files:
            if f.endswith(".py"):
                local_modules.add(os.path.splitext(f)[0])
    imports = re.findall(r'^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)', code, re.MULTILINE)
    top_level = set(i.split('.')[0] for i in imports if not i.startswith(('__', 'test')))
    return list(top_level - std_libs - local_modules)

def write_requirements(requirements: list, path: str):
    with open(path, "w") as f:
        f.write("\n".join(requirements))

def install_dependencies(requirements_path: str):
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_path], check=True)

def uninstall_dependencies(packages: list):
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", *packages], check=False)

def get_git_root() -> str:
    try:
        root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL)
        return root.decode("utf-8").strip()
    except subprocess.CalledProcessError:
        raise RuntimeError("❌ Not inside a Git repository.")

def run_python_test(test_file_path: str):
    test_dir = os.path.dirname(test_file_path)
    with open(test_file_path, encoding="utf-8", errors="replace") as f:
        test_code = f.read()
    temp_path = test_file_path + ".temp.py"
    injected_code = f"import sys\nsys.path.insert(0, r'{test_dir}')\n" + test_code
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(injected_code)
    result = subprocess.run([sys.executable, temp_path], capture_output=True, text=True)
    os.remove(temp_path)
    return result.stdout + result.stderr

def run_test(language: str, test_path: str):
    return run_python_test(test_path) if language == "python" else f"⚠️ Language '{language}' not supported."

def publish_test_result(data: dict):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, PUBLISH_TOPIC)
    publisher.publish(topic_path, data=json.dumps(data).encode("utf-8"))
    print("📤 Published test result to Pub/Sub.")

def log_to_bigquery(result: dict):
    client = bigquery.Client()
    table_id = f"{PROJECT_ID}.devops_logs.test_results"
    row = {
        "file_path": result["file_path"],
        "language": result["language"],
        "test_output": result["test_output"][:5000],
        "deps": ", ".join(result.get("dependencies", [])),
        "review_summary": json.dumps(result.get("review_summary", {})),
        "timestamp": datetime.utcnow().isoformat(),
        "run_id": result.get("run_id", "manual")
    }
    errors = client.insert_rows_json(table_id, [row])
    if errors:
        print("❌ BigQuery insert failed:", errors)
    else:
        print("✅ Logged test result to BigQuery.")

def generate_test_for_file(source_path: str, output_dir: str, root_dir: str, review: dict = None, run_id: str = "manual"):
    try:
        print(f"🧪 Generating test for: {source_path} (run_id={run_id})")
        code = read_local_file(source_path)
        language = detect_language_from_extension(source_path)

        prompt = build_test_generator_prompt(code, language, os.path.basename(source_path), review=review)
        response = model.generate_content(prompt)
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.splitlines()[1:-1]).strip()

        os.makedirs(output_dir, exist_ok=True)

        test_filename = f"test_{os.path.basename(source_path)}"
        test_path = os.path.join(output_dir, test_filename)
        root_test_path = os.path.join(root_dir, test_filename)

        with open(test_path, "w", encoding="utf-8") as f:
            f.write(raw)

        print(f"✅ Test saved to: {test_path}")

        deps = extract_python_dependencies(raw, root_dir) if language == "python" else []
        if deps:
            req_path = os.path.join(output_dir, "requirements.txt")
            write_requirements(deps, req_path)
            install_dependencies(req_path)

        shutil.copy2(test_path, root_test_path)
        result = run_test(language, root_test_path)

        test_result = {
            "file_path": source_path,
            "language": language,
            "test_output": result,
            "dependencies": deps,
            "review_summary": review,
            "run_id": run_id
        }

        publish_test_result(test_result)
        log_to_bigquery(test_result)

        # if language == "python" and deps:
        #     uninstall_dependencies(deps)

        os.remove(root_test_path)

    except Exception as e:
        print(f"❌ Test generation failed for {source_path}: {e}")

def callback(message):
    try:
        print("📥 Received message")
        data = json.loads(message.data.decode("utf-8"))
        file_path = data["file_path"]
        review_summary = data.get("review_summary", {})
        run_id = data.get("run_id", "manual")

        root_dir = get_git_root()
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "generated_tests")
        os.makedirs(output_dir, exist_ok=True)

        generate_test_for_file(file_path, output_dir, root_dir, review=review_summary, run_id=run_id)
        message.ack()
    except Exception as e:
        print(f"❌ Callback error: {e}")
        message.nack()

def listen_for_messages():
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    subscriber.subscribe(sub_path, callback=callback)
    print(f"🔁 Listening on subscription: {SUBSCRIPTION_ID}")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("🛑 Subscriber stopped.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        run_id = os.getenv("RUN_ID", "manual")
        root_dir = get_git_root()
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "generated_tests")
        os.makedirs(output_dir, exist_ok=True)
        generate_test_for_file(input_file, output_dir, root_dir, review={}, run_id=run_id)
    else:
        listen_for_messages()

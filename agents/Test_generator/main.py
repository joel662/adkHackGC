import vertexai
from vertexai.preview.generative_models import GenerativeModel
from utils import read_local_file, read_remote_file, is_url, detect_language_from_extension
from prompts import build_test_generator_prompt
from config import PROJECT_ID, LOCATION
import sys
import os
import subprocess
import re
import tempfile
import shutil
from git import Repo

EXTENSION_LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".java": "java",
    ".cpp": "cpp", ".c": "c", ".cs": "c#", ".go": "go", ".rb": "ruby", ".php": "php",
    ".rs": "rust", ".swift": "swift", ".kt": "kotlin", ".sh": "bash", ".sql": "sql",
    ".html": "html", ".jsx": "react-jsx", ".tsx": "react-tsx"
}

vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.0-flash-lite-001")

def extract_python_dependencies(code: str) -> list:
    std_libs = {
        'os', 'sys', 're', 'math', 'time', 'datetime', 'json', 'random', 'unittest',
        'typing', 'io', 'tempfile', 'shutil'
    }
    fake_modules = {'your_code', 'my_module', 'my_package', 'test_module'}
    imports = re.findall(r'^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)', code, re.MULTILINE)
    cleaned = set(i.split('.')[0] for i in imports if not i.startswith(('__', 'test')))
    return list(cleaned - std_libs - fake_modules)

def write_requirements(requirements: list, path: str):
    with open(path, "w") as f:
        f.write("\n".join(requirements))

def install_dependencies(requirements_path: str):
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_path], check=True)

def uninstall_dependencies(packages: list):
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", *packages], check=False)

def run_python_test(test_file_path: str):
    result = subprocess.run([sys.executable, test_file_path], capture_output=True, text=True)
    return result.stdout + result.stderr

def run_node_test(file_path):
    try:
        os.makedirs("node_temp", exist_ok=True)
        temp_test_path = os.path.join("node_temp", "test.js")
        with open(temp_test_path, "w") as f:
            f.write(open(file_path).read())
        subprocess.run(["npm", "install"], cwd="node_temp", check=False)
        result = subprocess.run(["node", "test.js"], capture_output=True, text=True, cwd="node_temp")
        return result.stdout + result.stderr
    finally:
        subprocess.run(["rm", "-rf", "node_temp"])

def run_typescript_test(file_path):
    result = subprocess.run(["npx", "ts-node", file_path], capture_output=True, text=True)
    return result.stdout + result.stderr

def run_java_test(file_path):
    class_name = os.path.basename(file_path).replace(".java", "")
    subprocess.run(["javac", file_path], check=True)
    result = subprocess.run(["java", "-cp", os.path.dirname(file_path), class_name], capture_output=True, text=True)
    return result.stdout + result.stderr

def run_cpp_test(file_path):
    binary = "a.out"
    subprocess.run(["g++", file_path, "-o", binary], check=True)
    result = subprocess.run([f"./{binary}"], capture_output=True, text=True)
    os.remove(binary)
    return result.stdout + result.stderr

def run_c_test(file_path):
    binary = "a.out"
    subprocess.run(["gcc", file_path, "-o", binary], check=True)
    result = subprocess.run([f"./{binary}"], capture_output=True, text=True)
    os.remove(binary)
    return result.stdout + result.stderr

def run_go_test(file_path):
    result = subprocess.run(["go", "run", file_path], capture_output=True, text=True)
    return result.stdout + result.stderr

def run_bash_test(file_path):
    result = subprocess.run(["bash", file_path], capture_output=True, text=True)
    return result.stdout + result.stderr

def run_sql_test(file_path):
    db = "test.db"
    result = subprocess.run(["sqlite3", db, f".read {file_path}"], capture_output=True, text=True)
    return result.stdout + result.stderr

def run_test(language: str, test_path: str):
    if language == "python":
        return run_python_test(test_path)
    elif language in {"javascript", "react-jsx"}:
        return run_node_test(test_path)
    elif language in {"typescript", "react-tsx"}:
        return run_typescript_test(test_path)
    elif language == "java":
        return run_java_test(test_path)
    elif language == "cpp":
        return run_cpp_test(test_path)
    elif language == "c":
        return run_c_test(test_path)
    elif language == "go":
        return run_go_test(test_path)
    elif language == "bash":
        return run_bash_test(test_path)
    elif language == "sql":
        return run_sql_test(test_path)
    else:
        raise NotImplementedError(f"Language '{language}' not yet supported.")

def get_supported_files_from_repo(repo_url):
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"🔄 Cloning repo: {repo_url}")
        Repo.clone_from(repo_url, temp_dir)

        supported_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in EXTENSION_LANGUAGE_MAP:
                    full_path = os.path.join(root, file)
                    supported_files.append(full_path)

        return supported_files, temp_dir
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to clone repo: {e}")

def generate_tests(source_path: str, output_dir="generated_tests"):
    try:
        if is_url(source_path):
            code = read_remote_file(source_path)
            language = detect_language_from_extension(source_path)
        else:
            code = read_local_file(source_path)
            language = detect_language_from_extension(source_path)

        prompt = build_test_generator_prompt(code, language)
        response = model.generate_content(prompt)
        raw = response.text.strip()

        if raw.startswith("```"):
            raw = "\n".join(raw.splitlines()[1:-1]).strip()

        os.makedirs(output_dir, exist_ok=True)
        test_filename = f"test_{os.path.basename(source_path)}"
        test_path = os.path.join(output_dir, test_filename)

        with open(test_path, "w", encoding="utf-8") as f:
            f.write(raw)

        print(f"✅ Test generated and saved to: {test_path}")

        if language == "python":
            deps = extract_python_dependencies(raw)
            if deps:
                req_path = os.path.join(output_dir, "requirements.txt")
                write_requirements(deps, req_path)
                print(f"📦 Installing dependencies: {deps}")
                install_dependencies(req_path)

        print("🚀 Running test...")
        result = run_test(language, test_path)
        print("🧪 Test output:\n" + result)

        if language == "python" and deps:
            print("🧹 Cleaning up dependencies...")
            uninstall_dependencies(deps)

    except Exception as e:
        print("❌ Error during test generation or execution:", e)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <file-path-or-raw-github-url>")
    else:
        input_path = sys.argv[1]
        if input_path.endswith(".git") and input_path.startswith("http"):
            try:
                files, temp_repo = get_supported_files_from_repo(input_path)
                for f in files:
                    print(f"\n🔍 Processing {f}")
                    generate_tests(f)
                print(f"\n✅ All supported files in repo processed.")
                shutil.rmtree(temp_repo, ignore_errors=True)
            except Exception as e:
                print(f"❌ Repo processing failed: {e}")
        else:
            generate_tests(input_path)

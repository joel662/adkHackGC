from vertexai import init
from vertexai.preview.generative_models import GenerativeModel
from utils import read_local_file, read_remote_file, is_url, detect_language_from_extension
from prompts import build_test_generator_prompt
from config import PROJECT_ID, LOCATION
import sys
import os
import subprocess
import re
import shutil
from git import Repo

EXTENSION_LANGUAGE_MAP = {
    ".py": "python"
}

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
    if language == "python":
        return run_python_test(test_path)
    else:
        return f"⚠️ Language '{language}' test execution not implemented."

def get_supported_files_from_local_repo(repo_root):
    supported_files = []
    for root, _, files in os.walk(repo_root):
        if any(skip in root.split(os.sep) for skip in {"agents", "generated_tests"}):
            continue
        for file in files:
            if file.endswith(".py"):
                supported_files.append(os.path.join(root, file))
    return supported_files

def clean_non_test_files(folder: str):
    for file in os.listdir(folder):
        if file.endswith(".py") and not file.startswith("test_"):
            os.remove(os.path.join(folder, file))

def generate_test_for_file(source_path: str, output_dir: str, root_dir: str):
    try:
        code = read_local_file(source_path)
        language = detect_language_from_extension(source_path)

        prompt = build_test_generator_prompt(code, language, os.path.basename(source_path))
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

        deps = []
        if language == "python":
            deps = extract_python_dependencies(raw, root_dir)
            if deps:
                req_path = os.path.join(output_dir, "requirements.txt")
                write_requirements(deps, req_path)
                print(f"📦 Installing dependencies: {deps}")
                install_dependencies(req_path)

        shutil.copy2(test_path, root_test_path)

        print("🚀 Running test...")
        result = run_test(language, root_test_path)

        if "Traceback" in result or "AssertionError" in result or "FAIL" in result:
            print("🧪 Test output:\n" + result)
        else:
            print("✅ Test passed with no errors.\n")

        if language == "python" and deps:
            print("🧹 Cleaning up dependencies...")
            uninstall_dependencies(deps)

        os.remove(root_test_path)

    except Exception as e:
        print(f"❌ Error while generating or running test for {source_path}:", e)

if __name__ == "__main__":
    try:
        root_dir = get_git_root()
        output_dir = os.path.join(root_dir, "generated_tests")

        os.makedirs(output_dir, exist_ok=True)

        if len(sys.argv) == 2:
            input_path = sys.argv[1]
            generate_test_for_file(input_path, output_dir, root_dir)
        else:
            files = get_supported_files_from_local_repo(root_dir)
            print(f"\n⚙️ Generating and running tests on copied files...\n")
            for f in files:
                generate_test_for_file(f, output_dir, root_dir)

            clean_non_test_files(output_dir)
            print(f"\n✅ All tests completed. Only test files remain in {output_dir}")

    except Exception as e:
        print(f"❌ Error: {e}")
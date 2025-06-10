import os
import subprocess
import sys

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(AGENTS_DIR)
CODE_REVIEWER = os.path.join(AGENTS_DIR, "code-review-agent", "main.py")
TEST_GENERATOR = os.path.join(AGENTS_DIR, "Test_generator", "main.py")
IGNORE_FILE = os.path.join(PROJECT_ROOT, ".agentignore")

def load_ignored_files():
    if not os.path.exists(IGNORE_FILE):
        return set()
    with open(IGNORE_FILE, "r") as f:
        lines = f.readlines()
    return set(line.strip() for line in lines if line.strip() and not line.startswith("#"))

def is_python_file(path):
    return path.endswith(".py") and "agents" not in path

def find_python_files(root_dir, ignored_files):
    py_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            full_path = os.path.join(dirpath, file)
            rel_path = os.path.relpath(full_path, PROJECT_ROOT)
            if is_python_file(rel_path) and rel_path not in ignored_files:
                py_files.append(full_path)
    return py_files

def run_agent(agent_path, target_file):
    print(f"\n🚀 Running {os.path.basename(agent_path)} on {target_file}")
    subprocess.run([sys.executable, agent_path, target_file], check=False)

if __name__ == "__main__":
    ignored = load_ignored_files()
    py_files = find_python_files(PROJECT_ROOT, ignored)

    if not py_files:
        print("⚠️ No Python files to process.")
        sys.exit(0)

    for py_file in py_files:
        run_agent(CODE_REVIEWER, py_file)
        run_agent(TEST_GENERATOR, py_file)

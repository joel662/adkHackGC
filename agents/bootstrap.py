import os
import subprocess
import sys

# Get absolute path to this agents/ directory
AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(AGENTS_DIR)

CODE_REVIEWER = os.path.join(AGENTS_DIR, "code_reviewer", "main.py")
TEST_GENERATOR = os.path.join(AGENTS_DIR, "test_generator", "main.py")

def is_python_file(path):
    return path.endswith(".py") and "agents" not in path

def find_python_files(root_dir):
    py_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            full_path = os.path.join(dirpath, file)
            rel_path = os.path.relpath(full_path, PROJECT_ROOT)
            if is_python_file(rel_path):
                py_files.append(full_path)
    return py_files

def run_agent(agent_path, target_file):
    print(f"\n🚀 Running {os.path.basename(agent_path)} on {target_file}")
    subprocess.run([sys.executable, agent_path, target_file], check=False)

if __name__ == "__main__":
    py_files = find_python_files(PROJECT_ROOT)
    if not py_files:
        print("⚠️ No Python files found outside agents/ directory.")
        sys.exit(0)

    for py_file in py_files:
        run_agent(CODE_REVIEWER, py_file)
        run_agent(TEST_GENERATOR, py_file)

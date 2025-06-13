import os
from dotenv import load_dotenv

# Load shared .env.local from root
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env.local'))
load_dotenv(dotenv_path=env_path)

PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
CICD_SUBSCRIPTION_ID = os.getenv("CICD_SUBSCRIPTION_ID", "cicd_listener_sub")

# Optional GitHub workflow info
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

if not PROJECT_ID:
    raise EnvironmentError("❌ PROJECT_ID is not set. Check your .env.local file.")

import os
from dotenv import load_dotenv

# Load .env.local from root directory
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env.local'))
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

# Load from .env or CI environment
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID") or os.environ.get("VERTEX_PROJECT_ID") or os.environ.get("PROJECT_ID")
LOCATION = os.getenv("VERTEX_LOCATION") or os.environ.get("VERTEX_LOCATION") or "us-central1"
SECURITY_SUBSCRIPTION_ID = os.getenv("SECURITY_SUBSCRIPTION_ID") or os.environ.get("SECURITY_SUBSCRIPTION_ID", "security_agent_sub")

if not PROJECT_ID:
    raise EnvironmentError("❌ PROJECT_ID is not set. Define it in .env.local or GitHub Actions secrets.")

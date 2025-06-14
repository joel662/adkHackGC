import os
from dotenv import load_dotenv

# Load shared .env.local from root
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env.local'))
load_dotenv(dotenv_path=env_path)

PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
SECURITY_SUBSCRIPTION_ID = os.getenv("SECURITY_SUBSCRIPTION_ID", "security_agent_sub")

if not PROJECT_ID:
    raise EnvironmentError("❌ PROJECT_ID is not set in .env.local")

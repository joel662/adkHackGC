import os
from dotenv import load_dotenv

# Automatically resolve path to shared .env at root
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env.local'))
load_dotenv(dotenv_path=env_path)

PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
LOCATION = os.getenv("VERTEX_LOCATION")
PUBSUB_TOPIC = os.getenv("PUBSUB_TOPIC")


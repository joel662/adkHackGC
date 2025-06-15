import os
from dotenv import load_dotenv

# Automatically resolve path to shared .env at root
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env.local'))
load_dotenv(dotenv_path=env_path)

PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
LOCATION = os.getenv("VERTEX_LOCATION")
PUBLISH_TOPIC = os.getenv("PUBLISH_TOPIC", "test_generation_done")
PUBLISH_TOPIC = os.getenv("TEST_GEN_OUTPUT_TOPIC", "test_generation_done")
SUBSCRIPTION_ID = os.getenv("TEST_GEN_SUBSCRIPTION_ID", "test_generator_sub")



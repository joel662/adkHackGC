import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
LOCATION = os.getenv("VERTEX_LOCATION")
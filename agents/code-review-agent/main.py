from vertexai import init
from vertexai.preview.generative_models import GenerativeModel
from utils import read_local_file, read_remote_file, is_url, detect_language_from_extension
from prompts import build_code_review_prompt
from config import PROJECT_ID, LOCATION
import json
import sys
import os

init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.0-flash-lite-001")

def review_code(source_path: str):
    try:
        if is_url(source_path):
            code = read_remote_file(source_path)
            language = "unknown"
        else:
            code = read_local_file(source_path)
            language = detect_language_from_extension(source_path)

        prompt = build_code_review_prompt(code, language)
        response = model.generate_content(prompt)

        print("\n📄 Review Output:")
        print(response.text)

        cleaned_text = response.text.strip()

        # Remove markdown formatting if present
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text.removeprefix("```json").removesuffix("```").strip()

        parsed_json = json.loads(cleaned_text)

        with open("agent_state.json", "w") as f:
            json.dump({"last_review": parsed_json}, f, indent=2)


    except Exception as e:
        print("❌ Error during code review:", e)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <file-path-or-raw-github-url>")
    else:
        review_code(sys.argv[1])
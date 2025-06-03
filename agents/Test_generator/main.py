import vertexai
from vertexai.preview.generative_models import GenerativeModel
from utils import read_local_file, read_remote_file, is_url, detect_language_from_extension
from prompts import build_test_generator_prompt
from config import PROJECT_ID, LOCATION
import sys
import os

vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.0-flash-lite-001")

def generate_tests(source_path: str, output_dir="generated_tests"):
    try:
        if is_url(source_path):
            code = read_remote_file(source_path)
            language = "unknown"
        else:
            code = read_local_file(source_path)
            language = detect_language_from_extension(source_path)

        prompt = build_test_generator_prompt(code, language)
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Remove markdown formatting if present
        if raw.startswith("```"):
            raw = "\n".join(raw.splitlines()[1:-1]).strip()

        os.makedirs(output_dir, exist_ok=True)
        filename = f"test_{os.path.basename(source_path)}"
        test_path = os.path.join(output_dir, filename)

        with open(test_path, "w", encoding="utf-8") as f:
            f.write(raw)

        print(f"\n✅ Test generated and saved to: {test_path}")

    except Exception as e:
        print("❌ Error during test generation:", e)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <file-path-or-raw-github-url>")
    else:
        generate_tests(sys.argv[1])

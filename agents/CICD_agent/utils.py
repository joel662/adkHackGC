from vertexai import init
from vertexai.preview.generative_models import GenerativeModel
from config import PROJECT_ID, LOCATION
from prompts import build_ci_prompt

init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.0-flash-lite")

def summarize_test_result(test_output: str, passed: bool = False) -> str:
    try:
        prompt = build_ci_prompt(test_output, passed)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[Gemini Error] Could not summarize test result: {e}"

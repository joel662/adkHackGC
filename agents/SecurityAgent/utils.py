from vertexai import init
from vertexai.preview.generative_models import GenerativeModel
from config import PROJECT_ID, LOCATION
from prompts import build_security_prompt

init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.0-flash-lite")

def explain_security_findings(findings: dict) -> str:
    try:
        prompt = build_security_prompt(findings)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[Gemini Error] Could not explain security findings: {e}"

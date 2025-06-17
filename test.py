import os
from vertexai.preview.generative_models import GenerativeModel
import vertexai

PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
LOCATION = os.getenv("VERTEX_LOCATION")


def main():
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel("gemini-2.0-flash-lite-001")

    print("🤖 Gemini Agent is ready. Type 'exit' to quit.")
    while True:
        prompt = input("You: ")
        if prompt.lower() == "exit":
            break

        try:
            response = model.generate_content(prompt)
            print("Gemini:", response.text)
 
    main()

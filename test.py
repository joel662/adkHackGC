from vertexai.preview.generative_models import GenerativeModel
import vertexai

def main():
    vertexai.init(project="halogen-framing-461606-q5", location="us-central1") # PUT project ID and location IN ENV FILE

    model = GenerativeModel("gemini-2.0-flash-lite-001")

    print("🤖 Gemini Agent is ready. Type 'exit' to quit.")
    while True:
        prompt = input("You: ")
        if prompt.lower() == "exit":
            break

        try:
            response = model.generate_content(prompt)
            print("Gemini:", response.text)
        except Exception as e:
            print("❌ Error:", e)

if __name__ == "__main__":
    main()

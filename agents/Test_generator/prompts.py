def build_test_generator_prompt(code: str, language: str, filename: str = "") -> str:
    return f"""
You are a helpful test-writing assistant. The language is {language}.

Here is the source code from file `{filename}`:
{code}

Please generate a fully working unit test file. Requirements:

- Use the appropriate testing framework (e.g., `unittest` for Python)
- Import all functions or classes using **direct absolute imports** like `from {filename.replace('.py', '')} import ...`
- DO NOT use relative imports like `from .{filename.replace('.py', '')} import ...`
- DO NOT hallucinate functions or modules — only write tests for what’s explicitly defined in the code
- Assume this file is in the same directory as the test file
- Include only executable test code
- Respond ONLY with a complete test file, wrapped in triple backticks (```), and nothing else.
""".strip()


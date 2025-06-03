def build_code_review_prompt(code: str, language: str = "unknown") -> str:
    return f"""
You are a senior software engineer. Please review the following {language} code.

Return a JSON object with:
1. "issues": a list of dictionaries with "type", "line", and "description"
2. "summary": a short paragraph summarizing the review

Respond ONLY with valid JSON.

```{language}
{code}
```
"""
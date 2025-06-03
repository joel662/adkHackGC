def build_test_generator_prompt(code: str, language: str = "unknown") -> str:
    return f"""
You are an expert {language} developer. Write comprehensive unit tests for the following {language} code.

Instructions:
- Use the standard test framework for the language.
- Cover normal cases, edge cases, and failure scenarios.
- Return only executable {language} code in your response, inside a code block.

```{language}
{code}
```

""" 
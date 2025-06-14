def build_ci_prompt(test_output: str, passed: bool = False) -> str:
    if passed:
        return f"""
You are a CI assistant. The following test suite has passed successfully:

{test_output}

Summarize what was tested and confirm that all assertions passed. Highlight any useful metrics or observations in 1-2 lines.
""".strip()
    else:
        return f"""
You are a CI assistant. Here is a failing test output:
{test_output}

Summarize the cause of failure in 2-3 lines and suggest how a developer could fix it.
""".strip()

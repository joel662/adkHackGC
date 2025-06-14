import json


def build_security_prompt(findings: dict) -> str:
    return f"""
You're a security auditor. Below is a list of secrets and vulnerabilities detected in a codebase:

{json.dumps(findings, indent=2)}

Summarize the risks and suggest mitigation for the top 2 most critical issues.
""".strip()

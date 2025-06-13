import re
import subprocess

SECRET_PATTERNS = [
    re.compile(r"(secret|token|api|key|password)[\s:=]+['\"]?[A-Za-z0-9_\-]{16,}['\"]?", re.IGNORECASE),
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS
    re.compile(r"ghp_[A-Za-z0-9]{36}"),  # GitHub Token
]

def scan_for_secrets_and_vulnerabilities(file_path, deps):
    findings = {"secrets": [], "vulnerabilities": []}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            for pattern in SECRET_PATTERNS:
                matches = pattern.findall(content)
                if matches:
                    findings["secrets"].extend(matches)
    except Exception as e:
        findings["secrets"].append(f"File read error: {e}")

    if deps:
        try:
            result = subprocess.run(["safety", "check", "--stdin"], input="\n".join(deps), text=True, capture_output=True)
            if result.stdout:
                findings["vulnerabilities"].append(result.stdout.strip())
        except Exception as e:
            findings["vulnerabilities"].append(f"Safety scan failed: {e}")

    return findings if findings["secrets"] or findings["vulnerabilities"] else None

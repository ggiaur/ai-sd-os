import re
from pathlib import Path
from typing import List, Dict, Any

DEFAULT_PATTERNS = [
    r"sk-ant-[a-zA-Z0-9_-]+",
    r"sk-[a-zA-Z0-9]{32,}",
    r"ghp_[a-zA-Z0-9]{36}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN PRIVATE KEY-----"
]

class SecretScanner:
    def __init__(self, patterns: List[str] = None):
        self.patterns = [re.compile(p) for p in (patterns or DEFAULT_PATTERNS)]

    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        findings = []
        if not file_path.exists() or file_path.is_dir():
            return findings
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            for line_idx, line in enumerate(content.splitlines(), 1):
                for pat in self.patterns:
                    match = pat.search(line)
                    if match:
                        findings.append({
                            "file": str(file_path),
                            "line": line_idx,
                            "match": match.group(0)[:10] + "..."
                        })
        except Exception:
            pass
        return findings

    def scan_directory(self, root_dir: Path) -> List[Dict[str, Any]]:
        results = []
        for p in root_dir.glob("**/*"):
            if p.is_file() and ".git" not in p.parts and ".ai-sd-os" not in p.parts:
                results.extend(self.scan_file(p))
        return results

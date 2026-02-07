#!/usr/bin/env python3
"""
House Bernard — Static Security Scanner v1.0
AST-based analysis of SAIF artifacts before execution.
Runs BEFORE the Executioner. Catches dangerous patterns at parse time.

Usage:
    python3 security_scanner.py <path_to_artifact.py>
    python3 security_scanner.py --scan-dir <directory>

Exit codes:
    0 = CLEAN
    1 = THREATS DETECTED
    2 = PARSE ERROR (file is not valid Python)
"""

import ast
import sys
import json
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

# === THREAT DEFINITIONS ===

# Functions/modules that should NEVER appear in a SAIF artifact
BANNED_IMPORTS = {
    "subprocess", "os.system", "shutil.rmtree", "ctypes",
    "multiprocessing", "threading", "signal", "pty",
    "importlib", "runpy", "code", "codeop", "compile",
    "socket", "http", "urllib", "requests", "httpx",
    "ftplib", "smtplib", "telnetlib", "xmlrpc",
    "pickle", "shelve", "marshal",
    "webbrowser", "antigravity",
    "tempfile",  # artifacts should use /work only
}

BANNED_FUNCTIONS = {
    "exec", "eval", "compile", "__import__",
    "getattr", "setattr", "delattr",
    "globals", "locals", "vars",
    "open",  # artifacts should not do raw file I/O outside /work
    "exit", "quit", "sys.exit",
}

BANNED_ATTRIBUTES = {
    "__subclasses__", "__bases__", "__mro__",
    "__code__", "__globals__", "__builtins__",
    "__class__", "__dict__",  # introspection attacks
}

# Patterns that indicate sandbox escape attempts
ESCAPE_PATTERNS = {
    "/proc", "/sys", "/dev", "/etc", "/tmp",
    "/root", "/home", "/var", "/usr",
    "../../", "../",
    "/app/",  # trying to write to read-only mount
}


class ThreatFinding:
    """Single security finding."""
    def __init__(self, severity: str, category: str, message: str,
                 line: int, col: int, node_type: str):
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
        self.category = category
        self.message = message
        self.line = line
        self.col = col
        self.node_type = node_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "line": self.line,
            "col": self.col,
            "node_type": self.node_type,
        }


class SecurityScanner(ast.NodeVisitor):
    """AST visitor that detects security threats in Python source."""

    def __init__(self, source_path: str):
        self.source_path = source_path
        self.findings: List[ThreatFinding] = []

    def _add(self, severity, category, message, node):
        self.findings.append(ThreatFinding(
            severity=severity,
            category=category,
            message=message,
            line=getattr(node, 'lineno', 0),
            col=getattr(node, 'col_offset', 0),
            node_type=type(node).__name__,
        ))

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.name.split('.')[0]
            if alias.name in BANNED_IMPORTS or name in BANNED_IMPORTS:
                self._add("CRITICAL", "banned_import",
                          f"Banned import: {alias.name}", node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            base = node.module.split('.')[0]
            if node.module in BANNED_IMPORTS or base in BANNED_IMPORTS:
                self._add("CRITICAL", "banned_import",
                          f"Banned import from: {node.module}", node)
        self.generic_visit(node)

    def visit_Call(self, node):
        # Check direct function calls: exec(), eval(), etc.
        if isinstance(node.func, ast.Name):
            if node.func.id in BANNED_FUNCTIONS:
                self._add("CRITICAL", "banned_function",
                          f"Banned function call: {node.func.id}()", node)

        # Check method calls: os.system(), etc.
        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name in BANNED_FUNCTIONS:
                self._add("HIGH", "banned_function",
                          f"Banned method call: .{attr_name}()", node)

        # Check for dynamic code execution patterns
        if isinstance(node.func, ast.Name) and node.func.id == "type":
            if len(node.args) == 3:
                self._add("HIGH", "dynamic_class",
                          "Dynamic class creation via type() — potential sandbox escape", node)

        self.generic_visit(node)

    def visit_Attribute(self, node):
        if node.attr in BANNED_ATTRIBUTES:
            self._add("HIGH", "introspection",
                      f"Dangerous attribute access: .{node.attr}", node)
        self.generic_visit(node)

    def visit_Constant(self, node):
        # Check string constants for path traversal / escape patterns
        if isinstance(node.value, str):
            for pattern in ESCAPE_PATTERNS:
                if pattern in node.value:
                    self._add("MEDIUM", "path_traversal",
                              f"Suspicious path in string: '{node.value[:60]}'", node)
                    break
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Flag functions with suspicious names
        suspicious_names = {"exploit", "payload", "shellcode", "inject",
                            "backdoor", "reverse_shell", "keylog"}
        if node.name.lower() in suspicious_names:
            self._add("HIGH", "suspicious_name",
                      f"Suspicious function name: {node.name}", node)

        # Flag excessive decorator usage (obfuscation)
        if len(node.decorator_list) > 3:
            self._add("LOW", "obfuscation",
                      f"Excessive decorators on {node.name} ({len(node.decorator_list)})", node)

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._add("MEDIUM", "async_code",
                  f"Async function detected: {node.name} — not permitted in SAIF artifacts", node)
        self.generic_visit(node)

    def visit_Global(self, node):
        self._add("LOW", "global_state",
                  f"Global statement: {', '.join(node.names)}", node)
        self.generic_visit(node)

    def visit_Try(self, node):
        # Flag bare except clauses (can swallow security errors)
        for handler in node.handlers:
            if handler.type is None:
                self._add("MEDIUM", "bare_except",
                          "Bare except clause — may swallow security errors", node)
        self.generic_visit(node)


def scan_file(filepath: str) -> Dict[str, Any]:
    """Scan a single Python file and return results."""
    filepath = str(filepath)

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        source = f.read()

    file_hash = hashlib.sha256(source.encode()).hexdigest()

    # Parse
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        return {
            "file": filepath,
            "hash": file_hash,
            "status": "PARSE_ERROR",
            "error": str(e),
            "findings": [],
            "verdict": "REJECT",
        }

    # Scan
    scanner = SecurityScanner(filepath)
    scanner.visit(tree)

    # Compute verdict
    severities = [f.severity for f in scanner.findings]
    if "CRITICAL" in severities:
        verdict = "REJECT"
    elif severities.count("HIGH") >= 2:
        verdict = "REJECT"
    elif "HIGH" in severities:
        verdict = "QUARANTINE"
    elif severities:
        verdict = "FLAG"
    else:
        verdict = "PASS"

    return {
        "file": filepath,
        "hash": file_hash,
        "status": "SCANNED",
        "findings": [f.to_dict() for f in scanner.findings],
        "summary": {
            "critical": severities.count("CRITICAL"),
            "high": severities.count("HIGH"),
            "medium": severities.count("MEDIUM"),
            "low": severities.count("LOW"),
            "total": len(severities),
        },
        "verdict": verdict,
    }


def scan_directory(dirpath: str) -> List[Dict[str, Any]]:
    """Scan all .py files in a directory."""
    results = []
    for path in sorted(Path(dirpath).rglob("*.py")):
        results.append(scan_file(str(path)))
    return results


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.py> | --scan-dir <directory>")
        sys.exit(2)

    if sys.argv[1] == "--scan-dir":
        if len(sys.argv) < 3:
            print("Error: --scan-dir requires a directory path")
            sys.exit(2)
        results = scan_directory(sys.argv[2])
    else:
        results = [scan_file(sys.argv[1])]

    # Output
    report = {
        "scanner": "House Bernard Security Scanner v1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files_scanned": len(results),
        "results": results,
        "overall_verdict": "REJECT" if any(r["verdict"] == "REJECT" for r in results)
                          else "QUARANTINE" if any(r["verdict"] == "QUARANTINE" for r in results)
                          else "FLAG" if any(r["verdict"] == "FLAG" for r in results)
                          else "PASS",
    }

    print(json.dumps(report, indent=2))

    if report["overall_verdict"] == "REJECT":
        sys.exit(1)
    elif report["overall_verdict"] in ("QUARANTINE", "FLAG"):
        sys.exit(0)  # warnings, but not blocking
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

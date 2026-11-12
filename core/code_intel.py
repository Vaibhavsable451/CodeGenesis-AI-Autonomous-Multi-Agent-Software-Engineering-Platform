"""Code intelligence: Python AST parsing, complexity, and heuristic security scan."""
import ast
import re
from pathlib import Path

RISKY = [
    (r"\beval\(", "Use of eval()", "high"),
    (r"\bexec\(", "Use of exec()", "high"),
    (r"subprocess\.\w+\(.*shell\s*=\s*True", "subprocess with shell=True", "high"),
    (r"pickle\.loads?\(", "Unsafe pickle deserialization", "medium"),
    (r"yaml\.load\((?!.*Loader)", "yaml.load without safe Loader", "medium"),
    (r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]", "Possible hardcoded secret", "high"),
    (r"verify\s*=\s*False", "TLS verification disabled", "medium"),
    (r"(?i)select .*['\"]\s*\+|execute\(f['\"]", "Possible SQL injection", "high"),
]
BRANCH_NODES = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.BoolOp,
                ast.ExceptHandler, ast.IfExp, ast.comprehension)


def analyze_python(source: str, path: str = "") -> dict:
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"path": path, "error": f"SyntaxError line {e.lineno}: {e.msg}",
                "functions": [], "classes": [], "imports": []}
    functions, classes, imports = [], [], []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            cx = 1 + sum(isinstance(n, BRANCH_NODES) for n in ast.walk(node))
            functions.append({"name": node.name, "line": node.lineno,
                              "end_line": node.end_lineno, "complexity": cx,
                              "has_docstring": ast.get_docstring(node) is not None})
        elif isinstance(node, ast.ClassDef):
            classes.append({"name": node.name, "line": node.lineno})
        elif isinstance(node, ast.Import):
            imports += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return {"path": path, "functions": functions, "classes": classes,
            "imports": sorted(set(imports)), "loc": len(source.splitlines())}


def security_scan(source: str, path: str = "") -> list[dict]:
    findings = []
    for i, line in enumerate(source.splitlines(), 1):
        for pattern, title, severity in RISKY:
            if re.search(pattern, line):
                findings.append({"path": path, "line": i, "title": title,
                                 "severity": severity, "code": line.strip()[:200]})
    return findings


def scan_repository(root: Path, files: list[dict]) -> dict:
    modules, findings = [], []
    for f in files:
        if not f["analyzable"] or f["language"] != "python":
            continue
        src = (root / f["path"]).read_text(errors="ignore")
        modules.append(analyze_python(src, f["path"]))
        findings += security_scan(src, f["path"])
    complex_fns = sorted(
        ({"path": m["path"], **fn} for m in modules for fn in m["functions"]),
        key=lambda x: -x["complexity"])[:10]
    return {"modules": modules, "security_findings": findings, "most_complex": complex_fns}

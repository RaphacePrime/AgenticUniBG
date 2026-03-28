"""
Script di Analisi Statica per AgenticUniBG Server.
Output: LOC, SLOC, LLOC e Cyclomatic Complexity per ogni classe.
"""
import ast
import os
import textwrap

from radon.complexity import cc_visit
from radon.raw import analyze

SERVER_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "agentic_unibg", "server")
)

def iter_python_files(root_dir):
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(root, name)


def class_metrics_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename=file_path)
    lines = source.splitlines()
    classes = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        if not hasattr(node, "end_lineno") or node.end_lineno is None:
            continue

        class_source = textwrap.dedent("\n".join(lines[node.lineno - 1 : node.end_lineno]))
        raw = analyze(class_source)

        complexity = 1
        for block in cc_visit(class_source):
            if block.__class__.__name__ == "Class" and block.name == node.name:
                complexity = block.complexity
                break

        classes.append(
            {
                "file": os.path.relpath(file_path, SERVER_DIR),
                "class": node.name,
                "loc": raw.loc,
                "sloc": raw.sloc,
                "lloc": raw.lloc,
                "cc": complexity,
            }
        )

    return classes


if not os.path.isdir(SERVER_DIR):
    raise SystemExit(f"Directory non trovata: {SERVER_DIR}")

all_classes = []
for py_file in iter_python_files(SERVER_DIR):
    all_classes.extend(class_metrics_from_file(py_file))

print("file,class,LOC,SLOC,LLOC,CC")
for item in sorted(all_classes, key=lambda x: (x["file"], x["class"])):
    print(
        f"{item['file']},{item['class']},{item['loc']},{item['sloc']},{item['lloc']},{item['cc']}"
    )

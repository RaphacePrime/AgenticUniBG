"""
Script di Analisi Statica per AgenticUniBG Server
Genera metriche usando Radon (CC, MI, Raw, Halstead).
"""
import subprocess
import json
import os
import sys

SERVER_DIR = os.path.join(os.path.dirname(__file__), "agentic_unibg", "server")

def run_radon(args):
    """Run radon via python -m radon for Windows compatibility."""
    return subprocess.run(
        [sys.executable, "-m", "radon"] + args,
        capture_output=True, text=True
    )

# File Python del progetto (escludi __pycache__)
PY_FILES = []
for root, dirs, files in os.walk(SERVER_DIR):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for f in files:
        if f.endswith(".py"):
            PY_FILES.append(os.path.join(root, f))

print("=" * 80)
print("ANALISI STATICA - AGENTIC UNIBG SERVER")
print("=" * 80)
print(f"\nFile Python analizzati: {len(PY_FILES)}")
for f in PY_FILES:
    print(f"  - {os.path.relpath(f, SERVER_DIR)}")

# ─── 1) RADON: Raw Metrics ───────────────────────────────────────
print("\n" + "=" * 80)
print("1. RADON RAW METRICS (LOC, SLOC, Comments, Blank Lines)")
print("=" * 80)
result = run_radon(["raw", "-s", SERVER_DIR])
print(result.stdout)

# ─── 2) RADON: Cyclomatic Complexity ─────────────────────────────
print("=" * 80)
print("2. RADON CYCLOMATIC COMPLEXITY (per function/method/class)")
print("=" * 80)
result = run_radon(["cc", "-s", "-a", "-n", "A", SERVER_DIR])
print(result.stdout)

# Mostra TUTTE le complessità (anche A) per report completo
print("\n--- Dettaglio completo (tutti i gradi) ---")
result_all = run_radon(["cc", "-s", "-a", SERVER_DIR])
print(result_all.stdout)

# ─── 3) RADON: Maintainability Index ─────────────────────────────
print("=" * 80)
print("3. RADON MAINTAINABILITY INDEX (per file)")
print("=" * 80)
result = run_radon(["mi", "-s", SERVER_DIR])
print(result.stdout)

# ─── 4) RADON: Halstead Metrics ──────────────────────────────────
print("=" * 80)
print("4. RADON HALSTEAD METRICS (per function)")
print("=" * 80)
result = run_radon(["hal", SERVER_DIR])
print(result.stdout)

# ─── 5) RADON CC in JSON format (for parsing) ────────────────────
print("=" * 80)
print("5. RADON CC - JSON OUTPUT (for LaTeX tables)")
print("=" * 80)
result = run_radon(["cc", "-s", "-j", SERVER_DIR])
try:
    cc_json = json.loads(result.stdout)
    print(json.dumps(cc_json, indent=2))
except json.JSONDecodeError:
    print(result.stdout)

# ─── 6) RADON MI in JSON format ──────────────────────────────────
print("=" * 80)
print("6. RADON MI - JSON OUTPUT")
print("=" * 80)
result = run_radon(["mi", "-s", "-j", SERVER_DIR])
try:
    mi_json = json.loads(result.stdout)
    print(json.dumps(mi_json, indent=2))
except json.JSONDecodeError:
    print(result.stdout)

# ─── 7) RADON RAW in JSON format ─────────────────────────────────
print("=" * 80)
print("7. RADON RAW - JSON OUTPUT")
print("=" * 80)
result = run_radon(["raw", "-s", "-j", SERVER_DIR])
try:
    raw_json = json.loads(result.stdout)
    print(json.dumps(raw_json, indent=2))
except json.JSONDecodeError:
    print(result.stdout)

print("\n" + "=" * 80)
print("ANALISI COMPLETATA")
print("=" * 80)

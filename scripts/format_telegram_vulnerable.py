from __future__ import annotations

import json
import sys

REPORT_PATH = "reports/pr_security_scan.json"

try:
    with open(REPORT_PATH) as f:
        report = json.load(f)
except FileNotFoundError:
    print("⚠️ Error: Reporte no encontrado.")
    sys.exit(0)

vulnerable_files = [f for f in report["files"] if f["status"] == "VULNERABLE"]
if not vulnerable_files:
    print("  (no vulnerable files listed)")
    sys.exit(0)

parts = []
for f in vulnerable_files:
    pct = f["probability"] * 100
    risk_level = f["risk_level"]
    parts.append(f"📁 <code>{f['path']}</code> — {pct:.1f}% ({risk_level})")

    vuln_types = f.get("vulnerability_types") or []
    for vt in vuln_types:
        parts.append(f"   🛡️ {vt[:100]}")

    syntax_errs = f.get("syntax_errors") or []
    for se in syntax_errs:
        if se.get("code"):
            parts.append(f"   ❌ Línea {se['line']}: <code>{se['code'][:70]}</code>")

    recs = f.get("recommendations") or []
    for r in recs[:1]:
        parts.append(f"   🔧 {r[:120]}")

    parts.append("")

output = "\n".join(parts).rstrip()
print(output)

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

lines = []
for f in report["files"]:
    if f["status"] == "VULNERABLE":
        pct = f["probability"] * 100
        lines.append(f"• <code>{f['path']}</code> - {pct:.1f}% ({f['risk_level']})")
        vuln_types = f.get("vulnerability_types") or []
        if vuln_types:
            lines.append(f"  -> {vuln_types[0]}")
        syntax_errs = f.get("syntax_errors") or []
        for se in syntax_errs:
            if se.get("code"):
                lines.append(f"  Línea {se['line']}: <code>{se['code'][:60]}</code>")
        recs = f.get("recommendations") or []
        for r in recs[:1]:
            lines.append(f"  🔧 {r[:80]}")

output = "%0A".join(lines) if lines else "  (no vulnerable files listed)"
print(output, end="")

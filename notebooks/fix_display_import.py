"""Patch train_vulnerability_model.ipynb to add 'from IPython.display import display' import."""
import json
from pathlib import Path

nb_path = Path(__file__).parent / "train_vulnerability_model.ipynb"
nb = json.loads(nb_path.read_text(encoding="utf-8"))

IMPORT_LINE = "from IPython.display import display\n"

for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        # Add import to the very first code cell (the config cell)
        if IMPORT_LINE not in cell["source"] and "from IPython.display import display" not in "".join(cell["source"]):
            cell["source"].insert(0, IMPORT_LINE)
            print(f"✅ Added '{IMPORT_LINE.strip()}' to first code cell.")
        else:
            print("ℹ️  Import already present, nothing to do.")
        break

nb_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("📝 Notebook saved.")

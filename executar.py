# Launcher v3 — Code Runner deve mostrar esta linha no topo.
print("=== Financeiro launcher v3 ===")
import os
import subprocess
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
PYTHON_VENV = PASTA / "venv" / "Scripts" / "python.exe"

if __name__ == "__main__":
    if not PYTHON_VENV.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(PASTA / "venv")])
    subprocess.check_call([str(PYTHON_VENV), "-m", "pip", "install", "-r", str(PASTA / "requirements.txt"), "-q"])
    ambiente = os.environ.copy()
    ambiente["PYTHONPATH"] = str(PASTA)
    sys.exit(
        subprocess.call(
            [str(PYTHON_VENV), "-m", "src.main"],
            cwd=str(PASTA),
            env=ambiente,
        )
    )

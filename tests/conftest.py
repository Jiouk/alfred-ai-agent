import os
import sys
from pathlib import Path

# Ensure project root is importable as `app` during test execution.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Required for bot pool import during admin router tests.
os.environ.setdefault("FERNET_KEY", "NE-KZSMcnorfPasnnlKSaNb5AN7OQ9ZKuyStmF-a1D0=")

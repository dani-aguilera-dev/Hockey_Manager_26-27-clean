import sys
from pathlib import Path

MANAGER = Path(__file__).resolve().parents[2]
if str(MANAGER) not in sys.path:
    sys.path.insert(0, str(MANAGER))

"""Puts the examples folder on the import path, so the tests can `import lib` from any working directory.

The tests live in lib/tests, which is not a package, so pytest would otherwise add only that folder to sys.path.
"""
import sys
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[2]  # examples/, the folder that holds lib/
if str(EXAMPLES) not in sys.path:
    sys.path.insert(0, str(EXAMPLES))

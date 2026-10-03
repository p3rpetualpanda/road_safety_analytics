"""
Pytest configuration for the ETL cleaning-function tests.

- Puts the etl/ directory on sys.path so tests can `import load`.
- Stubs out psycopg2 if it isn't installed, because the cleaning
  functions under test don't need a database driver.
"""

import sys
import types
from pathlib import Path

ETL_DIR = Path(__file__).resolve().parent.parent / "etl"
if str(ETL_DIR) not in sys.path:
    sys.path.insert(0, str(ETL_DIR))

try:
    import psycopg2  # noqa: F401
except ImportError:
    _psycopg2 = types.ModuleType("psycopg2")
    _extras = types.ModuleType("psycopg2.extras")
    _extras.execute_values = lambda *a, **k: None
    _psycopg2.extras = _extras
    _psycopg2.connect = lambda *a, **k: None
    sys.modules["psycopg2"] = _psycopg2
    sys.modules["psycopg2.extras"] = _extras

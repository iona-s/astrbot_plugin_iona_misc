from __future__ import annotations

import sys
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent
PLUGIN_ROOT = TESTS_ROOT.parent
PLUGIN_PARENT = PLUGIN_ROOT.parent
ASTRBOT_ROOT = PLUGIN_PARENT.parent.parent

for import_root in (PLUGIN_PARENT, ASTRBOT_ROOT):
    import_root_text = str(import_root)
    if import_root_text not in sys.path:
        sys.path.insert(0, import_root_text)

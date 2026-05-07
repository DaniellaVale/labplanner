import sys
from pathlib import Path
import types
import importlib.util

ROOT = Path(__file__).resolve().parents[1]

sys.path.append(str(ROOT / "backend_core"))
sys.path.append(str(ROOT / "doe_service"))

# Compatibilidade para pyDOE2 em Python 3.12+
imp_module = types.ModuleType("imp")


def load_source(name, pathname):
    spec = importlib.util.spec_from_file_location(name, pathname)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


imp_module.load_source = load_source
sys.modules["imp"] = imp_module
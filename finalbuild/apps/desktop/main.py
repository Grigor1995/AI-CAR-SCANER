"""Legacy Desktop entrypoint; backend lifecycle implementation is centralized."""
import sys
from backend import desktop_runtime as _runtime
if __name__ == '__main__':
    _runtime.run(sys.argv[1:])
else:
    sys.modules[__name__] = _runtime

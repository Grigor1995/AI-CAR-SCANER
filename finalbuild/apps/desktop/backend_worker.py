"""Legacy entrypoint forwarding to the shared server; no backend code here."""
import sys
from backend import server as _server
if __name__ == '__main__':
    _server.main()
else:
    sys.modules[__name__] = _server

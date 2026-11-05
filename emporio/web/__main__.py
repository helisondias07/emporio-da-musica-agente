"""python -m emporio.web"""

import os

from emporio.web.server import serve

if __name__ == "__main__":
    serve(
        host=os.getenv("EMPORIO_HOST", "0.0.0.0"),
        port=int(os.getenv("EMPORIO_PORT", "4721")),
    )

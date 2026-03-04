#!/usr/bin/env python3
"""
Entry point per il backend PyInstaller.

Avvia uvicorn con l'app FastAPI. Usato come script principale nel bundle .exe.

Uso:
    python tools/build/entry_point.py              # porta 8000 (default)
    python tools/build/entry_point.py --port 8002  # porta custom (installer test)
"""

import sys
import uvicorn


def main():
    # Default: porta 8000, ascolta su tutte le interfacce
    port = 8000
    host = "0.0.0.0"

    # Supporta --port NNNN da command line
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        log_level="info",
        # Workers=1 per PyInstaller (multiprocessing.spawn non supportato)
        workers=1,
    )


if __name__ == "__main__":
    main()

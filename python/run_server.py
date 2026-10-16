"""Python sunucusu: python python/run_server.py --port 4173"""

import argparse
from temiz_rota.server import make_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Temiz Rota yerel Python sunucusu")
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Port 1024–65535 arasında olmalı.")
    server = make_server(args.port)
    print(f"Temiz Rota Python hazır: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

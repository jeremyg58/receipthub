import os
import sys
import asyncio

from receipthub.config.loader import load_config, summarize_config, ConfigError
from receipthub.daemon.server_uds import UDSServer
from receipthub.daemon.workers import start_workers, stop_workers

APP_NAME = "ReceiptHub"
DEFAULT_CONFIG = "/etc/receipthub/config.yaml"

async def _run(cfg_path: str) -> int:
    print(f"{APP_NAME} daemon starting", flush=True)
    try:
        cfg = load_config(cfg_path)
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr, flush=True)
        return 1
    except Exception as e:
        print(f"Failed to load config: {e!r}", file=sys.stderr, flush=True)
        return 1

    print(summarize_config(cfg), flush=True)

    server = UDSServer(cfg)
    await server.start()
    print(f"UDS listening at {cfg.socket.path}", flush=True)

    # Start one worker per printer (logs jobs for now)
    worker_tasks = start_workers([p.name for p in cfg.printers], server.queue)
    print(f"Workers started: {[t.get_name() for t in worker_tasks]}", flush=True)
    print("Commands: status, submit (enqueue). Ctrl+C to exit.", flush=True)

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await stop_workers(worker_tasks)
        await server.stop()
        print(f"{APP_NAME} daemon exited cleanly.", flush=True)
    return 0

def main():
    cfg_path = os.environ.get("RECEIPTHUB_CONFIG", DEFAULT_CONFIG)
    rc = asyncio.run(_run(cfg_path))
    sys.exit(rc)

if __name__ == "__main__":
    main()

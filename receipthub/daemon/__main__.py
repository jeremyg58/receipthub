import os
import sys
import time
import signal

from receipthub.config.loader import load_config, summarize_config, ConfigError

APP_NAME = "ReceiptHub"
DEFAULT_CONFIG = "/etc/receipthub/config.yaml"

_running = True

def _handle_signal(signum, frame):
    global _running
    print(f"{APP_NAME}: received signal {signum}, shutting down...", flush=True)
    _running = False

def main():
    cfg_path = os.environ.get("RECEIPTHUB_CONFIG", DEFAULT_CONFIG)
    print(f"{APP_NAME} daemon starting", flush=True)

    # Load & validate config
    try:
        cfg = load_config(cfg_path)
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to load config: {e!r}", file=sys.stderr, flush=True)
        sys.exit(1)

    print(summarize_config(cfg), flush=True)
    print("Idle (no sockets/DB yet). Press Ctrl+C to exit.", flush=True)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    while _running:
        time.sleep(1)

    print(f"{APP_NAME} daemon exited cleanly.", flush=True)

if __name__ == "__main__":
    main()

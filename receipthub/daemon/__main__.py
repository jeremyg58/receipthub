import os
import sys
import time
import signal

APP_NAME = "ReceiptHub"
DEFAULT_CONFIG = "/etc/receipthub/config.yaml"

_running = True

def _handle_signal(signum, frame):
    global _running
    print(f"{APP_NAME}: received signal {signum}, shutting down...", flush=True)
    _running = False

def main():
    # Config path is not parsed yet; we just display where we'd read from
    cfg = os.environ.get("RECEIPTHUB_CONFIG", DEFAULT_CONFIG)
    exists = "present" if os.path.exists(cfg) else "missing"
    print(f"{APP_NAME} daemon starting", flush=True)
    print(f"Config path: {cfg} ({exists})", flush=True)
    print("No-op mode: not accepting jobs yet. Press Ctrl+C to exit.", flush=True)

    # Graceful shutdown hooks
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # Idle loop (placeholder for server/worker tasks)
    while _running:
        time.sleep(1)

    print(f"{APP_NAME} daemon exited cleanly.", flush=True)

if __name__ == "__main__":
    main()

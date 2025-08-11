# ReceiptHub

Local print hub for same-host producer scripts (e.g., Telegram bot, MLB notifier).  
A single daemon accepts jobs over a UNIX domain socket, validates them, persists to SQLite, schedules by time, and dispatches to per-printer workers.

**Stack:** Python 3.11, asyncio, UNIX socket, SQLite (WAL), CLI (`rh`).

---

## Features

### ✅ Current Functionality
- **Packaging & CLI**: `pyproject.toml`; `rh` CLI with `status` and `submit` commands.
- **Config loader**: YAML → dataclasses with validation; file mode parser supports `660`, `"660"`, `0o660`.
- **Daemon**: `python -m receipthub.daemon`; loads config; opens DB; starts UNIX domain socket (UDS) server.
- **UDS server**: newline-delimited JSON; commands: `status`, `submit`.
- **Queue (in‑memory)**: time-aware heap; jobs have `run_at` (epoch); accepts `not_before` as epoch or ISO‑8601 (`...Z` supported).
- **Workers**: one per printer; consume queue and **log** jobs (no printing yet).
- **SQLite**: schema + insert on submit; startup recovery loads `queued` jobs back into scheduler.

### 🔜 Planned Features
1. Workers update DB: `running` → `succeeded` / `failed`; retries with backoff; DLQ.
2. Printing pipeline: ESC/POS network output; text/QR/image renderers; emoji map; header/wrap.
3. CLI/admin: `queue` list, `requeue`, `testprint`, maybe `cancel`.
4. System mode: systemd unit, `/etc/receipthub/config.yaml`, `/var/lib/receipthub/receipthub.db`, group/permissions.
5. Baseball job type (scoring events), after core pipeline is stable.

---

## Installation

### Development Setup
```bash
# Clone the repo
git clone https://github.com/jeremyg58/receipthub.git
cd receipthub

# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

---

## Usage

### Start the daemon (development config)
```bash
RECEIPTHUB_CONFIG=./config/config.dev.yaml python -m receipthub.daemon
```

### CLI examples
```bash
# Status
rh status --socket ./run/receipthub.sock

# Submit a text job
rh submit --socket ./run/receipthub.sock --json '{
  "type": "text",
  "source": "dev",
  "printer": "default",
  "payload": { "body": "hello" }
}'
```

**Environment variables:**
- `RECEIPTHUB_CONFIG` — config file path
- `RECEIPTHUB_SOCKET` — default socket path for CLI
- `RECEIPTHUB_DB` — SQLite DB path (default: `./run/receipthub.db` in dev)

---

## Protocol

**Request** (one JSON object per line):

```json
{ "cmd": "status" }
{ "cmd": "submit", "job": { ... } }
```

**Job envelope:**
```json
{
  "type": "text" | "qr" | "image" | "raw_ops",
  "source": "producer-name",
  "printer": "default",
  "priority": 0,
  "not_before": 1733596800 | "2025-12-08T00:00:00Z",
  "payload": { ... }
}
```

**Payload formats:**
- **text**: `{ "body": "..." }`
- **qr**: `{ "data": "...", "size": 1-16, "caption"?: "..." }`
- **image**: `{ "image_b64": "...", "caption"?: "...", "max_width_px"?: 64-1024 }`
- **raw_ops**: `{ "ops": [{ "op": "...", ...}] }`

**Responses:**
- `status`: `{ ok, queue_depth, next_due_epoch|null, printers: [...] }`
- `submit`: `{ ok:true, accepted:true, job_id }` or `{ ok:false, error }`

---

## Repository Layout

```
receipthub/
  cli/main.py                # rh CLI (status, submit)
  daemon/__main__.py         # daemon entrypoint
  daemon/server_uds.py       # UNIX socket server
  daemon/queue_mem.py        # in-memory scheduler
  daemon/workers.py          # per-printer workers (logging only)
  daemon/storage_sqlite.py   # SQLite helpers
  config/loader.py           # YAML → dataclass + validation
config/
  config.sample.yaml         # example config
  config.dev.yaml            # development config
run/                         # dev runtime (socket, DB)
```

---

## Troubleshooting

- **Socket perms**: `socket.mode` supports `660`, `"660"`, `0o660`.
- **CLI can't connect**: daemon not running or wrong `--socket` path.
- **VS Code can't find venv**: Python: Select Interpreter → `./.venv/bin/python`.
- **Duplicate enqueue**: ensure only one `queue.put(...)` call per job.

---

## License

MIT License — see [`LICENSE`](LICENSE) for details.

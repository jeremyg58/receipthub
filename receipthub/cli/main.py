import argparse
import json
import socket
import os

DEFAULT_SOCKET = os.environ.get("RECEIPTHUB_SOCKET", "./run/receipthub.sock")

def cmd_status(args: argparse.Namespace) -> int:
    path = args.socket or DEFAULT_SOCKET
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(path)
        s.sendall(b'{"cmd":"status"}\n')
        data = s.recv(65536)
        s.close()
    except FileNotFoundError:
        print(f"Socket not found: {path}")
        return 2
    except ConnectionRefusedError:
        print(f"Cannot connect to socket: {path}")
        return 3
    except Exception as e:
        print(f"Error: {e}")
        return 4

    try:
        obj = json.loads(data.decode("utf-8").strip())
    except Exception:
        print(data.decode("utf-8", "replace").strip())
        return 0

    print(json.dumps(obj, indent=2))
    return 0

def main():
    p = argparse.ArgumentParser(prog="rh", description="ReceiptHub CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_status = sub.add_parser("status", help="Query daemon status")
    p_status.add_argument("--socket", help="Path to UDS (default: ./run/receipthub.sock or $RECEIPTHUB_SOCKET)")
    p_status.set_defaults(func=cmd_status)

    p_submit = sub.add_parser("submit", help="Submit a job (JSON object for 'job')")
    p_submit.add_argument("--socket", help="Path to UDS (default: ./run/receipthub.sock or $RECEIPTHUB_SOCKET)")
    p_submit.add_argument("--json", required=True, help="Job JSON (e.g. '{\"type\":\"text\",\"source\":\"dev\",\"printer\":\"default\",\"payload\":{\"body\":\"hi\"}}')")
    p_submit.set_defaults(func=cmd_submit)


    args = p.parse_args()
    rc = args.func(args)
    raise SystemExit(rc)

def cmd_submit(args: argparse.Namespace) -> int:
    path = args.socket or DEFAULT_SOCKET
    try:
        job = json.loads(args.json)
    except Exception as e:
        print(f"Job JSON parse error: {e}")
        return 2

    req = {"cmd": "submit", "job": job}

    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(path)
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        data = s.recv(65536)
        s.close()
    except FileNotFoundError:
        print(f"Socket not found: {path}")
        return 3
    except Exception as e:
        print(f"Error: {e}")
        return 4

    print(data.decode("utf-8").strip())
    return 0

"""
UNIX domain socket server for ReceiptHub (skeleton with start()).
We bind the socket and accept connections, but don't handle any commands yet.
"""

from __future__ import annotations
import asyncio
import os
import grp
from typing import Optional
import json



# We’ll accept connections and immediately close them for now.
# Command handling comes next.


class UDSServer:
    def __init__(self, cfg):
        self.cfg = cfg
        self._server: Optional[asyncio.AbstractServer] = None
        self._socket_path = cfg.socket.path

    async def start(self) -> None:
        """Bind the UNIX socket and start accepting connections (no-op handler)."""
        # Ensure parent directory
        parent = os.path.dirname(self._socket_path) or "."
        os.makedirs(parent, exist_ok=True)

        # Remove stale socket
        try:
            if os.path.exists(self._socket_path):
                os.unlink(self._socket_path)
        except FileNotFoundError:
            pass

        # Start the asyncio UNIX server with a no-op handler
        self._server = await asyncio.start_unix_server(self._handle_client, path=self._socket_path)

        # Set permissions
        try:
            os.chmod(self._socket_path, self.cfg.socket.mode)
        except Exception:
            pass

        # Set group if configured
        if self.cfg.socket.group:
            try:
                gid = grp.getgrnam(self.cfg.socket.group).gr_gid
                os.chown(self._socket_path, -1, gid)
            except Exception:
                pass

    async def stop(self) -> None:
        """Close the server and remove the socket file."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        try:
            if os.path.exists(self._socket_path):
                os.unlink(self._socket_path)
        except Exception:
            pass

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            line = await reader.readline()
            if not line:
                return
            try:
                req = json.loads(line.decode("utf-8").strip())
            except Exception as e:
                await self._send(writer, {"ok": False, "error": f"invalid_json: {e}"})
                return

            if req.get("cmd") == "status":
                printers = [{
                    "name": p.name,
                    "state": "idle",   # placeholder until workers exist
                    "host": p.host,
                    "port": p.port,
                    "cols": p.cols,
                } for p in self.cfg.printers]
                await self._send(writer, {"ok": True, "queue_depth": 0, "printers": printers})
            else:
                await self._send(writer, {"ok": False, "error": f"unknown_cmd: {req.get('cmd')!r}"})
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _send(self, writer: asyncio.StreamWriter, obj: dict) -> None:
        data = json.dumps(obj, separators=(",", ":")).encode("utf-8") + b"\n"
        writer.write(data)
        await writer.drain()

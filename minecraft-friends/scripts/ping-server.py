#!/usr/bin/env python3
"""Minecraft Java Server List Ping (status query)."""
from __future__ import annotations

import json
import socket
import struct
import sys


def encode_varint(value: int) -> bytes:
    out = bytearray()
    value &= 0xFFFFFFFF
    while True:
        bits = value & 0x7F
        value >>= 7
        if value:
            out.append(bits | 0x80)
        else:
            out.append(bits)
            break
    return bytes(out)


def encode_string(text: str) -> bytes:
    data = text.encode("utf-8")
    return encode_varint(len(data)) + data


def pack_packet(payload: bytes) -> bytes:
    return encode_varint(len(payload)) + payload


def read_varint(buf: bytes, offset: int) -> tuple[int, int]:
    num = 0
    for i in range(5):
        if offset >= len(buf):
            raise ConnectionError("truncated varint")
        val = buf[offset]
        offset += 1
        num |= (val & 0x7F) << (7 * i)
        if not val & 0x80:
            return num, offset
    raise ConnectionError("varint too long")


def ping(host: str = "127.0.0.1", port: int = 25565, timeout: float = 8.0) -> dict:
    handshake = (
        b"\x00"
        + encode_varint(0)
        + encode_string(host)
        + struct.pack(">H", port)
        + encode_varint(1)
    )
    with socket.create_connection((host, port), timeout) as sock:
        sock.sendall(pack_packet(handshake))
        sock.sendall(pack_packet(b"\x00"))
        # Read packet length, then the rest of the packet.
        raw = b""
        length = None
        consumed = 0
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionError("server closed the status connection")
            raw += chunk
            try:
                length, consumed = read_varint(raw, 0)
            except ConnectionError:
                continue
            if len(raw) - consumed >= length:
                break
        packet = raw[consumed : consumed + length]
        packet_id, off = read_varint(packet, 0)
        if packet_id != 0:
            raise ConnectionError(f"unexpected status packet id {packet_id}")
        json_len, off = read_varint(packet, off)
        payload = packet[off : off + json_len]
        return json.loads(payload.decode("utf-8"))


def main() -> int:
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 25565
    try:
        data = ping(host, port)
    except OSError as exc:
        print(f"protocol: down ({exc})")
        return 1
    version = (data.get("version") or {}).get("name", "unknown")
    players = data.get("players") or {}
    description = data.get("description")
    if isinstance(description, dict):
        motd = description.get("text") or json.dumps(description, ensure_ascii=False)
    else:
        motd = str(description)
    print(f"protocol: up")
    print(f"version: {version}")
    print(f"players: {players.get('online', '?')}/{players.get('max', '?')}")
    print(f"motd: {motd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

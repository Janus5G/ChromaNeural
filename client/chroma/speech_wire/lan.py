"""Bounded TCP transport for the existing Frame v1 bytes (NOT a new protocol)."""
from __future__ import annotations

import socket
import struct

from .frame import Frame, FrameError, HEADER, CRC, SHA256_LEN, MAX_FRAME_PAYLOAD

LENGTH = struct.Struct('>I')
MAX_PACKET = HEADER.size + MAX_FRAME_PAYLOAD + CRC.size + SHA256_LEN


def packet_bytes(frame: Frame) -> bytes:
    raw = frame.encode()
    if len(raw) > MAX_PACKET:
        raise FrameError('packet exceeds maximum size')
    return LENGTH.pack(len(raw)) + raw


def read_exact(sock: socket.socket, length: int, *, allow_clean_eof: bool = False) -> bytes | None:
    chunks = bytearray()
    while len(chunks) < length:
        chunk = sock.recv(length - len(chunks))
        if not chunk:
            if not chunks and allow_clean_eof:
                return None
            raise ConnectionError('truncated TCP packet')
        chunks.extend(chunk)
    return bytes(chunks)


def receive_frame(sock: socket.socket) -> Frame | None:
    prefix = read_exact(sock, LENGTH.size, allow_clean_eof=True)
    if prefix is None:
        return None
    size = LENGTH.unpack(prefix)[0]
    if size < HEADER.size + CRC.size + SHA256_LEN or size > MAX_PACKET:
        raise FrameError('invalid length-prefixed packet size')
    raw = read_exact(sock, size)
    assert raw is not None
    return Frame.decode(raw)


def send_frame(sock: socket.socket, frame: Frame) -> None:
    sock.sendall(packet_bytes(frame))

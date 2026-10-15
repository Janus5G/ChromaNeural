from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import hashlib
import struct
import zlib

MAGIC = b"PRSM"
PROTOCOL_VERSION = 1
HEADER = struct.Struct(">4sBBBBHHIIHHI")
CRC = struct.Struct(">I")
SHA256_LEN = 32
MAX_FRAME_PAYLOAD = 65535


class FrameType(IntEnum):
    DATA = 1
    ACK = 2
    NACK = 3
    DISCOVERY = 4
    SYNC = 5
    CALIBRATION = 6
    RESYNC = 7


class FrameError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Frame:
    source: int
    destination: int
    sequence: int
    message_id: int
    payload: bytes = b""
    frame_type: FrameType = FrameType.DATA
    flags: int = 0
    fragment_index: int = 0
    fragment_count: int = 1

    def validate(self) -> None:
        for name, value, max_value in (
            ("source", self.source, 0xFFFF),
            ("destination", self.destination, 0xFFFF),
            ("sequence", self.sequence, 0xFFFFFFFF),
            ("message_id", self.message_id, 0xFFFFFFFF),
            ("fragment_index", self.fragment_index, 0xFFFF),
            ("fragment_count", self.fragment_count, 0xFFFF),
        ):
            if not isinstance(value, int) or not 0 <= value <= max_value:
                raise FrameError(f"invalid {name}")
        if not isinstance(self.frame_type, FrameType):
            raise FrameError("invalid frame type")
        if not isinstance(self.flags, int) or not 0 <= self.flags <= 0xFF:
            raise FrameError("invalid flags")
        if not isinstance(self.payload, (bytes, bytearray, memoryview)):
            raise FrameError("payload must be bytes-like")
        if len(self.payload) > MAX_FRAME_PAYLOAD:
            raise FrameError("payload exceeds maximum frame size")
        if self.fragment_count < 1 or self.fragment_index >= self.fragment_count:
            raise FrameError("invalid fragmentation metadata")

    def encode(self) -> bytes:
        self.validate()
        payload = bytes(self.payload)
        header = HEADER.pack(
            MAGIC,
            PROTOCOL_VERSION,
            int(self.frame_type),
            self.flags,
            0,
            self.source,
            self.destination,
            self.sequence,
            self.message_id,
            self.fragment_index,
            self.fragment_count,
            len(payload),
        )
        body = header + payload
        crc = CRC.pack(zlib.crc32(body) & 0xFFFFFFFF)
        digest = hashlib.sha256(body + crc).digest()
        return body + crc + digest

    @classmethod
    def decode(cls, raw: bytes) -> "Frame":
        if not isinstance(raw, (bytes, bytearray, memoryview)):
            raise TypeError("raw frame must be bytes-like")
        data = bytes(raw)
        min_len = HEADER.size + CRC.size + SHA256_LEN
        if len(data) < min_len:
            raise FrameError("truncated frame")
        header = data[: HEADER.size]
        (
            magic,
            version,
            frame_type,
            flags,
            reserved,
            source,
            destination,
            sequence,
            message_id,
            fragment_index,
            fragment_count,
            payload_len,
        ) = HEADER.unpack(header)
        if magic != MAGIC:
            raise FrameError("bad magic")
        if version != PROTOCOL_VERSION:
            raise FrameError("unsupported protocol version")
        if reserved != 0:
            raise FrameError("reserved header byte must be zero")
        expected_len = HEADER.size + payload_len + CRC.size + SHA256_LEN
        if len(data) != expected_len:
            raise FrameError("frame length mismatch")
        payload_end = HEADER.size + payload_len
        payload = data[HEADER.size:payload_end]
        body = data[:payload_end]
        received_crc = CRC.unpack(data[payload_end : payload_end + CRC.size])[0]
        expected_crc = zlib.crc32(body) & 0xFFFFFFFF
        if received_crc != expected_crc:
            raise FrameError("CRC32 mismatch")
        received_digest = data[-SHA256_LEN:]
        expected_digest = hashlib.sha256(data[:-SHA256_LEN]).digest()
        if received_digest != expected_digest:
            raise FrameError("SHA-256 mismatch")
        try:
            ft = FrameType(frame_type)
        except ValueError as exc:
            raise FrameError("unknown frame type") from exc
        frame = cls(
            source=source,
            destination=destination,
            sequence=sequence,
            message_id=message_id,
            payload=payload,
            frame_type=ft,
            flags=flags,
            fragment_index=fragment_index,
            fragment_count=fragment_count,
        )
        frame.validate()
        return frame

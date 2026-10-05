"""Bridge between Refract Editor, PRISME's 256 bytes, and OPTB v1 streams.

The bridge uses PRISME's supplied R/G/B/V base-4 mapping and UV checksum.
It does not introduce source metadata, a second byte alphabet, or a competing
compiler. OPTB serializes each five-channel flash as five adjacent states.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
import struct
import zlib


MAGIC = b"OPTB"
FORMAT_VERSION = 1
FLAG_MSB_FIRST = 1
FLAG_SELF_DESCRIBING_MAPPING = 2
FIXED_HEADER = struct.Struct("<4sBBHIIQBBBBHHHII")
PRISME_WAVELENGTHS = (0.350, 0.410, 0.470, 0.530, 0.630)
PRISME_POLARIZATIONS = (0.0, 90.0)
PRISME_INTENSITIES = (0.07, 0.34, 0.66, 1.0)


class OpticalFormatError(ValueError):
    """Raised for invalid or unsupported optical streams."""


@dataclass(slots=True)
class OpticalStream:
    rows: int
    columns: int
    wavelength_bins_um: tuple[float, ...]
    polarization_bins_deg: tuple[float, ...]
    intensity_bins: tuple[float, ...]
    symbols: list[int]
    wavelength_bits: int
    polarization_bits: int
    intensity_bits: int
    flags: int = FLAG_MSB_FIRST | FLAG_SELF_DESCRIBING_MAPPING

    @property
    def bits_per_symbol(self) -> int:
        return self.wavelength_bits + self.polarization_bits + self.intensity_bits

    def split_symbol(self, symbol: int) -> tuple[int, int, int]:
        i_mask = (1 << self.intensity_bits) - 1
        p_mask = (1 << self.polarization_bits) - 1
        intensity = symbol & i_mask
        polarization = (symbol >> self.intensity_bits) & p_mask
        wavelength = symbol >> (self.polarization_bits + self.intensity_bits)
        return wavelength, polarization, intensity


def _bits_required(count: int) -> int:
    if count < 2:
        raise OpticalFormatError("Each mapping axis needs at least two bins.")
    return max(1, math.ceil(math.log2(count)))


def decode_optb(content: bytes) -> OpticalStream:
    if len(content) < FIXED_HEADER.size:
        raise OpticalFormatError("OPTB header is truncated.")
    (
        magic,
        version,
        flags,
        header_size,
        rows,
        columns,
        symbol_count,
        w_bits,
        p_bits,
        i_bits,
        symbol_bits,
        w_count,
        p_count,
        i_count,
        payload_size,
        expected_crc,
    ) = FIXED_HEADER.unpack_from(content)
    if magic != MAGIC or version != FORMAT_VERSION:
        raise OpticalFormatError("Not a supported OPTB v1 stream.")
    if not flags & FLAG_MSB_FIRST:
        raise OpticalFormatError("Only MSB-first OPTB streams are supported.")
    if symbol_bits != w_bits + p_bits + i_bits or not 1 <= symbol_bits <= 63:
        raise OpticalFormatError("Invalid OPTB symbol width.")
    mapping_size = 4 * (w_count + p_count + i_count)
    if header_size != FIXED_HEADER.size + mapping_size:
        raise OpticalFormatError("OPTB mapping size does not match its header.")
    if len(content) != header_size + payload_size:
        raise OpticalFormatError("OPTB payload length does not match its header.")
    if rows * columns != symbol_count:
        raise OpticalFormatError("OPTB dimensions do not match the symbol count.")

    payload = content[header_size:]
    if zlib.crc32(payload) & 0xFFFFFFFF != expected_crc:
        raise OpticalFormatError("OPTB CRC32 validation failed.")
    needed_bytes = (symbol_count * symbol_bits + 7) // 8
    if payload_size != needed_bytes:
        raise OpticalFormatError("OPTB packed payload has an invalid size.")

    floats = struct.unpack_from(
        f"<{w_count + p_count + i_count}f", content, FIXED_HEADER.size
    )
    w_end = w_count
    p_end = w_count + p_count
    all_bits = "".join(f"{byte:08b}" for byte in payload)
    symbols = [
        int(all_bits[offset : offset + symbol_bits], 2)
        for offset in range(0, symbol_count * symbol_bits, symbol_bits)
    ]

    stream = OpticalStream(
        rows=rows,
        columns=columns,
        wavelength_bins_um=tuple(floats[:w_end]),
        polarization_bins_deg=tuple(floats[w_end:p_end]),
        intensity_bins=tuple(floats[p_end:]),
        symbols=symbols,
        wavelength_bits=w_bits,
        polarization_bits=p_bits,
        intensity_bits=i_bits,
        flags=flags,
    )
    for number, symbol in enumerate(symbols):
        w, p, i = stream.split_symbol(symbol)
        if w >= w_count or p >= p_count or i >= i_count:
            raise OpticalFormatError(f"Symbol {number} references a mapping bin that does not exist.")
    return stream


def encode_optb(stream: OpticalStream) -> bytes:
    count = len(stream.symbols)
    if stream.rows * stream.columns != count:
        raise OpticalFormatError("Rows × columns must equal the number of symbols.")
    if stream.bits_per_symbol > 63:
        raise OpticalFormatError("OPTB supports at most 63 bits per symbol.")
    for number, symbol in enumerate(stream.symbols):
        if not 0 <= symbol < (1 << stream.bits_per_symbol):
            raise OpticalFormatError(f"Symbol {number} does not fit the declared width.")
        w, p, i = stream.split_symbol(symbol)
        if (
            w >= len(stream.wavelength_bins_um)
            or p >= len(stream.polarization_bins_deg)
            or i >= len(stream.intensity_bins)
        ):
            raise OpticalFormatError(f"Symbol {number} references an unknown mapping bin.")

    bit_text = "".join(f"{symbol:0{stream.bits_per_symbol}b}" for symbol in stream.symbols)
    padded = bit_text + "0" * ((8 - len(bit_text) % 8) % 8)
    payload = bytes(int(padded[n : n + 8], 2) for n in range(0, len(padded), 8))
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    mapping = struct.pack(
        f"<{len(stream.wavelength_bins_um) + len(stream.polarization_bins_deg) + len(stream.intensity_bins)}f",
        *stream.wavelength_bins_um,
        *stream.polarization_bins_deg,
        *stream.intensity_bins,
    )
    header_size = FIXED_HEADER.size + len(mapping)
    header = FIXED_HEADER.pack(
        MAGIC,
        FORMAT_VERSION,
        stream.flags,
        header_size,
        stream.rows,
        stream.columns,
        count,
        stream.wavelength_bits,
        stream.polarization_bits,
        stream.intensity_bits,
        stream.bits_per_symbol,
        len(stream.wavelength_bins_um),
        len(stream.polarization_bins_deg),
        len(stream.intensity_bins),
        len(payload),
        crc,
    )
    return header + mapping + payload


def _number_list(values: tuple[float, ...]) -> str:
    return ", ".join(f"{value:.9g}" for value in values)


def stream_to_asm4(stream: OpticalStream) -> str:
    lines = [
        "; Spectral IR — lossless OPTB v1 representation",
        "; Each SYMBOL is wavelength-index, polarization-index, intensity-index.",
        ".format OPTB1",
        f".shape {stream.rows}, {stream.columns}",
        f".wavelength_um {_number_list(stream.wavelength_bins_um)}",
        f".polarization_deg {_number_list(stream.polarization_bins_deg)}",
        f".intensity {_number_list(stream.intensity_bins)}",
        "",
    ]
    for address, symbol in enumerate(stream.symbols):
        w, p, i = stream.split_symbol(symbol)
        lines.append(
            f"SYMBOL {w}, {p}, {i}  ; @{address:04d} raw=0x{symbol:0{max(2, (stream.bits_per_symbol + 3) // 4)}X}"
        )
    return "\n".join(lines) + "\n"


def _parse_numbers(text: str, line_number: int) -> tuple[float, ...]:
    try:
        values = tuple(float(value.strip()) for value in text.split(",") if value.strip())
    except ValueError as exc:
        raise OpticalFormatError(f"Line {line_number}: invalid mapping number.") from exc
    if len(values) < 2:
        raise OpticalFormatError(f"Line {line_number}: a mapping needs at least two bins.")
    return values


def asm4_to_stream(source: str) -> OpticalStream:
    rows = columns = None
    wavelengths = polarizations = intensities = None
    triples: list[tuple[int, int, int]] = []
    for line_number, raw_line in enumerate(source.splitlines(), 1):
        line = raw_line.split(";", 1)[0].strip()
        if not line or line.lower() == ".format optb1":
            continue
        if match := re.fullmatch(r"\.shape\s+(\d+)\s*,\s*(\d+)", line, re.I):
            rows, columns = int(match.group(1)), int(match.group(2))
        elif match := re.fullmatch(r"\.wavelength_um\s+(.+)", line, re.I):
            wavelengths = _parse_numbers(match.group(1), line_number)
        elif match := re.fullmatch(r"\.polarization_deg\s+(.+)", line, re.I):
            polarizations = _parse_numbers(match.group(1), line_number)
        elif match := re.fullmatch(r"\.intensity\s+(.+)", line, re.I):
            intensities = _parse_numbers(match.group(1), line_number)
        elif match := re.fullmatch(r"SYMBOL\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", line, re.I):
            triples.append(tuple(map(int, match.groups())))
        else:
            raise OpticalFormatError(f"Line {line_number}: unknown Spectral IR statement.")
    if not all((rows, columns, wavelengths, polarizations, intensities)):
        raise OpticalFormatError("Spectral IR is missing shape or mapping declarations.")
    if rows * columns != len(triples):
        raise OpticalFormatError(
            f"Spectral IR shape is {rows}×{columns}, but contains {len(triples)} symbols."
        )
    w_bits = _bits_required(len(wavelengths))
    p_bits = _bits_required(len(polarizations))
    i_bits = _bits_required(len(intensities))
    symbols: list[int] = []
    for number, (w, p, i) in enumerate(triples):
        if w >= len(wavelengths) or p >= len(polarizations) or i >= len(intensities):
            raise OpticalFormatError(f"Spectral IR symbol {number} references an unknown bin.")
        symbols.append((w << (p_bits + i_bits)) | (p << i_bits) | i)
    return OpticalStream(
        rows=rows,
        columns=columns,
        wavelength_bins_um=wavelengths,
        polarization_bins_deg=polarizations,
        intensity_bins=intensities,
        symbols=symbols,
        wavelength_bits=w_bits,
        polarization_bits=p_bits,
        intensity_bits=i_bits,
    )


def stream_to_json(stream: OpticalStream) -> str:
    states = []
    for address, symbol in enumerate(stream.symbols):
        w, p, i = stream.split_symbol(symbol)
        states.append(
            {
                "address": address,
                "raw": symbol,
                "wavelength_index": w,
                "wavelength_um": stream.wavelength_bins_um[w],
                "polarization_index": p,
                "polarization_deg": stream.polarization_bins_deg[p],
                "intensity_index": i,
                "intensity": stream.intensity_bins[i],
            }
        )
    return json.dumps(
        {
            "format": "OPTB v1",
            "shape": [stream.rows, stream.columns],
            "bits_per_symbol": stream.bits_per_symbol,
            "states": states,
        },
        ensure_ascii=False,
        indent=2,
    )


def stream_to_hex(stream: OpticalStream) -> str:
    width = max(2, (stream.bits_per_symbol + 3) // 4)
    return "\n".join(
        f"{offset:04X}: "
        + " ".join(f"{value:0{width}X}" for value in stream.symbols[offset : offset + 16])
        for offset in range(0, len(stream.symbols), 16)
    )


def _nearest_index(values: tuple[float, ...], target: float, tolerance: float) -> int:
    index = min(range(len(values)), key=lambda item: abs(values[item] - target))
    if abs(values[index] - target) > tolerance:
        raise OpticalFormatError(f"OPTB mapping does not contain the PRISME {target * 1000:.0f} nm channel.")
    return index


def bytes_to_prisme_stream(data: bytes) -> OpticalStream:
    """Encode every byte as the existing five-channel PRISME flash.

    OPTB serializes the simultaneous flash as five adjacent spectral states in
    R, G, B, V, UV order. No source metadata or secondary compiler is added.
    """
    from .prisme_isa import byte_to_levels

    w_bits = _bits_required(len(PRISME_WAVELENGTHS))
    p_bits = _bits_required(len(PRISME_POLARIZATIONS))
    i_bits = _bits_required(len(PRISME_INTENSITIES))
    channel_indices = [
        _nearest_index(PRISME_WAVELENGTHS, wavelength, 0.002)
        for wavelength in (0.630, 0.530, 0.470, 0.410, 0.350)
    ]
    symbols: list[int] = []
    for value in data:
        for wavelength_index, intensity_index in zip(channel_indices, byte_to_levels(value)):
            symbols.append(
                (wavelength_index << (p_bits + i_bits))
                | intensity_index
            )
    return OpticalStream(
        rows=1,
        columns=len(symbols),
        wavelength_bins_um=PRISME_WAVELENGTHS,
        polarization_bins_deg=PRISME_POLARIZATIONS,
        intensity_bins=PRISME_INTENSITIES,
        symbols=symbols,
        wavelength_bits=w_bits,
        polarization_bits=p_bits,
        intensity_bits=i_bits,
    )


def prisme_stream_to_bytes(stream: OpticalStream) -> bytes:
    """Decode five adjacent OPTB states through PRISME's 256-character alphabet."""
    from .prisme_isa import levels_to_byte

    if len(stream.symbols) % 5:
        raise OpticalFormatError("The OPTB stream is not grouped as five-channel PRISME flashes.")
    expected_channels = [
        _nearest_index(stream.wavelength_bins_um, wavelength, 0.012)
        for wavelength in (0.630, 0.530, 0.470, 0.410, 0.350)
    ]
    output = bytearray()
    for offset in range(0, len(stream.symbols), 5):
        levels: list[int] = []
        for position, symbol in enumerate(stream.symbols[offset : offset + 5]):
            wavelength, _polarization, intensity = stream.split_symbol(symbol)
            if wavelength != expected_channels[position]:
                raise OpticalFormatError(
                    f"Flash {offset // 5} does not use R/G/B/V/UV channel order."
                )
            if intensity > 3:
                raise OpticalFormatError(f"Flash {offset // 5} has a non-quaternary intensity.")
            levels.append(intensity)
        try:
            output.append(levels_to_byte(tuple(levels)))
        except ValueError as exc:
            raise OpticalFormatError(f"Flash {offset // 5}: {exc}") from exc
    return bytes(output)


def import_optical(
    content: bytes, view: str = "PRISME ASM", text_encoding: str = "utf-8"
) -> tuple[str, str, OpticalStream]:
    stream = decode_optb(content)
    view_key = view.upper()
    if view_key == "JSON IR":
        return stream_to_json(stream), "JSON IR", stream
    if view_key == "HEX":
        return stream_to_hex(stream), "Hex", stream
    if view_key in {"SPECTRAL IR", "ASM4"}:
        return stream_to_asm4(stream), "Spectral IR", stream
    data = prisme_stream_to_bytes(stream)
    if view_key == "PRISME ASM":
        from .prisme_isa import disassemble

        return disassemble(data), "PRISME ASM", stream
    try:
        return data.decode(text_encoding), view, stream
    except UnicodeDecodeError as exc:
        raise OpticalFormatError(
            f"PRISME bytes are not valid {text_encoding}; choose PRISME ASM or Hex."
        ) from exc


def export_optical(source: str, language: str, text_encoding: str = "utf-8") -> bytes:
    if language.upper() == "PRISME ASM":
        from .prisme_isa import assemble

        data = assemble(source)
    elif language.upper() in {"SPECTRAL IR", "ASM4"}:
        return encode_optb(asm4_to_stream(source))
    else:
        data = source.encode(text_encoding)
    return encode_optb(bytes_to_prisme_stream(data))

"""Python adapter for the existing 256-byte PRISME instruction set.

The instruction layout and assembler rules mirror the supplied prisme.html:
one byte is four base-4 channel levels (R/G/B/V), while UV carries their
modulo-4 checksum.  This module is an editor adapter, not a new compiler.
"""

from __future__ import annotations

import re


REGISTERS = {"A": 0, "B": 1, "C": 2, "D": 3}
REGISTER_NAMES = ("A", "B", "C", "D")

# mnemonic: class, operation, operand form, encoded length
ISA = {
    "NOP": (0, 0, "none", 1),
    "HALT": (0, 1, "none", 1),
    "OUT": (0, 2, "r", 1),
    "EMIT": (0, 3, "r", 1),
    "ADD": (1, 0, "rr", 1),
    "SUB": (1, 1, "rr", 1),
    "MUL": (1, 2, "rr", 1),
    "XOR": (1, 3, "rr", 1),
    "SET": (2, 0, "ri", 2),
    "MOV": (2, 1, "rr", 1),
    "LOAD": (2, 2, "rm", 1),
    "STORE": (2, 3, "mr", 1),
    "JMP": (3, 0, "a", 2),
    "JZ": (3, 1, "a", 2),
    "JNZ": (3, 2, "a", 2),
    "CMP": (3, 3, "rr", 1),
}
OPCODE_TO_MNEMONIC = {(value[0], value[1]): name for name, value in ISA.items()}


class PrismeSyntaxError(ValueError):
    pass


def byte_to_levels(value: int) -> tuple[int, int, int, int, int]:
    value &= 0xFF
    red = (value >> 6) & 3
    green = (value >> 4) & 3
    blue = (value >> 2) & 3
    violet = value & 3
    return red, green, blue, violet, (red + green + blue + violet) % 4


def levels_to_byte(levels: tuple[int, int, int, int, int]) -> int:
    red, green, blue, violet, uv = levels
    if any(level not in range(4) for level in levels):
        raise ValueError("PRISME channel levels must be between 0 and 3.")
    if (red + green + blue + violet) % 4 != uv:
        raise ValueError("PRISME UV checksum does not match the visible channels.")
    return (red << 6) | (green << 4) | (blue << 2) | violet


def _number(token: str, labels: dict[str, int] | None = None) -> int:
    token = token.strip()
    if token.startswith("#"):
        token = token[1:].strip()
    if len(token) == 3 and token[0] == token[-1] == "'":
        return ord(token[1]) & 0xFF
    if re.fullmatch(r"0x[0-9a-f]+", token, re.I):
        return int(token, 16) & 0xFF
    if re.fullmatch(r"-?\d+", token):
        return int(token) % 256
    if labels is not None and token in labels:
        return labels[token]
    raise PrismeSyntaxError(f'Unknown number or label "{token}".')


def _register(token: str) -> int:
    try:
        return REGISTERS[token.strip().upper()]
    except KeyError as exc:
        raise PrismeSyntaxError(f'Unknown register "{token.strip()}".') from exc


def _data_bytes(line: str) -> list[int] | None:
    if match := re.fullmatch(r"\.byte\s+(.+)", line, re.I):
        return [_number(value) for value in match.group(1).split(",")]
    if match := re.fullmatch(r'\.(?:tekst|text)\s+"([^"]*)"(?:\s*,\s*(.*))?', line, re.I):
        values = [ord(character) & 0xFF for character in match.group(1)]
        if match.group(2):
            values.extend(_number(value) for value in match.group(2).split(","))
        return values
    if match := re.fullmatch(r"\.(?:plads|space)\s+(\d+)", line, re.I):
        return [0] * int(match.group(1))
    return None


def assemble(source: str) -> bytes:
    parsed: list[tuple[int, str, str, int]] = []
    labels: dict[str, int] = {}
    address = 0
    for line_number, raw in enumerate(source.splitlines(), 1):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if match := re.match(r"^([A-Za-zÆØÅæøå_][\wÆØÅæøå_]*):\s*(.*)$", line):
            label, line = match.groups()
            if label in labels:
                raise PrismeSyntaxError(f'Line {line_number}: duplicate label "{label}".')
            labels[label] = address
            line = line.strip()
            if not line:
                continue
        if data := _data_bytes(line):
            parsed.append((line_number, ".DATA", ",".join(map(str, data)), address))
            address += len(data)
            continue
        match = re.fullmatch(r"([A-Za-z]+)\s*(.*)", line)
        if not match or match.group(1).upper() not in ISA:
            raise PrismeSyntaxError(f'Line {line_number}: unknown instruction "{line}".')
        mnemonic, args = match.group(1).upper(), match.group(2).strip()
        parsed.append((line_number, mnemonic, args, address))
        address += ISA[mnemonic][3]
    if address > 256:
        raise PrismeSyntaxError(f"Program uses {address} bytes; PRISME memory contains 256.")

    output = bytearray()
    for line_number, mnemonic, args, _ in parsed:
        if mnemonic == ".DATA":
            output.extend(int(value) for value in args.split(","))
            continue
        instruction_class, operation, form, _ = ISA[mnemonic]
        destination = source_register = 0
        extra = None
        parts = [part.strip() for part in args.split(",")] if args else []
        try:
            if form == "none":
                if args:
                    raise PrismeSyntaxError(f"{mnemonic} takes no operands.")
            elif form == "r":
                destination = _register(args)
            elif form == "rr":
                if len(parts) != 2:
                    raise PrismeSyntaxError(f"{mnemonic} requires two registers.")
                destination, source_register = map(_register, parts)
            elif form == "ri":
                if len(parts) != 2:
                    raise PrismeSyntaxError(f"{mnemonic} requires a register and value.")
                destination, extra = _register(parts[0]), _number(parts[1], labels)
            elif form == "rm":
                if len(parts) != 2:
                    raise PrismeSyntaxError(f"{mnemonic} requires register, [register].")
                destination = _register(parts[0])
                match = re.fullmatch(r"\[\s*([A-Da-d])\s*\]", parts[1])
                if not match:
                    raise PrismeSyntaxError("Memory source must be written as [A].")
                source_register = _register(match.group(1))
            elif form == "mr":
                if len(parts) != 2:
                    raise PrismeSyntaxError(f"{mnemonic} requires [register], register.")
                match = re.fullmatch(r"\[\s*([A-Da-d])\s*\]", parts[0])
                if not match:
                    raise PrismeSyntaxError("Memory target must be written as [A].")
                destination, source_register = _register(match.group(1)), _register(parts[1])
            elif form == "a":
                extra = _number(args, labels)
        except PrismeSyntaxError as exc:
            raise PrismeSyntaxError(f"Line {line_number}: {exc}") from exc
        output.append(
            (instruction_class << 6)
            | (operation << 4)
            | (destination << 2)
            | source_register
        )
        if extra is not None:
            output.append(extra)
    return bytes(output)


def disassemble(program: bytes) -> str:
    """Produce assembly that reassembles byte-for-byte."""
    lines = [
        "; PRISME assembler — 256-tegns bytealfabet",
        "; R/G/B/V er fire base-4 cifre; UV er modulo-4 kontrolsum.",
        "",
    ]
    pc = 0
    while pc < len(program):
        value = program[pc]
        instruction_class = (value >> 6) & 3
        operation = (value >> 4) & 3
        destination = (value >> 2) & 3
        source_register = value & 3
        mnemonic = OPCODE_TO_MNEMONIC[(instruction_class, operation)]
        form = ISA[mnemonic][2]
        if ISA[mnemonic][3] == 2 and pc + 1 >= len(program):
            lines.append(f".byte 0x{value:02X} ; @{pc:03d} truncated {mnemonic}")
            break
        text = mnemonic
        if form == "r":
            text += f" {REGISTER_NAMES[destination]}"
        elif form == "rr":
            text += f" {REGISTER_NAMES[destination]}, {REGISTER_NAMES[source_register]}"
        elif form == "rm":
            text += f" {REGISTER_NAMES[destination]}, [{REGISTER_NAMES[source_register]}]"
        elif form == "mr":
            text += f" [{REGISTER_NAMES[destination]}], {REGISTER_NAMES[source_register]}"
        elif form == "ri":
            text += f" {REGISTER_NAMES[destination]}, #{program[pc + 1]}"
        elif form == "a":
            text += f" {program[pc + 1]}"
        levels = byte_to_levels(value)
        lines.append(
            f"{text:<24} ; @{pc:03d} 0x{value:02X} "
            f"R{levels[0]} G{levels[1]} B{levels[2]} V{levels[3]} UV{levels[4]}"
        )
        pc += ISA[mnemonic][3]
    return "\n".join(lines) + "\n"

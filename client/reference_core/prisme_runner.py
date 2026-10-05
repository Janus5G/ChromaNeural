"""Small command-line VM for testing PRISME ASM in Refract Studio."""

from __future__ import annotations

from pathlib import Path
import sys

from prisme_isa import assemble


def run(program: bytes, max_steps: int = 100_000) -> int:
    memory = bytearray(256)
    memory[: len(program)] = program
    registers = [0, 0, 0, 0]
    pc = 0
    zero = False

    for _step in range(max_steps):
        opcode = memory[pc]
        pc = (pc + 1) & 0xFF
        instruction_class = (opcode >> 6) & 3
        operation = (opcode >> 4) & 3
        destination = (opcode >> 2) & 3
        source = opcode & 3

        if instruction_class == 0:
            if operation == 0:  # NOP
                continue
            if operation == 1:  # HALT
                return 0
            if operation == 2:  # OUT
                print(registers[destination])
            elif operation == 3:  # EMIT
                print(chr(registers[destination]), end="", flush=True)
        elif instruction_class == 1:
            if operation == 0:
                registers[destination] = (
                    registers[destination] + registers[source]
                ) & 0xFF
            elif operation == 1:
                registers[destination] = (
                    registers[destination] - registers[source]
                ) & 0xFF
            elif operation == 2:
                registers[destination] = (
                    registers[destination] * registers[source]
                ) & 0xFF
            else:
                registers[destination] ^= registers[source]
            zero = registers[destination] == 0
        elif instruction_class == 2:
            if operation == 0:  # SET
                registers[destination] = memory[pc]
                pc = (pc + 1) & 0xFF
            elif operation == 1:  # MOV
                registers[destination] = registers[source]
            elif operation == 2:  # LOAD
                registers[destination] = memory[registers[source]]
            else:  # STORE
                memory[registers[destination]] = registers[source]
            zero = registers[destination] == 0
        else:
            if operation == 0:  # JMP
                pc = memory[pc]
            elif operation == 1:  # JZ
                target = memory[pc]
                pc = target if zero else (pc + 1) & 0xFF
            elif operation == 2:  # JNZ
                target = memory[pc]
                pc = target if not zero else (pc + 1) & 0xFF
            else:  # CMP
                zero = registers[destination] == registers[source]

    print(f"\nFejl: programmet overskred grænsen på {max_steps} instruktioner.", file=sys.stderr)
    return 124


def main() -> int:
    if len(sys.argv) != 2:
        print("Brug: prisme_runner.py <program.prisme>", file=sys.stderr)
        return 2
    try:
        source = Path(sys.argv[1]).read_text(encoding="utf-8")
        return run(assemble(source))
    except Exception as exc:
        print(f"PRISME-fejl: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

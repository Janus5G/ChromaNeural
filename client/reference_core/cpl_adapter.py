"""Adapter around the byte-exact original ChromaPlex OS compiler package.

The files under vendor/chromaplex-toolchain/chromaplex_os are restored from
chromaplex_os_package.json and must remain unmodified. Compatibility handling
belongs here, outside the original compiler.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys


DESKTOP_ROOT = Path(__file__).resolve().parent.parent
TOOLCHAIN_ROOT = DESKTOP_ROOT / "vendor" / "chromaplex-toolchain"
MAIN_ROOT = DESKTOP_ROOT / "vendor" / "chromaplex-main"

for path in (TOOLCHAIN_ROOT, MAIN_ROOT):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)


@dataclass(frozen=True)
class CPLRunResult:
    dialect: str
    cpa: str
    output: list[int]
    state: str


def _normalize_original_cpl(source: str) -> str:
    """Remove optional line-ending semicolons before the original regex parser.

    The package examples use semicolons, while its original greedy expression
    parser includes them in numeric expressions. Normalizing the accepted
    delimiter keeps compiler.py byte-identical to its JSON/Git source.
    """

    normalized = []
    for line in source.splitlines():
        content, marker, comment = line.partition("//")
        content = re.sub(r";\s*$", "", content)
        normalized.append(content + (marker + comment if marker else ""))
    return "\n".join(normalized)


def _compile_original_cpl(source: str) -> tuple[str, str]:
    from chromaplex_os.compiler import CPLCompiler

    cpa = CPLCompiler().compile(_normalize_original_cpl(source))
    return cpa, "original ChromaPlex OS CPL v1.0.0"


def _compile_specification_cpl(source: str) -> tuple[str, str]:
    from chromaplex.cpl_compiler import compile_cpl as compile_specification

    return (
        compile_specification(source),
        "current chromaplex-os specification CPL",
    )


def compile_cpl(source: str) -> tuple[str, str]:
    """Route the two documented CPL dialects to their matching Git compiler."""

    if re.search(
        r"(?m)^\s*(?:tal|potens|streng|konstant|pixel|skriv_voxel|kanal)\b",
        source,
    ):
        return _compile_specification_cpl(source)
    if re.search(r"(?m)^\s*(?:var|store|load|print)\b", source):
        return _compile_original_cpl(source)

    errors = []
    for compiler in (_compile_original_cpl, _compile_specification_cpl):
        try:
            return compiler(source)
        except Exception as exc:
            errors.append(str(exc))
    raise SyntaxError("Ingen dokumenteret CPL-dialekt accepterede koden:\n" + "\n".join(errors))


def _normalize_original_cpa(cpa: str) -> str:
    """Normalize named colours for the original assembler's eager fallback."""

    from chromaplex_os.spec import COLOUR_NAMES

    def replace_colour(match):
        name = match.group(1).upper()
        return f"SET_COLOR {COLOUR_NAMES[name]}"

    return re.sub(
        r"(?mi)^\s*SET_COLOR\s+(UV|VIOLET|BLUE|GREEN|RED)\s*$",
        replace_colour,
        cpa,
    )


def _run_original_cpa(cpa: str) -> tuple[list[int], str]:
    """Execute original CPA and support its compiler-emitted PRINT pseudo-op."""

    from chromaplex_os.assembler import assemble
    from chromaplex_os.vm import VirtualMachine

    vm = VirtualMachine()
    output = []
    segment = []

    def execute_segment():
        if not segment:
            return
        text = _normalize_original_cpa("\n".join(segment))
        if not re.search(r"(?m)^\s*HALT\s*$", text):
            text += "\nHALT"
        vm.load_program(assemble(text))
        vm.run()
        segment.clear()

    for raw_line in cpa.splitlines():
        match = re.match(r"^\s*PRINT\s+R([0-7])\s*$", raw_line, re.I)
        if match:
            execute_segment()
            output.append(vm.registers[int(match.group(1))])
        else:
            segment.append(raw_line)
    execute_segment()
    return output, f"Registre: {vm.registers}\nKrystallager: {vm.storage.stats()}"


def _run_specification_cpa(cpa: str) -> tuple[list[int], str]:
    from chromaplex.cpa_assembler import assemble
    from chromaplex.crystal_simulator import CrystalSimulator

    simulator = CrystalSimulator()
    output = simulator.execute_program(assemble(cpa))
    return output, (
        f"Registre: {simulator.registers}\n"
        f"Voxels i brug: {len(simulator._grid)}"
    )


def run_cpl(source: str) -> CPLRunResult:
    cpa, dialect = compile_cpl(source)
    if dialect.startswith("original"):
        output, state = _run_original_cpa(cpa)
    else:
        output, state = _run_specification_cpa(cpa)
    return CPLRunResult(dialect, cpa, output, state)


def run_cpa(source: str) -> CPLRunResult:
    if re.search(r"(?mi)^\s*(?:LOAD\.|STORE\.|OUT\b|IN\b|JMP\.IF\b)", source):
        output, state = _run_specification_cpa(source)
        dialect = "current chromaplex-os specification CPA"
    else:
        output, state = _run_original_cpa(source)
        dialect = "original ChromaPlex OS CPA v1.0.0"
    return CPLRunResult(dialect, source, output, state)

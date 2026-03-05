#!/usr/bin/env python3
"""Cross-platform downloader wrapper for easyeda2kicad."""

from __future__ import annotations

import subprocess
import sys
import os
import shutil
import venv
from pathlib import Path


def prompt_choice(prompt: str, valid: set[str]) -> str:
    while True:
        value = input(prompt).strip()
        if value in valid:
            return value
        print(f"Please type one of: {', '.join(sorted(valid))}")


def prompt_yes_no(prompt: str) -> bool:
    while True:
        value = input(prompt).strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please type Y or N.")


def get_venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def module_available(python_executable: str | Path) -> bool:
    result = subprocess.run(
        [str(python_executable), "-c", "import easyeda2kicad"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def create_and_install_venv(venv_dir: Path) -> list[str] | None:
    python_in_venv = get_venv_python(venv_dir)

    if not python_in_venv.exists():
        print()
        print(f'Creating local virtual environment: "{venv_dir}"')
        try:
            venv.EnvBuilder(with_pip=True).create(str(venv_dir))
        except Exception:
            print("Failed to create virtual environment.")
            return None

    print("Installing easyeda2kicad (first run may take a moment)...")
    install = subprocess.run(
        [str(python_in_venv), "-m", "pip", "install", "easyeda2kicad"], check=False
    )
    if install.returncode != 0:
        print("Failed to install easyeda2kicad in local virtual environment.")
        return None

    if not module_available(python_in_venv):
        print("easyeda2kicad is still unavailable after installation.")
        return None

    return [str(python_in_venv), "-m", "easyeda2kicad"]


def resolve_easyeda_runner(script_dir: Path) -> list[str] | None:
    if module_available(sys.executable):
        return [sys.executable, "-m", "easyeda2kicad"]

    cli_cmd = shutil.which("easyeda2kicad")
    if cli_cmd:
        return [cli_cmd]

    venv_dir = script_dir / ".easyeda2kicad-venv"
    python_in_venv = get_venv_python(venv_dir)

    if python_in_venv.exists() and module_available(python_in_venv):
        return [str(python_in_venv), "-m", "easyeda2kicad"]

    print()
    print("easyeda2kicad was not found in this Python environment.")
    if not prompt_yes_no(
        'Create local venv ".easyeda2kicad-venv" and install now? [Y]=Yes [N]=No : '
    ):
        print("Cannot continue without easyeda2kicad.")
        print("Tip: run this script again and choose Y, or install manually.")
        return None

    return create_and_install_venv(venv_dir)


def get_output_dir() -> Path | None:
    print()
    print("Example path:")
    print("  C:\\Projects\\MyPCB\\kicad_lib")
    print()
    print("Tip: spaces are OK.")
    print()

    raw_path = input("Type the destination folder path: ").strip().strip('"').strip("'")
    if not raw_path:
        print("Folder not provided.")
        return None

    output_dir = Path(raw_path).expanduser()

    if not output_dir.exists():
        print()
        print("Folder does not exist:")
        print(f'"{output_dir}"')
        print()
        if not prompt_yes_no("Create this folder? [Y]=Yes [N]=No : "):
            print("Cancelled.")
            return None
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            print("Failed to create folder.")
            return None

    return output_dir


def run_easyeda2kicad(
    easyeda_runner: list[str], lcsc_id: str, output_dir: Path | None
) -> int:
    cmd = [*easyeda_runner, "--full", "--overwrite", f"--lcsc_id={lcsc_id}"]

    if output_dir is not None:
        cmd.extend(["--output", str(output_dir)])

    return subprocess.run(cmd, check=False).returncode


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    # Keep behavior close to the .bat by running from script directory.
    os.chdir(script_dir)

    print()
    print("==============================")
    print(" easyeda2kicad - downloader")
    print("==============================")
    print()

    easyeda_runner = resolve_easyeda_runner(script_dir)
    if easyeda_runner is None:
        input("Press Enter to exit...")
        return 1

    mode = prompt_choice(
        "Where to save? [1]=Default folder  [2]=Project folder : ", {"1", "2"}
    )

    output_dir: Path | None = None
    if mode == "2":
        output_dir = get_output_dir()
        if output_dir is None:
            input("Press Enter to exit...")
            return 1

    while True:
        print()
        lcsc_id = input("Type the LCSC_ID (e.g. C2040) or 'e' to exit: ").strip()

        if lcsc_id.lower() == "e":
            return 0
        if not lcsc_id:
            print("Please type an ID or 'e' to exit.")
            input("Press Enter to continue...")
            continue

        print()
        if output_dir is not None:
            print(f'Saving INSIDE: "{output_dir}"')
        else:
            print("Saving to easyeda2kicad default folder")

        exit_code = run_easyeda2kicad(easyeda_runner, lcsc_id, output_dir)
        if exit_code != 0:
            print()
            print(f"easyeda2kicad failed with exit code {exit_code}.")

        print()
        input("Press Enter to continue...")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        raise SystemExit(130)

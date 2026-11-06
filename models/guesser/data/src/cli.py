"""Command-line entry points for the Guesser data workflow."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path
from pprint import pprint

from . import __version__
from .common import DataError, load_step
from .settings import (
    CONCURRENCY,
    DEFAULT_DATA_ROOT,
    EXAMPLE_DATA_ROOT,
    PACKAGE_ROOT,
    PROBE_DATA_ROOT,
    PROFILES,
    Settings,
)

REMOVED_COMMANDS = {
    "scan": "Use guesser-data download; matching completed classes resume automatically.",
    "freeze": "Use guesser-data export; it checks the data once and writes the summary.",
    "qa": "Use guesser-data preview for optional contact sheets. Approval is no longer required.",
    "validate": "Use guesser-data example for a small offline example, or probe for explicit source samples.",
}


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise DataError(
            message,
            "usage_error",
            hint="Run guesser-data <command> --help for accepted options.",
        )


def parser() -> argparse.ArgumentParser:
    root = Parser(
        prog="guesser-data",
        description="Prepare Quick, Draw! originals and generate timed model images.",
        allow_abbrev=False,
    )
    root.add_argument("--version", "-v", "-V", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True, parser_class=Parser)
    for name in (
        "download",
        "prepare",
        "preview",
        "export",
        "preflight",
        "status",
        "inventory",
        "probe",
        "audit",
        "example",
    ):
        command = commands.add_parser(name, allow_abbrev=False)
        default_root = (
            EXAMPLE_DATA_ROOT
            if name == "example"
            else PROBE_DATA_ROOT
            if name == "probe"
            else DEFAULT_DATA_ROOT
        )
        command.add_argument(
            "--data-root",
            type=Path,
            default=default_root,
            help="Generated-data directory (any drive)",
        )
        command.add_argument(
            "--profile",
            choices=tuple(PROFILES),
            default="smoke" if name in ("probe", "example") else "production",
            help="Dataset size: production, medium or small; smoke is for examples/probes",
        )
        command.add_argument(
            "--json", action="store_true", help="Print the result as JSON"
        )
        if name == "download":
            command.add_argument(
                "--class",
                dest="classes",
                action="append",
                help="Official category name; repeat for several categories (default: all)",
            )
            command.add_argument(
                "--candidates", type=int, help="Candidate reserve per selected category"
            )
            command.add_argument(
                "--concurrency", type=int, choices=(1, 2, 3), default=CONCURRENCY
            )
        if name == "probe":
            command.add_argument("--max-categories", type=int, default=3)
            command.add_argument("--range-mib", type=int, default=1)
            command.add_argument("--limit-records", type=int, default=60)
        if name == "export":
            command.add_argument("--output-dir", type=Path)
    return root


def configure_local_storage() -> None:
    temporary = PACKAGE_ROOT / ".local/tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("UV_CACHE_DIR", str(PACKAGE_ROOT / ".local/cache/uv"))
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    tempfile.tempdir = str(temporary)


def _class_ids(names: list[str] | None) -> list[int] | None:
    if not names:
        return None
    registry = (
        (PACKAGE_ROOT / "src/resources/categories.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    unknown = [name for name in names if name not in registry]
    if unknown:
        raise DataError(
            "Unknown category: " + ", ".join(unknown),
            "invalid_class",
            hint="Use the exact name from the bundled categories.txt.",
        )
    return sorted({registry.index(name) for name in names})


def _counts_result(settings: Settings, result: dict) -> dict:
    result = result.get("summary", result)
    counts = result.get("counts", {})
    return {
        "classes": len(counts),
        "originals": {
            split: sum(values[split] for values in counts.values())
            for split in ("train", "validation", "test")
        },
        "summary": str(settings.base / "dataset-summary.json"),
    }


def dispatch(args: argparse.Namespace) -> dict:
    settings = Settings(args.data_root, args.profile)
    if args.command == "preflight":
        import psutil

        return {
            "python": platform.python_version(),
            "data_root": str(settings.data_root),
            "free_gib": round(
                shutil.disk_usage(settings.data_root.anchor).free / 2**30, 2
            ),
            "available_ram_gib": round(psutil.virtual_memory().available / 2**30, 2),
            "uv_cache": os.environ["UV_CACHE_DIR"],
            "dependencies": {
                name: importlib.metadata.version(name)
                for name in (
                    "numpy",
                    "pillow",
                    "pyarrow",
                    "opencv-python-headless",
                    "psutil",
                )
            },
        }
    if args.command == "status":
        return {
            "profile": settings.profile,
            "path": str(settings.base),
            "inventory": (settings.base / "inventory.json").exists(),
            "candidate_classes": len(
                list((settings.base / "receipts").glob("c*.json"))
            ),
            "prepared": (settings.base / "prepared/manifests/train.parquet").exists(),
            "summary": (settings.base / "dataset-summary.json").exists(),
        }
    if args.command in ("download", "inventory", "probe"):
        download = load_step("01-download")

        if args.command == "inventory":
            result = download.inventory(settings)
            return {
                "classes": len(result["categories"]),
                "path": str(settings.base / "inventory.json"),
            }
        if args.command == "download":
            ids = _class_ids(args.classes)
            print(
                f"Downloading {settings.profile} ({settings.download_method})...",
                file=sys.stderr,
            )
            result = download.download(
                settings,
                class_ids=ids,
                candidates=args.candidates,
                concurrency=args.concurrency,
            )
        else:
            if settings.profile != "smoke":
                raise DataError("probe uses the smoke profile", "invalid_profile")
            if not (settings.base / "inventory.json").exists():
                download.inventory(settings)
            result = download.probe(
                settings, args.max_categories, args.range_mib, args.limit_records
            )
        return {
            "classes": len(result["receipts"]),
            "candidates": sum(row["candidate_count"] for row in result["receipts"]),
            "path": str(settings.base / "candidates"),
        }
    if args.command == "prepare":
        return _counts_result(settings, load_step("02-prepare").prepare(settings))
    if args.command == "audit":
        result = load_step("04-export").audit(settings)
        return {
            "status": result.get("status", "passed"),
            **_counts_result(settings, result),
        }
    if args.command == "export":
        return load_step("04-export").export_dataset(settings, args.output_dir)
    if args.command in ("preview", "example"):
        preview = load_step("03-preview")

        if args.command == "example":
            if settings.profile != "smoke":
                raise DataError("example uses the smoke profile", "invalid_profile")
            result = preview.create_example(settings)
            return {
                "synthetic": True,
                **_counts_result(settings, result),
                "preview": result["preview"],
            }
        return preview.generate_preview(settings)
    raise DataError("Unknown command", "usage_error")


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    json_output = "--json" in arguments
    try:
        if arguments and arguments[0] in REMOVED_COMMANDS:
            raise DataError(
                f"{arguments[0]} was removed.",
                "usage_error",
                hint=REMOVED_COMMANDS[arguments[0]],
            )
        args = parser().parse_args(arguments)
        configure_local_storage()
        settings = Settings(args.data_root, args.profile)
        targets = settings.spec
        if args.command == "download" and args.candidates is not None:
            targets["candidates"] = args.candidates
        result = {
            "profile": settings.profile,
            "targets_per_category": targets,
            **dispatch(args),
        }
    except (DataError, OSError, ValueError, KeyError) as exc:
        message = {
            "code": getattr(exc, "code", "operation_failed"),
            "message": str(exc),
            "hint": getattr(exc, "hint", ""),
        }
        if json_output:
            print(json.dumps({"ok": False, "error": message}, indent=2))
        else:
            print(f"Error: {message['message']}")
            if message["hint"]:
                print(message["hint"])
        return 2 if message["code"] == "usage_error" else 1
    except KeyboardInterrupt:
        print(
            "Interrupted; incomplete categories will restart on the next download.",
            file=sys.stderr,
        )
        return 1
    if json_output:
        print(
            json.dumps(
                {"ok": True, "command": args.command, "result": result},
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(f"{args.command.capitalize()} complete.")
        pprint(result, sort_dicts=False, width=100)
    return 0

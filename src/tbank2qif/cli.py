from __future__ import annotations
import argparse
from pathlib import Path
from .core import convert

DEFAULT_INPUT_FILE = "data/Input/operations.csv"
DEFAULT_CATEGORY_FILE = "data/Input/category.csv"
DEFAULT_OUTPUT_DIR = "data/Output/"
DEFAULT_DATE_CSV="%d.%m.%Y %H:%M:%S"

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tbank2qif",
        description="T-Bank CSV → Quicken QIF/CSV (single file or batch directory).",
        formatter_class=argparse.RawTextHelpFormatter  # Используем RawTextHelpFormatter
    )
    p.add_argument("-i", "--input", type=Path, default=DEFAULT_INPUT_FILE, help="Input CSV file with path like data/Input/operations.csv.")
    p.add_argument("-o", "--output", type=Path, help="Output QIF file (if omitted but --out-dir given, will use import.qif)")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory (writes QIF and quicken.csv)")
    p.add_argument("--categories", type=Path, default= DEFAULT_CATEGORY_FILE, help="Categories CSV (optional, default in data/Input/category.csv)")
    p.add_argument("--date-format", default=DEFAULT_DATE_CSV, help="Date format in input CSV (default: dd.mm.YY HH:MM:SS)")
    p.add_argument("--delimiter", default=";", help="CSV delimiter (default: ;)")
    p.add_argument("--encoding", default="utf-8", help="CSV encoding (default: utf-8)")

    p.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity")
    return p

def _run(args) -> int:
    if not args.input:
        raise SystemExit("Single-file mode requires -i/--input")
    if not (args.output or args.out_dir):
        raise SystemExit("Provide either -o/--output (QIF path) or --out-dir (directory).")

    # If out-dir provided, write as import.qif + quicken.csv
    out_dir = None
    if args.out_dir:
        out_dir = args.out_dir
    else:
        # derive out_dir from output file
        out_dir = args.output.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(f"[tbank2qif] Converting {args.input} -> {out_dir}")

    convert(
        input_csv=args.input,
        categories_csv=args.categories,
        out_dir=out_dir,
        date_format=args.date_format,
        delimiter=args.delimiter,
        encoding=args.encoding,
    )

    # If user requested -o specific QIF file, and core wrote default 'import.qif', move/rename it
    if args.output:
        default_qif = out_dir / "import.qif"
        if default_qif.exists():
            default_qif.replace(args.output)

    if args.verbose:
        print("[tbank2qif] Convertion done.")
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    single = bool(args.input) or bool(args.output) or bool(args.out_dir)

    if not single:
        raise SystemExit("Provide arguments for single-file (-i/-o/--out-dir)")
    else:
        return _run(args)


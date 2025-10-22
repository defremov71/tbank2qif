from __future__ import annotations
import argparse
from pathlib import Path
from .core import convert

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tbank2qif",
        description="Tinkoff Bank CSV → Quicken QIF/CSV (single file or batch directory)."
    )
    # Single-file mode
    p.add_argument("-i", "--input", type=Path, help="Input CSV file")
    p.add_argument("-o", "--output", type=Path, help="Output QIF file (if omitted but --out-dir given, will use import.qif)")
    p.add_argument("--out-dir", type=Path, help="Output directory (writes QIF and quicken.csv)")
    p.add_argument("--categories", type=Path, help="Categories CSV (optional)")
    p.add_argument("--date-format", default="%d.%m.%Y", help="Date format in input CSV (default: %%d.%%m.%%Y)")
    p.add_argument("--delimiter", default=";", help="CSV delimiter (default: ;)")
    p.add_argument("--encoding", default="utf-8", help="CSV encoding (default: utf-8)")

    # Batch mode
    p.add_argument("--input-dir", type=Path, help="Directory with input CSV files")
    p.add_argument("--output-dir", type=Path, help="Directory to write outputs for batch")
    p.add_argument("--combined", action="store_true", help="In batch mode, also write a combined.qif in output-dir")

    p.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity")
    return p

def _run_single(args) -> int:
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
        print("[tbank2qif] Done.")
    return 0

def _run_batch(args) -> int:
    if not args.input_dir or not args.output_dir:
        raise SystemExit("Batch mode requires --input-dir and --output-dir.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    from .core import build_quicken_df
    from .writers import write_qif, write_quicken_csv, write_qif_append

    combined_qif = args.output_dir / "combined.qif" if args.combined else None
    if combined_qif and combined_qif.exists():
        combined_qif.unlink()

    n = 0
    for csv_file in sorted(args.input_dir.glob("*.csv")):
        stem = csv_file.stem
        out_dir = args.output_dir / stem
        out_dir.mkdir(parents=True, exist_ok=True)
        if args.verbose:
            print(f"[tbank2qif] {csv_file.name} -> {out_dir}")

        # Build DF once
        df = build_quicken_df(
            input_csv=csv_file,
            categories_csv=args.categories,
            date_format=args.date_format,
            delimiter=args.delimiter,
            encoding=args.encoding,
        )
        # Write individual outputs
        write_quicken_csv(df, out_dir / "quicken.csv")
        write_qif(df, out_dir / "import.qif")

        # Append to combined, if requested
        if combined_qif:
            write_qif_append(df, combined_qif)

        n += 1

    if args.verbose:
        print(f"[tbank2qif] Converted {n} file(s).")
        if combined_qif:
            print(f"[tbank2qif] Combined QIF: {combined_qif}")
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    single = bool(args.input) or bool(args.output) or bool(args.out_dir)
    batch = bool(args.input_dir) or bool(args.output_dir)
    if single and batch:
        raise SystemExit("Choose either single-file or batch mode, not both.")
    if not single and not batch:
        raise SystemExit("Provide arguments for single-file (-i/-o/--out-dir) or batch (--input-dir/--output-dir) mode.")

    if single:
        return _run_single(args)
    else:
        return _run_batch(args)

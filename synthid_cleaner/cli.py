"""
Command Line Interface for SynthID Cleaner.
"""

import argparse
import sys
from pathlib import Path
from . import __version__
from .core import sanitize_image, batch_sanitize
from .gui import run_gui, is_gui_available


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="synthid-cleaner",
        description="Strip C2PA/EXIF metadata and disrupt imperceptible SynthID watermarks on AI-generated images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive file dialog (GUI)
  synthid-cleaner
  synthid-cleaner --gui

  # Clean a single image
  synthid-cleaner -i photo.jpg
  synthid-cleaner -i photo.jpg -o cleaned.png --noise 1.4

  # Batch clean an entire directory
  synthid-cleaner --batch ./input_folder --output-dir ./cleaned_folder
  synthid-cleaner -b ./inputs -r  # Recursive scan
        """,
    )

    parser.add_argument(
        "-i", "--input",
        type=str,
        help="Path to an input image or folder (when used with --batch).",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Path to output image file or output directory.",
    )
    parser.add_argument(
        "-n", "--noise",
        type=float,
        default=1.2,
        help="Noise level std-dev for SynthID perturbation (default: 1.2, recommended: 0.8 - 1.8).",
    )
    parser.add_argument(
        "-b", "--batch",
        action="store_true",
        help="Batch process an entire directory.",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively scan subdirectories in batch mode.",
    )
    parser.add_argument(
        "-g", "--gui",
        action="store_true",
        help="Force open the interactive graphical file picker.",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def main() -> None:
    parser = create_parser()

    # If no arguments passed, prefer GUI if display is available, else print help
    if len(sys.argv) == 1:
        if is_gui_available():
            run_gui()
            return
        else:
            parser.print_help()
            sys.exit(0)

    args = parser.parse_args()

    if args.gui:
        run_gui(noise_level=args.noise, output_dir=args.output)
        return

    if not args.input:
        parser.error("The -i/--input argument is required when not in --gui mode.")

    input_path = Path(args.input)

    if not input_path.exists():
        sys.exit(f"[-] Error: Input path does not exist: {input_path}")

    # Batch directory mode
    if args.batch or input_path.is_dir():
        if not input_path.is_dir():
            sys.exit(f"[-] Error: Batch mode specified, but {input_path} is not a directory.")

        out_dir = Path(args.output) if args.output else input_path
        print(f"[*] Batch processing directory: {input_path}")
        print(f"[*] Target output directory: {out_dir}")
        print(f"[*] Noise variance level: {args.noise}")

        def log_progress(current: int, total: int, in_f: Path, out_f: Path):
            print(f"[{current}/{total}] Cleaned: {in_f.name} -> {out_f.name}")

        results = batch_sanitize(
            input_dir=input_path,
            output_dir=out_dir,
            noise_level=args.noise,
            recursive=args.recursive,
            progress_callback=log_progress,
        )
        print(f"[+] Done! Processed {len(results)} images.")
        return

    # Single file mode
    try:
        out_path = Path(args.output) if args.output else None
        print(f"[*] Sanitizing: {input_path}")
        saved = sanitize_image(
            input_path=input_path,
            output_path=out_path,
            noise_level=args.noise,
        )
        print(f"[+] Success! Cleaned image saved to: {saved}")
    except Exception as e:
        sys.exit(f"[-] Error: {e}")


if __name__ == "__main__":
    main()

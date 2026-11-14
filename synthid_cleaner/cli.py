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

  # Clean a single image (positional or -i)
  synthid-cleaner photo.jpg
  synthid-cleaner -i photo.jpg -o cleaned.jpg

  # Batch clean a folder
  synthid-cleaner ./images --output-dir ./cleaned_folder
  synthid-cleaner --batch ./images --output-dir ./cleaned_folder --recursive
  synthid-cleaner -i ./images -o ./cleaned_folder -r -f webp -q 90
        """,
    )

    # Optional positional argument for direct path input: synthid-cleaner ./images or synthid-cleaner photo.jpg
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Input image file or directory (optional positional argument).",
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        default=None,
        help="Path to an input image or folder.",
    )
    parser.add_argument(
        "-o", "--output", "--output-dir", "-d",
        dest="output",
        type=str,
        default=None,
        help="Path to output image file or output directory.",
    )
    parser.add_argument(
        "-b", "--batch",
        nargs="?",
        const=True,
        default=None,
        help="Batch process an entire directory (can specify directory: --batch ./images or as flag: -b).",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively scan subdirectories in batch mode.",
    )
    parser.add_argument(
        "-f", "--format", "--f",
        dest="format",
        type=str,
        default="auto",
        choices=["auto", "png", "jpg", "jpeg", "webp"],
        help="Output image format ('auto', 'png', 'jpg', 'webp'). Default: 'auto' (preserves input format to prevent file size increase).",
    )
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=95,
        help="Compression quality (1-100) for lossy formats like JPEG/WebP (default: 95).",
    )
    parser.add_argument(
        "-n", "--noise",
        type=float,
        default=1.2,
        help="Noise level std-dev for SynthID perturbation (default: 1.2, recommended: 0.8 - 1.8).",
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

    # If no arguments passed at all, prefer GUI if display is available, else print help
    if len(sys.argv) == 1:
        if is_gui_available():
            run_gui()
            return
        else:
            parser.print_help()
            sys.exit(0)

    args = parser.parse_args()

    if args.gui:
        run_gui(
            noise_level=args.noise,
            output_dir=args.output,
            output_format=args.format,
            quality=args.quality,
        )
        return

    # Resolve input target from positional arg, -i/--input, or --batch argument
    raw_input = args.input
    if not raw_input:
        if isinstance(args.batch, str):
            raw_input = args.batch
        elif args.path:
            raw_input = args.path

    if not raw_input:
        parser.error("Please specify an input image or directory (e.g. synthid-cleaner ./images or -i photo.jpg)")

    input_path = Path(raw_input)

    if not input_path.exists():
        sys.exit(f"[-] Error: Input path does not exist: {input_path}")

    # Determine if batch mode should be triggered
    is_batch = bool(args.batch) or input_path.is_dir()

    # Batch directory mode
    if is_batch:
        if not input_path.is_dir():
            sys.exit(f"[-] Error: Batch mode requested, but '{input_path}' is not a directory.")

        out_dir = Path(args.output) if args.output else input_path
        print(f"[*] Batch processing directory: {input_path}")
        print(f"[*] Target output directory: {out_dir}")
        print(f"[*] Format: {args.format} | Quality: {args.quality} | Noise level: {args.noise}")

        def log_progress(current: int, total: int, in_f: Path, out_f: Path):
            print(f"[{current}/{total}] Cleaned: {in_f.name} -> {out_f.name}")

        results = batch_sanitize(
            input_dir=input_path,
            output_dir=out_dir,
            noise_level=args.noise,
            output_format=args.format,
            quality=args.quality,
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
            output_format=args.format,
            quality=args.quality,
        )
        print(f"[+] Success! Cleaned image saved to: {saved}")
    except Exception as e:
        sys.exit(f"[-] Error: {e}")


if __name__ == "__main__":
    main()

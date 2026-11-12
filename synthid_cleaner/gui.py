"""
Graphical User Interface (Tkinter file picker) for SynthID Cleaner.
"""

import os
import sys
from pathlib import Path
from typing import Optional


def is_gui_available() -> bool:
    """
    Check if a GUI / display environment is available.
    """
    if sys.platform.startswith("win"):
        return True
    if sys.platform == "darwin":
        return True
    # Linux / Unix
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def run_gui(
    noise_level: float = 1.2,
    output_dir: Optional[str] = None,
    output_format: str = "auto",
    quality: int = 95,
) -> Optional[Path]:
    """
    Launches an interactive native file picker to select and sanitize an image.
    """
    try:
        from tkinter import Tk, filedialog
    except ImportError:
        print("[-] Tkinter is not installed on this system. Please use CLI mode (--help).")
        return None

    if not is_gui_available():
        print("[-] No display server detected (HEADLESS). Please specify an image file via CLI:")
        print("    synthid-cleaner --input path/to/image.jpg")
        return None

    try:
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
    except Exception as e:
        print(f"[-] Could not initialize GUI: {e}")
        return None

    print("[*] Please select your AI-generated image from the file window...")
    file_types = [
        ("Image Files", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff"),
        ("All Files", "*.*"),
    ]
    input_path = filedialog.askopenfilename(
        title="Select AI-Generated Image to Clean",
        filetypes=file_types,
    )

    if not input_path:
        print("[-] Cancelled: No file selected.")
        return None

    from .core import sanitize_image, generate_clean_output_path

    out_path = generate_clean_output_path(input_path, output_dir, output_format=output_format)
    print(f"[+] Processing target: {input_path}")
    saved = sanitize_image(
        input_path=input_path,
        output_path=out_path,
        noise_level=noise_level,
        output_format=output_format,
        quality=quality,
    )
    print(f"[+] Success! Cleaned file saved to: {saved}")
    return saved

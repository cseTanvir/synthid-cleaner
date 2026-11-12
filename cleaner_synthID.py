#!/usr/bin/env python3
"""
SynthID Cleaner - Standalone Legacy Script

This script is maintained for direct single-file usage and backward compatibility.
For advanced CLI options (batch directory processing, recursion, custom output directories),
use `synthid-cleaner` or `python main.py --help`.
"""

import os
import sys
from pathlib import Path
from tkinter import Tk, filedialog
import numpy as np
from PIL import Image


def sanitize_image_high_quality(input_path, output_path, noise_level=1.2):
    """
    Locally removes C2PA data and breaks hidden SynthID patterns.
    """
    # 1. Open image and drop C2PA/EXIF data by extracting only the raw pixel canvas
    with Image.open(input_path) as img:
        # Check for transparency
        has_alpha = img.mode in ("RGBA", "LA") or ("transparency" in img.info)

        if has_alpha:
            img = img.convert("RGBA")
            rgba_data = np.array(img, dtype=np.float32)
            rgb_channels = rgba_data[:, :, :3]
            alpha_channel = rgba_data[:, :, 3:]

            # 2. Add mathematical variance to break SynthID alignments
            noise = np.random.normal(0, noise_level, rgb_channels.shape)
            disrupted_rgb = np.clip(rgb_channels + noise, 0, 255)
            disrupted_rgba = np.concatenate([disrupted_rgb, alpha_channel], axis=-1).astype(np.uint8)
            clean_img = Image.fromarray(disrupted_rgba, "RGBA")
        else:
            img = img.convert("RGB")
            data = np.array(img, dtype=np.float32)

            # 2. Add mathematical variance to break SynthID alignments
            noise = np.random.normal(0, noise_level, data.shape)
            disrupted_data = np.clip(data + noise, 0, 255).astype(np.uint8)
            clean_img = Image.fromarray(disrupted_data, "RGB")

        # 3. Save as a lossless PNG to preserve 100% sharp details
        clean_img.save(output_path, "PNG", optimize=True)
        print(f"[+] Success! Cleaned file saved to: {output_path}")


def select_and_process_file():
    """
    Open native file dialog to choose and clean an image.
    """
    root = Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass

    print("[*] Please select your AI-generated image from the file window...")

    file_types = [("Image Files", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff"), ("All Files", "*.*")]
    input_path = filedialog.askopenfilename(title="Select AI-Generated Image to Clean", filetypes=file_types)

    if not input_path:
        print("[-] Cancelled: No file selected.")
        return

    dir_name, file_name = os.path.split(input_path)
    base_name, _ = os.path.splitext(file_name)
    output_path = os.path.join(dir_name, f"{base_name}_clean.png")

    print(f"[+] Processing target: {input_path}")
    sanitize_image_high_quality(input_path, output_path)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If CLI arguments were provided, delegate to the package CLI
        from synthid_cleaner.cli import main
        main()
    else:
        select_and_process_file()

"""
Core sanitization functions for SynthID Cleaner.
"""

import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def generate_clean_output_path(input_path: Union[str, Path], output_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Generate a default output filename with '_clean.png' suffix.
    """
    in_path = Path(input_path)
    out_dir = Path(output_dir) if output_dir else in_path.parent
    base_name = in_path.stem
    return out_dir / f"{base_name}_clean.png"


def sanitize_image(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    noise_level: float = 1.2,
    seed: Optional[int] = None,
) -> Path:
    """
    Sanitizes an image by:
    1. Dropping C2PA, EXIF, and all metadata by extracting the raw pixel buffer.
    2. Injecting imperceptible Gaussian micro-perturbations to disrupt hidden SynthID patterns.
    3. Exporting to a clean, lossless PNG format.

    Args:
        input_path: Path to the target image file.
        output_path: Path to save the cleaned image (default: <name>_clean.png).
        noise_level: Standard deviation of Gaussian perturbation (default: 1.2).
                     Values between 0.8 and 1.5 disrupt watermarks with zero human-visible degradation.
        seed: Optional random seed for reproducible sanitization.

    Returns:
        Path to the saved sanitized image.
    """
    in_path = Path(input_path)
    if not in_path.is_file():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    if output_path is None:
        out_path = generate_clean_output_path(in_path)
    else:
        out_path = Path(output_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if seed is not None:
        np.random.seed(seed)

    # 1. Open image and inspect format/mode
    with Image.open(in_path) as img:
        # Preserve alpha transparency if present
        has_alpha = img.mode in ("RGBA", "LA") or ("transparency" in img.info)

        if has_alpha:
            img = img.convert("RGBA")
            rgba_data = np.array(img, dtype=np.float32)
            rgb_channels = rgba_data[:, :, :3]
            alpha_channel = rgba_data[:, :, 3:]

            # 2. Add mathematical variance to color channels to break SynthID alignments
            noise = np.random.normal(0, noise_level, rgb_channels.shape)
            disrupted_rgb = np.clip(rgb_channels + noise, 0, 255)

            # Recombine with intact alpha channel
            disrupted_rgba = np.concatenate([disrupted_rgb, alpha_channel], axis=-1).astype(np.uint8)
            clean_img = Image.fromarray(disrupted_rgba, "RGBA")
        else:
            # Standard color conversion
            img = img.convert("RGB")
            data = np.array(img, dtype=np.float32)

            # 2. Add mathematical variance to break SynthID alignments
            noise = np.random.normal(0, noise_level, data.shape)
            disrupted_data = np.clip(data + noise, 0, 255).astype(np.uint8)
            clean_img = Image.fromarray(disrupted_data, "RGB")

        # 3. Save as clean lossless PNG without any original EXIF/C2PA metadata
        clean_img.save(str(out_path), "PNG", optimize=True)

    return out_path


def batch_sanitize(
    input_dir: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    noise_level: float = 1.2,
    recursive: bool = False,
    progress_callback: Optional[Callable[[int, int, Path, Path], None]] = None,
) -> List[Tuple[Path, Path]]:
    """
    Process all supported images in a directory.

    Args:
        input_dir: Directory containing images.
        output_dir: Directory to save cleaned images (default: input_dir).
        noise_level: Standard deviation for Gaussian perturbation (default: 1.2).
        recursive: Whether to scan subdirectories recursively.
        progress_callback: Callback function(current_idx, total_count, in_file, out_file).

    Returns:
        List of (input_path, output_path) tuples for successfully processed images.
    """
    in_dir = Path(input_dir)
    if not in_dir.is_dir():
        raise NotADirectoryError(f"Input directory not found: {in_dir}")

    out_dir = Path(output_dir) if output_dir else in_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    pattern = "**/*" if recursive else "*"
    files = [
        f for f in in_dir.glob(pattern)
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS and not f.name.endswith("_clean.png")
    ]

    results: List[Tuple[Path, Path]] = []
    total = len(files)

    for idx, file_path in enumerate(files, start=1):
        rel_path = file_path.relative_to(in_dir)
        target_out = (out_dir / rel_path).with_name(f"{file_path.stem}_clean.png")
        target_out.parent.mkdir(parents=True, exist_ok=True)

        try:
            saved_path = sanitize_image(
                input_path=file_path,
                output_path=target_out,
                noise_level=noise_level,
            )
            results.append((file_path, saved_path))
            if progress_callback:
                progress_callback(idx, total, file_path, saved_path)
        except Exception as e:
            print(f"[-] Error processing {file_path}: {e}")

    return results

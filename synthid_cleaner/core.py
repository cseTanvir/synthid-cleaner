"""
Core sanitization functions for SynthID Cleaner.
"""

import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def generate_clean_output_path(
    input_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    output_format: str = "auto",
) -> Path:
    """
    Generate a default output filename with '_clean.<ext>' suffix.

    Args:
        input_path: Original input image path.
        output_dir: Optional target directory.
        output_format: Output format ('auto', 'png', 'jpg', 'jpeg', 'webp').
    """
    in_path = Path(input_path)
    out_dir = Path(output_dir) if output_dir else in_path.parent
    base_name = in_path.stem

    fmt = output_format.lower().strip()
    if fmt in ("auto", ""):
        ext = in_path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            ext = ".png"
    elif fmt in ("jpg", "jpeg"):
        ext = ".jpg"
    elif fmt == "png":
        ext = ".png"
    elif fmt == "webp":
        ext = ".webp"
    else:
        ext = f".{fmt.lstrip('.')}"

    return out_dir / f"{base_name}_clean{ext}"


def sanitize_image(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    noise_level: float = 1.2,
    output_format: str = "auto",
    quality: int = 95,
    seed: Optional[int] = None,
) -> Path:
    """
    Sanitizes an image by:
    1. Dropping C2PA, EXIF, and all metadata by extracting the raw pixel buffer.
    2. Injecting imperceptible Gaussian micro-perturbations to disrupt hidden SynthID patterns.
    3. Exporting to the desired format (preserving original format by default to avoid size inflation).

    Args:
        input_path: Path to the target image file.
        output_path: Path to save the cleaned image (default: <name>_clean.<ext>).
        noise_level: Standard deviation of Gaussian perturbation (default: 1.2).
                     Values between 0.8 and 1.5 disrupt watermarks with zero human-visible degradation.
        output_format: Output image format ('auto', 'png', 'jpg', 'webp'). Default 'auto' matches input format.
        quality: Compression quality (1-100) for lossy formats like JPEG/WebP (default: 95).
        seed: Optional random seed for reproducible sanitization.

    Returns:
        Path to the saved sanitized image.
    """
    in_path = Path(input_path)
    if not in_path.is_file():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    if output_path is None:
        out_path = generate_clean_output_path(in_path, output_format=output_format)
    else:
        out_path = Path(output_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine target PIL format
    target_ext = out_path.suffix.lower()
    fmt_choice = output_format.lower().strip()

    if fmt_choice != "auto":
        if fmt_choice in ("jpg", "jpeg"):
            pil_format = "JPEG"
        elif fmt_choice == "png":
            pil_format = "PNG"
        elif fmt_choice == "webp":
            pil_format = "WEBP"
        else:
            pil_format = fmt_choice.upper()
    else:
        if target_ext in (".jpg", ".jpeg"):
            pil_format = "JPEG"
        elif target_ext == ".webp":
            pil_format = "WEBP"
        elif target_ext == ".png":
            pil_format = "PNG"
        else:
            pil_format = "PNG"

    if seed is not None:
        np.random.seed(seed)

    # 1. Open image and inspect format/mode
    with Image.open(in_path) as img:
        has_alpha = img.mode in ("RGBA", "LA") or ("transparency" in img.info)

        # For formats that don't support alpha (like JPEG), convert directly to RGB
        if has_alpha and pil_format != "JPEG":
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
            img = img.convert("RGB")
            data = np.array(img, dtype=np.float32)

            # 2. Add mathematical variance to break SynthID alignments
            noise = np.random.normal(0, noise_level, data.shape)
            disrupted_data = np.clip(data + noise, 0, 255).astype(np.uint8)
            clean_img = Image.fromarray(disrupted_data, "RGB")

        # 3. Save as clean file without any original EXIF/C2PA metadata
        if pil_format == "JPEG":
            clean_img.save(str(out_path), "JPEG", quality=quality, optimize=True)
        elif pil_format == "WEBP":
            clean_img.save(str(out_path), "WEBP", quality=quality)
        elif pil_format == "PNG":
            clean_img.save(str(out_path), "PNG", optimize=True)
        else:
            clean_img.save(str(out_path), pil_format)

    return out_path


def batch_sanitize(
    input_dir: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    noise_level: float = 1.2,
    output_format: str = "auto",
    quality: int = 95,
    recursive: bool = False,
    progress_callback: Optional[Callable[[int, int, Path, Path], None]] = None,
) -> List[Tuple[Path, Path]]:
    """
    Process all supported images in a directory.

    Args:
        input_dir: Directory containing images.
        output_dir: Directory to save cleaned images (default: input_dir).
        noise_level: Standard deviation for Gaussian perturbation (default: 1.2).
        output_format: Output format ('auto', 'png', 'jpg', 'webp').
        quality: Quality (1-100) for JPEG/WebP.
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
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS and "_clean" not in f.stem
    ]

    results: List[Tuple[Path, Path]] = []
    total = len(files)

    for idx, file_path in enumerate(files, start=1):
        rel_path = file_path.relative_to(in_dir)
        temp_out = generate_clean_output_path(file_path, output_format=output_format)
        target_out = (out_dir / rel_path).with_name(temp_out.name)
        target_out.parent.mkdir(parents=True, exist_ok=True)

        try:
            saved_path = sanitize_image(
                input_path=file_path,
                output_path=target_out,
                noise_level=noise_level,
                output_format=output_format,
                quality=quality,
            )
            results.append((file_path, saved_path))
            if progress_callback:
                progress_callback(idx, total, file_path, saved_path)
        except Exception as e:
            print(f"[-] Error processing {file_path}: {e}")

    return results

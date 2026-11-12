import shutil
import tempfile
from pathlib import Path
import numpy as np
import pytest
from PIL import Image

from synthid_cleaner.core import sanitize_image, batch_sanitize, generate_clean_output_path


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


def create_sample_rgb_image(path: Path, width=64, height=64):
    arr = np.random.randint(50, 200, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    # Add dummy info/metadata
    img.info["comment"] = "SynthID Test Metadata"
    img.save(path, format="PNG")
    return arr


def create_sample_rgba_image(path: Path, width=64, height=64):
    arr = np.random.randint(50, 200, (height, width, 4), dtype=np.uint8)
    arr[:, :, 3] = 128  # Fixed semi-transparency
    img = Image.fromarray(arr, mode="RGBA")
    img.save(path, format="PNG")
    return arr


def test_sanitize_rgb_image(temp_dir):
    input_file = temp_dir / "sample.png"
    orig_pixels = create_sample_rgb_image(input_file)

    output_file = temp_dir / "sample_clean.png"
    result_path = sanitize_image(input_file, output_file, noise_level=1.5, seed=42)

    assert result_path.exists()
    assert result_path == output_file

    with Image.open(result_path) as cleaned:
        assert cleaned.size == (64, 64)
        assert cleaned.mode == "RGB"
        assert "comment" not in cleaned.info

        cleaned_arr = np.array(cleaned)
        # Check that pixels are within valid range
        assert cleaned_arr.min() >= 0
        assert cleaned_arr.max() <= 255

        # Check that disruption occurred (pixels not identical to original)
        diff = np.abs(cleaned_arr.astype(float) - orig_pixels.astype(float))
        assert np.any(diff > 0)
        # But average disruption is small (close to noise_level)
        assert np.mean(diff) < 3.0


def test_sanitize_rgba_image(temp_dir):
    input_file = temp_dir / "transparent.png"
    orig_rgba = create_sample_rgba_image(input_file)

    output_file = temp_dir / "transparent_clean.png"
    result_path = sanitize_image(input_file, output_file, noise_level=1.2, seed=123)

    assert result_path.exists()
    with Image.open(result_path) as cleaned:
        assert cleaned.mode == "RGBA"
        cleaned_arr = np.array(cleaned)
        # Alpha channel should be preserved exactly
        np.testing.assert_array_equal(cleaned_arr[:, :, 3], orig_rgba[:, :, 3])


def test_generate_clean_output_path(temp_dir):
    img_path = temp_dir / "art.jpg"
    expected = temp_dir / "art_clean.png"
    assert generate_clean_output_path(img_path) == expected

    custom_dir = temp_dir / "outputs"
    expected_custom = custom_dir / "art_clean.png"
    assert generate_clean_output_path(img_path, output_dir=custom_dir) == expected_custom


def test_batch_sanitize(temp_dir):
    # Create 3 images
    img1 = temp_dir / "img1.png"
    img2 = temp_dir / "img2.jpg"
    img3 = temp_dir / "img3.webp"

    create_sample_rgb_image(img1)
    create_sample_rgb_image(img2)
    create_sample_rgb_image(img3)

    out_dir = temp_dir / "cleaned"
    results = batch_sanitize(input_dir=temp_dir, output_dir=out_dir, noise_level=1.0)

    assert len(results) == 3
    for in_p, out_p in results:
        assert out_p.exists()
        assert out_p.name.endswith("_clean.png")


def test_missing_file_raises_error(temp_dir):
    non_existent = temp_dir / "does_not_exist.png"
    with pytest.raises(FileNotFoundError):
        sanitize_image(non_existent)

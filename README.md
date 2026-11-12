# synthid-cleaner

A lightweight, local tool to sanitize AI-generated images by purging C2PA metadata manifests and disrupting hidden SynthID frequency patterns while keeping visual quality pristine.

---

## Key Features

- **Metadata Purge**: Drops all C2PA, EXIF, XMP, and IPTC headers by extracting raw pixel arrays.
- **Watermark Disruption**: Applies calibrated micro-variance (Gaussian perturbation) to break latent SynthID alignments without human-perceptible degradation.
- **Format & Size Preservation**: Automatically preserves the input format (`--format auto`) and applies smart compression quality (`--quality 95`) so your cleaned JPEGs/WebPs do not explode in file size.
- **Dual Interface**: Supports both an interactive graphical file picker (Tkinter GUI) and an automated CLI.
- **Batch Processing**: Clean entire folders and subdirectories with a single command.
- **Transparency Preservation**: Handles RGBA images while leaving alpha transparency intact.
- **100% Offline & Private**: Runs entirely on your local machine with zero network calls.

---

## Requirements

- Python 3.8 or higher
- Dependencies:
  - `numpy >= 1.22.0`
  - `Pillow >= 9.0.0`

---

## Installation & Building

### 1. Install CLI Command (Recommended)

To register the `synthid-cleaner` command directly in your terminal/PATH:

#### In a virtual environment / current Python:
```bash
git clone https://github.com/cseTanvir/synthid-cleaner.git
cd synthid-cleaner
pip install -e .
```
Now `synthid-cleaner` is available anywhere in your active environment:
```bash
synthid-cleaner --gui
```

#### Globally with `pipx` or `uv tool`:
```bash
# Isolated global CLI installation
pipx install .

# Or using uv:
uv tool install .
```

---

### 2. Building Packages & Binaries

#### Build Distribution Packages (Wheel & sdist)
Generate `.whl` and `.tar.gz` packages in `dist/`:
```bash
# Using uv (fastest)
uv build

# Or standard build tool
pip install build
python -m build
```

#### Build Standalone Executable (Zero Python dependency)
To package everything into a single standalone binary executable (`dist/synthid-cleaner`):
```bash
# Install pyinstaller and build
pip install pyinstaller
pyinstaller synthid-cleaner.spec
```
The resulting executable in `dist/synthid-cleaner` runs independently without needing Python or external libraries:
```bash
./dist/synthid-cleaner --gui
```

---

## Usage

### 1. Graphical Interface (GUI)
Run without flags to open the native image picker dialog:
```bash
python main.py
```
Or via the CLI tool:
```bash
synthid-cleaner --gui
```

### 2. Command Line (CLI)

#### Clean a single image:
```bash
synthid-cleaner -i /path/to/image.jpg
```
The sanitized file is automatically saved as `image_clean.jpg` (preserving format and compact file size).

#### Output as high-quality WebP or JPEG:
```bash
# Convert to WebP for minimal file size
synthid-cleaner -i photo.png -f webp -q 95

# Export as high-quality JPEG
synthid-cleaner -i photo.jpg -f jpg -q 92
```

#### Force lossless PNG output:
```bash
synthid-cleaner -i photo.jpg -f png
```

#### Specify custom output path and noise level:
```bash
synthid-cleaner -i /path/to/image.jpg -o /path/to/output.jpg --noise 1.5
```

#### Batch process a folder (preserves each image's native format):
```bash
synthid-cleaner --batch ./input_folder --output-dir ./cleaned_folder
```

#### Recursive folder scan:
```bash
synthid-cleaner --batch ./input_folder --output-dir ./cleaned_folder --recursive --format auto
```

### 3. Python API
Use directly in your Python code or automation pipelines:

```python
from synthid_cleaner import sanitize_image, batch_sanitize

# Clean a single image (auto-preserves input format and optimizes size)
clean_path = sanitize_image("ai_art.jpg", noise_level=1.2, output_format="auto", quality=95)
print(f"Sanitized file: {clean_path}")

# Export explicitly to WebP or lossless PNG
webp_path = sanitize_image("ai_art.jpg", output_format="webp", quality=90)
png_path = sanitize_image("ai_art.jpg", output_format="png")

# Batch clean a directory
results = batch_sanitize(input_dir="./gallery", output_dir="./cleaned_gallery", output_format="auto")
print(f"Cleaned {len(results)} images.")
```

---

## How It Works

1. **Pixel Buffer Isolation**: Loads the image strictly into a raw numerical array (`numpy.float32`), discarding all metadata containers, EXIF headers, and C2PA signatures.
2. **Harmonic Disruption**: Latent watermarks such as SynthID rely on subtle spatial and frequency-domain correlations. Injecting calibrated Gaussian noise ($\mu=0, \sigma=1.2$) disrupts these imperceptible patterns while staying within less than 0.5% variance of pixel intensity.
3. **Lossless Encoding**: Re-encodes the sanitized pixel array into lossless PNG format with optimization enabled.

---

## Use Cases

- **Privacy & Metadata Scrubbing**: Remove unwanted device signatures, tracking identifiers, and provenance tags prior to publishing.
- **Dataset Preprocessing**: Prepare neutral visual datasets for computer vision models without embedded generator fingerprints.
- **Creative Pipelines**: Integrate into automated image generation workflows to normalize output files.

---

## Running Tests

Run unit tests with `pytest`:
```bash
pytest -v
```

---

## License

This project is licensed under the [MIT License](LICENSE).

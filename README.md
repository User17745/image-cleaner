# Image Cleaner

Local, project-agnostic product image modernization pipeline.

The pipeline reads images recursively from `source_images`, mirrors the same folder structure into `output_images`, and supports background removal, upscaling, optimization, WebP export, idempotent reruns, dry runs, sample runs, and per-file reporting.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy the example config if you want to customize defaults:

```bash
cp config.example.json config.json
```

## AI Setup

The full AI pipeline uses two pieces:

- `rembg` for background removal
- `realesrgan-ncnn-vulkan` for Real-ESRGAN upscaling

Install Python dependencies:

```bash
./venv/bin/pip install -r requirements.txt
```

The first background-removal run downloads the `u2net.onnx` model into the user's cache directory. On macOS this is usually:

```text
~/.u2net/u2net.onnx
```

For Real-ESRGAN, either put `realesrgan-ncnn-vulkan` on your `PATH`, or place the official ncnn Vulkan package under `tools/` so the project contains:

```text
tools/
├── realesrgan-ncnn-vulkan
└── models/
    ├── realesrgan-x4plus.bin
    └── realesrgan-x4plus.param
```

The `tools/` directory is ignored by git because the binary and models are machine-local dependencies.

Recommended macOS sidecar setup:

```bash
mkdir -p tools
curl -L https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-macos.zip \
  -o tools/realesrgan-ncnn-vulkan-20220424-macos.zip
unzip -o tools/realesrgan-ncnn-vulkan-20220424-macos.zip -d tools
chmod +x tools/realesrgan-ncnn-vulkan
```

Validate setup before processing:

```bash
./venv/bin/python process_images.py --preflight-only --sample-limit 1
```

## Usage

Preview what would be processed:

```bash
python process_images.py --dry-run
```

Process a small QA sample:

```bash
python process_images.py --sample-limit 10
```

Run the full pipeline:

```bash
python process_images.py
```

Run the full AI pipeline on a tiny sample first:

```bash
./venv/bin/python process_images.py --sample-limit 1 --force --parallel-workers 1
```

Then run a larger QA sample:

```bash
./venv/bin/python process_images.py --sample-limit 10 --force --parallel-workers 1
```

Use custom folders:

```bash
python process_images.py --input path/to/source_images --output path/to/output_images
```

Force a full reprocess:

```bash
python process_images.py --force
```

Disable stages:

```bash
python process_images.py --no-upscale
python process_images.py --no-remove-background
python process_images.py --no-optimize
```

Run only WebP conversion/optimization without AI:

```bash
./venv/bin/python process_images.py --no-remove-background --no-upscale --force --parallel-workers 4
```

## Notes

- `rembg` is required when background removal is enabled.
- Real-ESRGAN is invoked through an external executable. The script first checks `tools/realesrgan-ncnn-vulkan`, then `realesrgan-ncnn-vulkan` on `PATH`.
- The default Real-ESRGAN model is `realesrgan-x4plus`.
- If upscaling is enabled and the Real-ESRGAN executable or model files are unavailable, preflight fails before processing starts.
- Processing reports are written to `processing_report.csv` by default.
- Full AI processing is much slower than conversion-only processing. On the initial macOS test, one 500x400 image took about 65 seconds, including first-time model setup.

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

## Notes

- `rembg` is required when background removal is enabled.
- Real-ESRGAN is invoked through an external executable, defaulting to `realesrgan-ncnn-vulkan`.
- If upscaling is enabled and the Real-ESRGAN executable is unavailable, the file is marked as failed unless `--no-upscale` is used.
- Processing reports are written to `processing_report.csv` by default.

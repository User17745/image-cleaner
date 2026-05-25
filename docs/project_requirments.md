# Product Image Modernization Pipeline — Developer Project Plan

## Objective

Build an automated bulk-processing pipeline for product catalog images to:

1. Remove outdated static background graphics
2. Improve image quality using AI upscaling
3. Standardize image dimensions/output
4. Export optimized web-ready images
5. Process images recursively from a project-agnostic source directory:

   * `source_images`

Target:

* ~455 product images
* Minimal recurring cost
* Fully local/offline-capable pipeline
* OS-agnostic implementation with macOS, Linux, and Windows compatibility

---

# Expected Folder Structure

```text
project-root/
│
├── source_images/
│   ├── category-a/
│   │    ├── image1.jpg
│   │    ├── image2.png
│   │    └── ...
│   │
│   └── category-b/
│        ├── image3.jpg
│        ├── image4.png
│        └── ...
│
├── output_images/
│   ├── category-a/
│   └── category-b/
│
├── scripts/
│
├── temp/
│
├── requirements.txt
│
└── README.md
```

---

# Functional Requirements

| Requirement               | Description                           |
| ------------------------- | ------------------------------------- |
| Recursive processing      | Process all images inside subfolders  |
| Background removal        | Remove old graphical backgrounds      |
| AI enhancement            | Improve sharpness/resolution          |
| Batch processing          | Fully automated                       |
| Format conversion         | Export WebP                           |
| Preserve folder structure | Mirror `source_images` hierarchy      |
| Logging                   | Generate processing logs              |
| Failure handling          | Skip failed images and continue       |
| Idempotent runs           | Safe re-runs                          |
| Dry-run mode              | Preview planned processing without writing outputs |
| Stage toggles             | Enable/disable background removal, upscaling, and optimization |
| QA sample mode            | Process a small configurable sample before full batch |
| Processing manifest       | Generate structured per-file processing report |
| Output format selection   | Support WebP by default with optional PNG/JPEG/AVIF |
| Hardware fallback         | Detect GPU/CPU capabilities and fall back predictably |

---

# Recommended Tech Stack

| Component           | Tool                 |
| ------------------- | -------------------- |
| Language            | Python 3.11+         |
| Background removal  | rembg                |
| AI upscaling        | Real-ESRGAN          |
| Image conversion    | Pillow / ImageMagick |
| CLI support         | argparse             |
| Logging             | Python logging       |
| Parallel processing | concurrent.futures   |
| Packaging           | venv                 |

---

# OS-Agnostic Setup Requirements

## Install Dependencies

Install Python 3.11+ and ImageMagick using the package manager appropriate for the operating system.

### macOS

Install:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

```bash
brew install python imagemagick
```

### Linux

Use the distribution package manager.

Example:

```bash
sudo apt-get update
sudo apt-get install python3 python3-venv imagemagick
```

### Windows

Install:

* Python 3.11+ from the official Python installer
* ImageMagick from the official ImageMagick installer

Ensure both are available from the terminal/PATH.

---

# Python Environment Setup

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

---

# Python Packages

## requirements.txt

```text
rembg
pillow
onnxruntime
numpy
opencv-python
tqdm
```

Install:

```bash
pip install -r requirements.txt
```

---

# Real-ESRGAN Setup

Clone repository:

```bash
git clone https://github.com/xinntao/Real-ESRGAN.git
```

Install dependencies:

```bash
cd Real-ESRGAN
pip install -r requirements.txt
```

Download model weights:

```bash
mkdir weights
curl -L https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth \
-o weights/RealESRGAN_x4plus.pth
```

---

# Processing Pipeline

# Stage 1 — Image Discovery

## Tasks

* Scan `source_images`
* Detect supported formats:

  * jpg
  * jpeg
  * png
  * webp
* Preserve all relative paths from `source_images`
* Support dry-run mode to print planned source-to-output mappings without processing files
* Support sample mode to process a limited number of discovered images for QA

## Output Example

```text
source_images/catalog/shirt/red/front.jpg
↓
output_images/catalog/shirt/red/front.webp
```

---

# Stage 2 — Background Removal

## Tool

`rembg`

## Requirements

* Remove old graphical backgrounds
* Preserve transparent edges
* Allow this stage to be enabled or disabled via config/CLI
* Use:

  * `u2net` model

## Example

```python
from rembg import remove
```

## Output

Transparent PNG intermediate files.

Store inside:

```text
temp/bg_removed/
```

---

# Stage 3 — AI Upscaling

## Tool

Real-ESRGAN

## Requirements

* 2x or 4x upscale
* Maintain product realism
* Avoid oversharpening
* Allow this stage to be enabled or disabled via config/CLI
* Detect GPU availability when supported
* Fall back to CPU processing when GPU acceleration is unavailable
* Log the selected execution device for each run

## Recommended Model

```text
RealESRGAN_x4plus
```

## Output

Store inside:

```text
temp/upscaled/
```

---

# Stage 4 — Final Optimization

## Tasks

| Task                      | Details          |
| ------------------------- | ---------------- |
| Convert to WebP           | quality=88–92    |
| Resize if needed          | max 2000px       |
| Strip metadata            | reduce file size |
| Optional white background | configurable     |
| Output format             | WebP default; PNG/JPEG/AVIF optional |

Allow this stage to be enabled or disabled via config/CLI.

---

# Stage 5 — Output Generation

## Final Output Structure

```text
output_images/
├── category-a/
└── category-b/
```

Example:

```text
source_images/furniture/chair1.jpg
↓
output_images/furniture/chair1.webp
```

## Idempotency Requirements

* Skip files when the output already exists and is newer than or equal to the source image
* Reprocess files when the source image has changed since the output was generated
* Provide a force mode to reprocess all files regardless of output state
* Keep deterministic temp paths derived from each image's relative input path

Example:

```text
source_images/catalog/shirt/red/front.jpg
↓
temp/bg_removed/catalog/shirt/red/front.png
↓
temp/upscaled/catalog/shirt/red/front.png
↓
output_images/catalog/shirt/red/front.webp
```

---

# Developer Tasks Breakdown

| Task                     | Owner | Priority |
| ------------------------ | ----- | -------- |
| Project scaffolding      | Dev   | High     |
| Folder traversal utility | Dev   | High     |
| rembg integration        | Dev   | High     |
| Real-ESRGAN integration  | Dev   | High     |
| Output optimization      | Dev   | High     |
| Logging/error handling   | Dev   | Medium   |
| Parallel processing      | Dev   | Medium   |
| Config system            | Dev   | Medium   |
| README/documentation     | Dev   | Medium   |
| QA review tooling        | Dev   | Low      |
| Dry-run/sample modes     | Dev   | Medium   |
| Processing manifest      | Dev   | Medium   |
| Hardware detection       | Dev   | Medium   |
| Stage toggle support     | Dev   | Medium   |

---

# Configuration Requirements

## Create `.env` or `config.json`

Example:

```json
{
  "input_dir": "source_images",
  "output_dir": "output_images",
  "temp_dir": "temp",
  "upscale_factor": 4,
  "webp_quality": 90,
  "output_format": "webp",
  "max_dimension": 2000,
  "background": "transparent",
  "parallel_workers": 4,
  "remove_background": true,
  "upscale": true,
  "optimize": true,
  "dry_run": false,
  "sample_limit": null,
  "force": false,
  "hardware_device": "auto",
  "manifest_path": "processing_report.csv"
}
```

## Config Behavior

* CLI arguments should override config file values
* `hardware_device` should support `auto`, `cpu`, and GPU-specific options where available
* `sample_limit` should process only the first N discovered images when set
* `dry_run` should not create output files or temp files
* `force` should bypass idempotency checks and reprocess all images

---

# Performance Considerations

| Concern                    | Recommendation            |
| -------------------------- | ------------------------- |
| 455 images processing time | Use parallel workers      |
| Large temp files           | Auto-clean temp directory |
| Memory spikes              | Process in batches        |
| CPU/GPU thermal throttling | Limit concurrency         |

---

# Error Handling Requirements

Pipeline must:

* continue on failure
* generate:

  * `success.log`
  * `failed.log`
  * `processing_report.csv` or `processing_report.json`
* include each file's status, input path, output path, dimensions, duration, selected stages, and error details in the processing report
* distinguish skipped files from successful processed files
* log selected hardware mode and fallback events

Failure examples:

* corrupt image
* unsupported format
* AI inference failure
* missing model weights
* unavailable GPU acceleration

---

# Quality Assurance Checklist

## Developers Must Verify

| Check                       | Expected               |
| --------------------------- | ---------------------- |
| Background removed cleanly  | No leftover graphics   |
| Product edges preserved     | No clipping            |
| Colors accurate             | No AI hallucination    |
| File sizes optimized        | Reasonable compression |
| Folder structure maintained | Exact mapping          |
| Transparent PNG handling    | Correct                |
| WebP rendering              | Works in browser       |
| Dry-run output              | Planned mappings are correct |
| Sample mode                 | Limited QA batch works before full run |
| Idempotent skipping         | Unchanged files are skipped correctly |
| Stage toggles               | Each stage can run independently |
| Hardware fallback           | CPU fallback works when GPU is unavailable |

---

# Suggested Deliverables

| Deliverable               | Description        |
| ------------------------- | ------------------ |
| Python pipeline           | Main automation    |
| requirements.txt          | Dependencies       |
| README.md                 | Setup instructions |
| Config system             | Tunable settings   |
| Logs                      | Debugging          |
| Example processed outputs | QA samples         |
| Processing manifest       | Per-file audit trail |
| Dry-run mode              | Safe preview command |
| Sample processing mode    | Small-batch QA workflow |
| Hardware fallback         | Portable CPU/GPU behavior |

---

# Recommended Execution Command

Example:

```bash
python process_images.py
```

Optional:

```bash
python process_images.py --input source_images --output output_images
```

Dry run:

```bash
python process_images.py --dry-run
```

Sample QA run:

```bash
python process_images.py --sample-limit 10
```

Force reprocess:

```bash
python process_images.py --force
```

Disable selected stages:

```bash
python process_images.py --no-upscale
```

---

# Suggested Future Enhancements (Out of Scope)

## Future Version

* AI-generated alternate angles
* Auto shadow generation
* Product centering
* AI relighting
* CDN upload automation
* Shopify/Magento sync
* Background templates

---

# Success Criteria

Pipeline is considered successful when:

| Metric               | Target              |
| -------------------- | ------------------- |
| Bulk automation      | 100%                |
| Manual intervention  | Minimal             |
| Process success rate | >95%                |
| Visual consistency   | High                |
| Output format        | WebP                |
| Processing cost      | Near-zero recurring |

---

# Approach & Reasoning Checklist

| Technique                 | Why Used                               | Where Applied          |
| ------------------------- | -------------------------------------- | ---------------------- |
| Pipeline architecture     | Ensure scalability for 455+ images     | Overall structure      |
| Open-source tooling       | Minimize recurring SaaS costs          | Tech stack             |
| Intermediate staging      | Easier debugging and QA                | temp folder design     |
| Config-driven development | Flexible tuning without code changes   | config.json            |
| Recursive folder mapping  | Preserve existing catalog organization | image discovery        |
| Failure isolation         | Avoid full pipeline crashes            | logging/error handling |
| eCommerce optimization    | Improve frontend delivery performance  | WebP optimization      |

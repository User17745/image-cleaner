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

---

# Configuration Requirements

## Create `.env` or `config.json`

Example:

```json
{
  "input_dir": "source_images",
  "output_dir": "output_images",
  "upscale_factor": 4,
  "webp_quality": 90,
  "max_dimension": 2000,
  "background": "transparent",
  "parallel_workers": 4
}
```

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

Failure examples:

* corrupt image
* unsupported format
* AI inference failure

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

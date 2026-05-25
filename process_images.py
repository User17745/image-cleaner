#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import logging
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **_: Any):  # type: ignore[no-redef]
        return iterable


SUPPORTED_INPUT_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_OUTPUT_FORMATS = {"webp", "png", "jpeg", "jpg", "avif"}


DEFAULT_CONFIG: dict[str, Any] = {
    "input_dir": "source_images",
    "output_dir": "output_images",
    "temp_dir": "temp",
    "upscale_factor": 4,
    "webp_quality": 90,
    "output_format": "webp",
    "max_dimension": 2000,
    "background": "transparent",
    "parallel_workers": 4,
    "remove_background": True,
    "upscale": True,
    "optimize": True,
    "dry_run": False,
    "sample_limit": None,
    "force": False,
    "hardware_device": "auto",
    "manifest_path": "processing_report.csv",
    "realesrgan_executable": "realesrgan-ncnn-vulkan",
}


@dataclass
class ProcessingResult:
    status: str
    input_path: str
    output_path: str
    width: int | None = None
    height: int | None = None
    duration_seconds: float = 0.0
    stages: str = ""
    error: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bulk process images from source_images to output_images.")
    parser.add_argument("--config", default="config.json", help="Path to JSON config file.")
    parser.add_argument("--input", dest="input_dir", help="Input image directory.")
    parser.add_argument("--output", dest="output_dir", help="Output image directory.")
    parser.add_argument("--temp-dir", help="Temporary working directory.")
    parser.add_argument("--output-format", choices=sorted(SUPPORTED_OUTPUT_FORMATS), help="Output format.")
    parser.add_argument("--webp-quality", type=int, help="WebP/JPEG/AVIF quality.")
    parser.add_argument("--max-dimension", type=int, help="Maximum final width/height.")
    parser.add_argument("--parallel-workers", type=int, help="Number of worker threads.")
    parser.add_argument("--sample-limit", type=int, help="Process only the first N discovered images.")
    parser.add_argument("--manifest-path", help="CSV manifest path.")
    parser.add_argument("--hardware-device", choices=["auto", "cpu", "gpu"], help="Requested processing device.")
    parser.add_argument("--realesrgan-executable", help="Real-ESRGAN executable path/name.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned mappings without writing files.")
    parser.add_argument("--force", action="store_true", help="Reprocess files even when outputs are current.")
    parser.add_argument("--no-remove-background", action="store_false", dest="remove_background")
    parser.add_argument("--no-upscale", action="store_false", dest="upscale")
    parser.add_argument("--no-optimize", action="store_false", dest="optimize")
    parser.set_defaults(remove_background=None, upscale=None, optimize=None)
    return parser.parse_args()


def load_config(args: argparse.Namespace) -> dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    config_path = Path(args.config)
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as file:
            config.update(json.load(file))

    for key in (
        "input_dir",
        "output_dir",
        "temp_dir",
        "output_format",
        "webp_quality",
        "max_dimension",
        "parallel_workers",
        "sample_limit",
        "manifest_path",
        "hardware_device",
        "realesrgan_executable",
    ):
        value = getattr(args, key, None)
        if value is not None:
            config[key] = value

    for key in ("dry_run", "force"):
        if getattr(args, key):
            config[key] = True

    for key in ("remove_background", "upscale", "optimize"):
        value = getattr(args, key)
        if value is not None:
            config[key] = value

    config["output_format"] = str(config["output_format"]).lower()
    if config["output_format"] == "jpg":
        config["output_format"] = "jpeg"
    if config["output_format"] not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError(f"Unsupported output format: {config['output_format']}")
    return config


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler("process_images.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def discover_images(input_dir: Path, sample_limit: int | None) -> list[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    images = sorted(
        path for path in input_dir.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_FORMATS
    )
    if sample_limit is not None:
        images = images[:sample_limit]
    return images


def output_path_for(source: Path, input_dir: Path, output_dir: Path, output_format: str) -> Path:
    relative = source.relative_to(input_dir)
    extension = ".jpg" if output_format == "jpeg" else f".{output_format}"
    return output_dir / relative.with_suffix(extension)


def temp_path_for(source: Path, input_dir: Path, temp_dir: Path, stage: str) -> Path:
    relative = source.relative_to(input_dir)
    return temp_dir / stage / relative.with_suffix(".png")


def should_skip(source: Path, output: Path, force: bool) -> bool:
    if force or not output.exists():
        return False
    return output.stat().st_mtime >= source.stat().st_mtime


def remove_background(source: Path, destination: Path) -> None:
    try:
        from rembg import remove
    except ImportError as exc:
        raise RuntimeError("rembg is not installed. Install requirements or use --no-remove-background.") from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes()
    destination.write_bytes(remove(data))


def run_realesrgan(source: Path, destination: Path, config: dict[str, Any]) -> None:
    executable = shutil.which(str(config["realesrgan_executable"]))
    if executable is None:
        raise RuntimeError(
            f"Real-ESRGAN executable not found: {config['realesrgan_executable']}. "
            "Install it or run with --no-upscale."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        executable,
        "-i",
        str(source),
        "-o",
        str(destination),
        "-s",
        str(config["upscale_factor"]),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Real-ESRGAN failed")


def flatten_alpha_on_white(image: Image.Image) -> Image.Image:
    from PIL import Image

    if image.mode not in ("RGBA", "LA"):
        return image.convert("RGB")
    background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    background.alpha_composite(image.convert("RGBA"))
    return background.convert("RGB")


def optimize_image(source: Path, destination: Path, config: dict[str, Any]) -> tuple[int, int]:
    from PIL import Image

    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image.load()
        max_dimension = int(config["max_dimension"])
        if max(image.size) > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        output_format = str(config["output_format"]).lower()
        save_kwargs: dict[str, Any] = {"optimize": True}

        if output_format in {"jpeg", "jpg"}:
            image = flatten_alpha_on_white(image)
            save_format = "JPEG"
            save_kwargs["quality"] = int(config["webp_quality"])
        elif output_format == "webp":
            save_format = "WEBP"
            save_kwargs["quality"] = int(config["webp_quality"])
        elif output_format == "avif":
            save_format = "AVIF"
            save_kwargs["quality"] = int(config["webp_quality"])
        else:
            save_format = "PNG"

        if config["background"] == "white" and image.mode in ("RGBA", "LA"):
            image = flatten_alpha_on_white(image)

        image.save(destination, save_format, **save_kwargs)
        return image.size


def copy_as_output(source: Path, destination: Path) -> tuple[int, int]:
    from PIL import Image

    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image.save(destination)
        return image.size


def process_one(source: Path, input_dir: Path, output_dir: Path, config: dict[str, Any]) -> ProcessingResult:
    start = time.perf_counter()
    output = output_path_for(source, input_dir, output_dir, config["output_format"])
    stages: list[str] = []

    if should_skip(source, output, bool(config["force"])):
        return ProcessingResult(
            status="skipped",
            input_path=str(source),
            output_path=str(output),
            duration_seconds=round(time.perf_counter() - start, 3),
            stages="idempotency",
        )

    try:
        current = source
        if config["remove_background"]:
            bg_removed = temp_path_for(source, input_dir, Path(config["temp_dir"]), "bg_removed")
            remove_background(current, bg_removed)
            current = bg_removed
            stages.append("background_removal")

        if config["upscale"]:
            upscaled = temp_path_for(source, input_dir, Path(config["temp_dir"]), "upscaled")
            run_realesrgan(current, upscaled, config)
            current = upscaled
            stages.append(f"upscale:{config['hardware_device']}")

        if config["optimize"]:
            width, height = optimize_image(current, output, config)
            stages.append("optimization")
        else:
            width, height = copy_as_output(current, output)
            stages.append("copy")

        return ProcessingResult(
            status="success",
            input_path=str(source),
            output_path=str(output),
            width=width,
            height=height,
            duration_seconds=round(time.perf_counter() - start, 3),
            stages="|".join(stages),
        )
    except Exception as exc:
        logging.exception("Failed processing %s", source)
        return ProcessingResult(
            status="failed",
            input_path=str(source),
            output_path=str(output),
            duration_seconds=round(time.perf_counter() - start, 3),
            stages="|".join(stages),
            error=str(exc),
        )


def write_manifest(results: list[ProcessingResult], manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True) if manifest_path.parent != Path(".") else None
    with manifest_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(asdict(results[0]).keys()) if results else list(ProcessingResult("", "", "").__dict__.keys()))
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def write_status_logs(results: list[ProcessingResult]) -> None:
    with Path("success.log").open("w", encoding="utf-8") as success, Path("failed.log").open("w", encoding="utf-8") as failed:
        for result in results:
            if result.status in {"success", "skipped"}:
                success.write(f"{result.status}\t{result.input_path}\t{result.output_path}\n")
            elif result.status == "failed":
                failed.write(f"{result.input_path}\t{result.error}\n")


def print_dry_run(images: list[Path], input_dir: Path, output_dir: Path, config: dict[str, Any]) -> None:
    for source in images:
        output = output_path_for(source, input_dir, output_dir, config["output_format"])
        print(f"{source} -> {output}")
    print(f"Dry run complete. Planned files: {len(images)}")


def main() -> int:
    setup_logging()
    args = parse_args()
    config = load_config(args)
    input_dir = Path(config["input_dir"])
    output_dir = Path(config["output_dir"])

    logging.info("Hardware device requested: %s", config["hardware_device"])
    images = discover_images(input_dir, config["sample_limit"])
    logging.info("Discovered %s image(s)", len(images))

    if config["dry_run"]:
        print_dry_run(images, input_dir, output_dir, config)
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    Path(config["temp_dir"]).mkdir(parents=True, exist_ok=True)

    results: list[ProcessingResult] = []
    workers = max(1, int(config["parallel_workers"]))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_one, image, input_dir, output_dir, config) for image in images]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
            results.append(future.result())

    results.sort(key=lambda result: result.input_path)
    write_manifest(results, Path(config["manifest_path"]))
    write_status_logs(results)

    failed_count = sum(1 for result in results if result.status == "failed")
    skipped_count = sum(1 for result in results if result.status == "skipped")
    success_count = sum(1 for result in results if result.status == "success")
    logging.info("Complete: %s success, %s skipped, %s failed", success_count, skipped_count, failed_count)
    return 1 if failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())

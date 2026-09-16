#!/usr/bin/env python3
"""
generate-studio-shot.py — Clean studio product shot via Higgsfield gpt_image_2.

Usage (run from project root):
  python3 scripts/generate-studio-shot.py brands/[brand]/studio-shots/[output-name]

Reads studio-shot-spec.json from the output folder.
Output: [output-name]_v1.png (auto-increments if file already exists).
"""

import json
import sys
from pathlib import Path

from _higgsfield import run_higgsfield_image, download, resolve_image, save_job_uuid


def _next_version(folder: Path, name: str) -> Path:
    v = 1
    while (folder / f"{name}_v{v}.png").exists():
        v += 1
    return folder / f"{name}_v{v}.png"


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(
            "Usage: python3 scripts/generate-studio-shot.py "
            "brands/[brand]/studio-shots/[output-name]"
        )

    output_dir = Path(sys.argv[1])
    spec_path  = output_dir / "studio-shot-spec.json"

    if not spec_path.exists():
        sys.exit(f"Error: studio-shot-spec.json not found at {spec_path}")

    with open(spec_path) as f:
        spec = json.load(f)

    prompt        = spec.get("prompt", "").strip()
    product_image = spec.get("product_image", "")
    output_name   = spec.get("output_name", output_dir.name)
    aspect_ratio  = spec.get("aspect_ratio", "1:1")

    if not prompt:
        sys.exit("Error: No prompt found in studio-shot-spec.json.")

    if not product_image:
        sys.exit("Error: No product_image found in studio-shot-spec.json.")

    img_path = Path(product_image)
    if not img_path.exists():
        sys.exit(f"Error: Product image not found: {img_path}")

    print(f"\nGenerating studio shot — {output_name} ({aspect_ratio})")
    print("Model: gpt_image_2")
    print("Generating...")

    job = run_higgsfield_image(
        "gpt_image_2",
        prompt,
        images=[resolve_image(str(img_path))],
        aspect_ratio=aspect_ratio,
        quality="high",
        extra=["--resolution", "2k"],
    )

    out_path = _next_version(output_dir, output_name)
    download(job["result_url"], out_path)
    save_job_uuid(job, out_path)

    print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()

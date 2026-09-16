#!/usr/bin/env python3
"""
generate-brand-shot.py — Recompose-mode product shot via Higgsfield gpt_image_2.

Uses a Claude-generated prompt (Style Descriptor + product analysis + Generation
Modifier) instead of passing the reference image directly. The prompt is built
by the /product-shot-generator skill (recompose mode) and saved in shot-spec.json.

Usage (run from project root):
  python3 scripts/generate-brand-shot.py brands/[brand]/product-shots/[output-name]

Reads shot-spec.json from the output folder.
Output: [output-name]_v1.png, v2, v3 ... (never overwrites).
"""

import json
import sys
from pathlib import Path

from _higgsfield import run_higgsfield_image, download, resolve_image, save_job_uuid


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(
            "Usage: python3 scripts/generate-brand-shot.py "
            "brands/[brand]/product-shots/[output-name]"
        )

    output_dir = Path(sys.argv[1])
    spec_path  = output_dir / "shot-spec.json"

    if not spec_path.exists():
        sys.exit(f"shot-spec.json not found in {output_dir}")

    with open(spec_path) as f:
        spec = json.load(f)

    prompt      = spec.get("prompt", "").strip()
    product_img = spec.get("product_image", "")
    output_name = spec.get("output_name", output_dir.name)
    aspect      = spec.get("aspect_ratio", "4:5")

    if not prompt:
        sys.exit("prompt missing from shot-spec.json — run the skill first to generate it.")
    if not product_img:
        sys.exit("product_image missing from shot-spec.json")

    img_path = Path(product_img)
    if not img_path.exists():
        sys.exit(f"Product image not found: {img_path}")

    print(f"\nProduct shot (recompose) — {output_name} ({aspect})")
    print("Model: gpt_image_2")
    print("Generating...")

    job = run_higgsfield_image(
        "gpt_image_2",
        prompt,
        images=[resolve_image(str(img_path))],
        aspect_ratio=aspect,
        quality="high",
        extra=["--resolution", "2k"],
    )

    v, out_path = 1, output_dir / f"{output_name}_v1.png"
    while out_path.exists():
        v += 1
        out_path = output_dir / f"{output_name}_v{v}.png"

    download(job["result_url"], out_path)
    save_job_uuid(job, out_path)

    print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
generate-ad.py — Static ad generation via Higgsfield gpt_image_2.

Usage (run from project root):
  python3 scripts/generate-ad.py brands/[brand]/advertisements/[timestamp]/[NN]-[template-name]

Reads ad-spec.json from the output folder.
Output: [output-name]_v1.png, _v2, _v3 ... (never overwrites).
"""

import json
import sys
from pathlib import Path

from _higgsfield import run_higgsfield_image, download, resolve_image, save_job_uuid


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(
            "Usage: python3 scripts/generate-ad.py "
            "brands/[brand]/advertisements/[timestamp]/[NN]-[template-name]"
        )

    output_dir = Path(sys.argv[1])
    spec_path  = output_dir / "ad-spec.json"

    if not spec_path.exists():
        sys.exit(f"ad-spec.json not found in {output_dir}")

    with open(spec_path) as f:
        spec = json.load(f)

    prompt        = spec.get("prompt", "").strip()
    product_image = spec.get("product_image", "")
    output_name   = spec.get("output_name", output_dir.name)
    aspect        = spec.get("aspect_ratio", "1:1")
    brand         = spec.get("brand", "brand")
    template_name = spec.get("template_name", "ad")

    if not prompt:
        sys.exit("prompt missing from ad-spec.json — run /ad-generator first.")
    if not product_image:
        sys.exit("product_image missing from ad-spec.json")

    img_path = Path(product_image)
    if not img_path.exists():
        sys.exit(f"Product image not found: {img_path}")

    print(f"\nGenerating ad — {brand} / {template_name} ({aspect})")
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

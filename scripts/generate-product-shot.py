#!/usr/bin/env python3
"""
generate-product-shot.py — Recreate-mode product shot via Higgsfield gpt_image_2.

Uploads two images to gpt_image_2 (order preserved):
  Image 1 — scene reference  (environment, framing, light, atmosphere)
  Image 2 — product image    (what gets placed into the scene)

Usage (run from project root):
  python3 scripts/generate-product-shot.py brands/[brand]/product-shots/[output-name]

Reads shot-spec.json from the output folder.
Output: [output-name]_v1.png, v2, v3 ... (never overwrites).
"""

import json
import sys
from pathlib import Path

from _higgsfield import run_higgsfield_image, download, resolve_image, save_job_uuid


PROMPT = (
    "Use image 1 as the compositional blueprint. Lock in its camera position, perspective, "
    "environment, surface material, light direction and quality, tonal grade, and overall atmosphere exactly as captured. "
    "Take the product shown in image 2 and seat it into that scene. "
    "Carry over the product's actual silhouette, surface finish, proportions, and any visible branding without distortion — "
    "draw all product detail from image 2, not from whatever was in the original scene. "
    "The rest of the frame is untouched. No added type or overlays."
)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(
            "Usage: python3 scripts/generate-product-shot.py "
            "brands/[brand]/product-shots/[output-name]"
        )

    output_dir = Path(sys.argv[1])
    spec_path  = output_dir / "shot-spec.json"

    if not spec_path.exists():
        sys.exit(f"shot-spec.json not found in {output_dir}")

    with open(spec_path) as f:
        spec = json.load(f)

    scene_ref   = spec.get("scene_reference", "")
    product_img = spec.get("product_image", "")
    output_name = spec.get("output_name", output_dir.name)
    aspect      = spec.get("aspect_ratio", "4:5")
    notes       = spec.get("notes", "").strip()

    if not scene_ref:
        sys.exit("scene_reference missing from shot-spec.json")
    if not product_img:
        sys.exit("product_image missing from shot-spec.json")

    scene_path = Path(scene_ref)
    img_path   = Path(product_img)

    if not scene_path.exists():
        sys.exit(f"Scene reference not found: {scene_path}")
    if not img_path.exists():
        sys.exit(f"Product image not found: {img_path}")

    prompt = PROMPT if not notes else f"{PROMPT} {notes}"

    print(f"\nProduct shot — {output_name} ({aspect})")
    print("Model: gpt_image_2")
    print("Generating...")

    job = run_higgsfield_image(
        "gpt_image_2",
        prompt,
        images=[resolve_image(str(scene_path)), resolve_image(str(img_path))],
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

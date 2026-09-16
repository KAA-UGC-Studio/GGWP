#!/usr/bin/env python3
"""
generate-product-visual.py — backend for the /product-visual skill.

Reads a spec JSON from a brand subfolder, resolves the source product image
(and optional character headshot for virtual_model_tryout) through the existing
UUID indexing system, fires `higgsfield product-photoshoot create` via the
shared helper, downloads the PNG, and writes a sidecar.

Called by skills/product-visual/SKILL.md as:
    python3 scripts/generate-product-visual.py brands/<brand>/product-visual/<output-name>

Exit codes:
    0  — success
    1  — generic failure (CLI error, malformed spec, etc.)
    2  — backend NSFW filter rejected the prompt. The skill catches this and
         either auto-sanitizes + re-runs OR surfaces the failure to the user.

The script itself does NOT retry on NSFW — retry policy is a skill-layer
concern (the user-facing copy and the sanitization word list live in SKILL.md).
"""

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from _higgsfield import (
    run_product_photoshoot,
    download,
    save_job_uuid,
)


REQUIRED_SPEC_KEYS = ("output_name", "brand", "mode", "product_image", "aspect_ratio")
NSFW_EXIT_CODE = 2

# ─────────────────────────────────────────────────────────────────────────────
# Locked preservation infrastructure — auto-attached to every prompt.
# These three strings concatenate around the user-editable scene_description
# to form the final --prompt that gets sent to product-photoshoot.
# Universal: works for any product (tube, jacket, can, watch, anything).
# ─────────────────────────────────────────────────────────────────────────────
PRESERVATION_TOP = (
    "Replicate the product from the reference image exactly — every color, "
    "gradient, finish, and label detail must match pixel-for-pixel."
)
SHAPE_LOCK = (
    "Preserve the exact product proportions, height-to-width ratio, "
    "and geometry — match the reference image precisely."
)
PRESERVATION_TAIL = (
    "Product appearance must match the reference image exactly — preserve "
    "all label details, color gradient, and finish. Do not substitute or infer."
)


def _next_version(output_dir: Path, output_name: str) -> int:
    """Return the next _v{N} for this output_name, starting at 1."""
    existing = sorted(output_dir.glob(f"{output_name}_v*.png"))
    return len(existing) + 1


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: generate-product-visual.py <output_dir>")

    output_dir = Path(sys.argv[1]).resolve()
    if not output_dir.is_dir():
        sys.exit(f"Output directory not found: {output_dir}")

    spec_path = output_dir / "product-visual-spec.json"
    if not spec_path.exists():
        sys.exit(f"Spec not found: {spec_path}")

    try:
        with open(spec_path) as f:
            spec = json.load(f)
    except (OSError, json.JSONDecodeError) as err:
        sys.exit(f"Failed to read spec: {err}")

    for key in REQUIRED_SPEC_KEYS:
        if key not in spec:
            sys.exit(f"Spec missing required key: '{key}'")

    output_name = spec["output_name"]
    mode = spec["mode"]
    product_image = spec["product_image"]
    character_image = spec.get("character_image")  # optional, virtual_model_tryout only
    aspect_ratio = spec["aspect_ratio"]
    brand_context = spec.get("brand_context", "")
    product_context = spec.get("product_context", "")

    # ── Build the final prompt ──────────────────────────────────────────
    # New format (v1.1): spec stores only `scene_description`; preservation
    # directives are infrastructure, concatenated at fire time.
    # Legacy fallback: if spec has a `prompt` field (older runs), use as-is.
    if "scene_description" in spec:
        scene_description = spec["scene_description"]
        prompt = f"{PRESERVATION_TOP} {scene_description} {SHAPE_LOCK} {PRESERVATION_TAIL}"
    elif "prompt" in spec:
        prompt = spec["prompt"]
    else:
        sys.exit("Spec missing required field: 'scene_description' (or legacy 'prompt')")

    # ── Validate source images exist (we pass paths directly to the CLI) ──
    # `product-photoshoot` does NOT accept upload UUIDs as --image (despite the
    # CLI help saying it should — returns "Not Found"). The CLI does its own
    # internal upload. So we pass file paths, not UUIDs. Other Higgsfield skills
    # that DO accept UUIDs continue to benefit from cross-skill upload caching;
    # this one endpoint is the exception.
    print(f"  mode: {mode}")
    print(f"  product image: {product_image}")
    if not os.path.exists(product_image):
        sys.exit(f"Product image not found: {product_image}")
    images = [product_image]

    if character_image:
        print(f"  character image: {character_image}")
        if not os.path.exists(character_image):
            sys.exit(f"Character image not found: {character_image}")
        images.append(character_image)

    # ── Fire the job ────────────────────────────────────────────────────
    print(f"  submitting product-photoshoot job ({mode}, {aspect_ratio})...")
    job = run_product_photoshoot(
        mode=mode,
        prompt=prompt,
        images=images,
        aspect_ratio=aspect_ratio,
        brand_context=brand_context,
        product_context=product_context,
    )

    # ── NSFW handling: exit with code 2 so the skill can detect ─────────
    if job["status"] == "nsfw":
        sys.stderr.write(
            "Backend NSFW filter rejected this prompt. "
            "Skill should sanitize trigger words and retry once.\n"
        )
        sys.exit(NSFW_EXIT_CODE)

    # ── Download to versioned filename + write sidecar ──────────────────
    version = _next_version(output_dir, output_name)
    out_path = output_dir / f"{output_name}_v{version}.png"
    print(f"  downloading → {out_path.name}")
    download(job["url"], out_path)

    # save_job_uuid reads job["id"] — pass the extracted-from-filename UUID.
    save_job_uuid({"id": job["job_uuid"]}, out_path)

    print(f"\n✅ saved: {out_path}")
    print(f"   sidecar: {out_path.name}.uuid")


if __name__ == "__main__":
    main()

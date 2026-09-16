#!/usr/bin/env python3
"""
generate-product-video.py — Generate a Marketing Studio Video (non-UGC cinematic).

Wraps Higgsfield's `marketing_studio_video` model behind the `/product-video`
skill, covering the four NON-UGC modes. Sibling of generate-ugc-content.py —
same backend, same entity resolution; only the mode map and brief shape differ.

Reads a spec JSON, silently resolves entities (optional avatar from
character_dir, product from product_image via the dual URL/medias path),
composes the brief into a single --prompt, and emits a versioned MP4.

Run from the project root:

  python3 scripts/generate-product-video.py brands/<brand>/product-video/<mode>/<output-name>

The folder must contain `product-video-spec.json`.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _higgsfield import (
    resolve_avatar,
    resolve_product,
    resolve_image,
    run_marketing_studio_video,
    remap_aspect,
    download,
    save_job_uuid,
)


# Operator-facing mode label → Higgsfield CLI `--mode` slug.
# The label appears in the SKILL.md picker and in product-video-spec.json's `mode` field.
# The slug is what `marketing_studio_video --mode` actually takes.
#
# Website preset → label → slug:
#   Hypermotion        → product_motion_film  → product_showcase
#   Wildcard           → creative_video_mode  → wild_card
#   TV Spot            → cinematic_brand_spot  → tv_spot
#   Pro Virtual Try-on → editorial_tryon       → virtual_try_on  (NOT ugc_virtual_try_on)
MODE_MAP = {
    "product_motion_film": "product_showcase",
    "creative_video_mode": "wild_card",
    "cinematic_brand_spot": "tv_spot",
    "editorial_tryon":      "virtual_try_on",
}


def compose_prompt(spec: dict) -> str:
    """Build the --prompt string from the derived brief slots.

    Setting / Action / Mood are universal. Tagline is appended for the brand
    spot (end-card line); product detail is appended for try-on (so closeups
    render true construction detail). Empty slots are skipped cleanly.
    """
    parts = []
    if spec.get("setting"):
        parts.append(f"Setting: {spec['setting']}.")
    action = spec.get("action") or spec.get("motion")  # 'motion' = legacy field name
    if action:
        parts.append(f"Action: {action}.")
    if spec.get("mood"):
        parts.append(f"Mood: {spec['mood']}.")
    if spec.get("tagline"):
        parts.append(f"Tagline (end card): {spec['tagline']}.")
    if spec.get("product_detail"):
        parts.append(f"Product detail: {spec['product_detail']}.")
    return " ".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Marketing Studio cinematic (non-UGC) video."
    )
    parser.add_argument(
        "output_dir",
        help="Folder containing product-video-spec.json (versioned MP4 is written here).",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    spec_path = output_dir / "product-video-spec.json"

    if not spec_path.exists():
        sys.exit(f"product-video-spec.json not found at {spec_path}")

    with open(spec_path) as f:
        spec = json.load(f)

    # --- Mode ---
    output_name = spec.get("output_name") or output_dir.name
    mode_label = spec.get("mode")
    if mode_label not in MODE_MAP:
        sys.exit(f"Unknown mode '{mode_label}'. Valid: {', '.join(MODE_MAP.keys())}")
    mode_slug = MODE_MAP[mode_label]

    # --- Prompt: slots are authoritative. Recompose from them every run so an
    # edited slot can never be silently overridden by a stale stored `prompt`.
    # Fall back to a stored `prompt` only when no slots are present. ---
    prompt = compose_prompt(spec) or spec.get("prompt")
    if not prompt:
        sys.exit("Spec has no brief slots and no 'prompt' to compose from.")

    # --- Settings (standard: 1080p / 8s / 9:16 / audio on) ---
    aspect_ratio   = remap_aspect(spec.get("aspect_ratio", "9:16"))  # silent 4:5 -> 3:4
    resolution     = spec.get("resolution", "1080p")
    generate_audio = bool(spec.get("generate_audio", True))

    # Marketing Studio Video caps duration at 15s — clamp defensively.
    duration = int(spec.get("duration", 8))
    if duration > 15:
        print(f"  duration {duration}s exceeds the 15s max — clamping to 15s.")
        duration = 15
    elif duration < 1:
        duration = 1

    # --- Resolve optional avatar (model passthrough is per-mode) ---
    # If the spec carries a character_dir, the model is ON: headshot → avatar
    # entity, fullbody → --medias outfit-lock reference. Absent character_dir
    # means product-only (Higgsfield auto-casts if the mode needs a person).
    avatar_uuid = None
    medias_list = []
    if spec.get("character_dir"):
        avatar_uuid = resolve_avatar(spec["character_dir"])
        fullbody_path = os.path.join(spec["character_dir"], "fullbody.png")
        if os.path.exists(fullbody_path):
            medias_list.append(resolve_image(fullbody_path))

    # --- Resolve product (dual-path: URL entity vs. manual medias) ---
    product_uuid = None
    if spec.get("product_image"):
        product_result = resolve_product(spec["product_image"])
        if product_result["type"] == "product_id":
            product_uuid = product_result["uuid"]
        elif product_result["type"] == "media_ref":
            medias_list.append(product_result["uuid"])

    if not medias_list:
        medias_list = None

    # --- Versioned output filename ---
    existing = sorted(output_dir.glob(f"{output_name}_v*.mp4"))
    out_path = output_dir / f"{output_name}_v{len(existing) + 1}.mp4"

    # --- Generate (blocks via --wait until the job completes) ---
    print(f"\nGenerating Product Video ({mode_label} → mode={mode_slug})")
    print(f"  duration:   {duration}s")
    print(f"  resolution: {resolution}")
    print(f"  aspect:     {aspect_ratio}")
    print(f"  audio:      {'on' if generate_audio else 'off'}")
    print(f"  avatar:     {avatar_uuid or '(none — product only)'}")
    print(f"  product:    {product_uuid or '(none — passed via medias)'}")
    print(f"  medias:     {medias_list if medias_list else '(none)'}")
    print(f"  prompt:     {prompt}")

    job = run_marketing_studio_video(
        prompt=prompt,
        avatar_uuid=avatar_uuid,
        product_uuid=product_uuid,
        medias=medias_list,
        mode=mode_slug,
        aspect_ratio=aspect_ratio,
        duration=duration,
        resolution=resolution,
        generate_audio=generate_audio,
    )

    result_url = job.get("result_url")
    if not result_url:
        sys.exit(f"Job completed but no result_url in response: {json.dumps(job)[:500]}")

    download(result_url, out_path)
    save_job_uuid(job, out_path)

    print(f"\n✅ Done. Saved:\n  {out_path}")


if __name__ == "__main__":
    main()

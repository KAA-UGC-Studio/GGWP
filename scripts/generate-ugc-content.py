#!/usr/bin/env python3
"""
generate-ugc-content.py — Generate a Marketing Studio Video (UGC-style).

Wraps Higgsfield's `marketing_studio_video` model behind the `/ugc-content`
skill. Reads a spec JSON, silently resolves the Marketing Studio entities
(avatar from character_dir, product from product_image, optional outfit-lock
medias from character's fullbody.png), and emits a versioned MP4.

Run from the project root:

  python3 scripts/generate-ugc-content.py brands/<brand>/ugc-content/<mode>/<output-name>

The folder must contain `ugc-content-spec.json`.
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
    download,
    save_job_uuid,
)


# User-facing mode label → Higgsfield CLI slug.
# The label appears in the SKILL.md picker and in ugc-content-spec.json's `mode` field.
# The slug is what `marketing_studio_video --mode` actually takes.
MODE_MAP = {
    "ugc":      "ugc",
    "tutorial": "ugc_how_to",
    "unboxing": "ugc_unboxing",
    "review":   "product_review",
    "tryon":    "ugc_virtual_try_on",
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Marketing Studio UGC-style video."
    )
    parser.add_argument(
        "output_dir",
        help="Folder containing ugc-content-spec.json (versioned MP4 is written here).",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    spec_path = output_dir / "ugc-content-spec.json"

    if not spec_path.exists():
        sys.exit(f"ugc-content-spec.json not found at {spec_path}")

    with open(spec_path) as f:
        spec = json.load(f)

    # --- Required spec fields ---
    output_name = spec.get("output_name") or output_dir.name
    mode_label = spec.get("mode", "ugc")
    if mode_label not in MODE_MAP:
        sys.exit(
            f"Unknown mode '{mode_label}'. Valid: {', '.join(MODE_MAP.keys())}"
        )
    mode_slug = MODE_MAP[mode_label]

    prompt = spec.get("prompt")
    if not prompt:
        sys.exit("Spec is missing the 'prompt' field (composed brief is required).")

    # --- Optional spec fields with sensible fallbacks ---
    aspect_ratio = spec.get("aspect_ratio", "9:16")
    duration     = int(spec.get("duration", 12))
    resolution   = spec.get("resolution", "1080p")
    generate_audio = bool(spec.get("generate_audio", True))

    # --- Resolve entities silently ---
    # Outfit-lock is permanently ON: when a character is provided, fullbody.png
    # is always passed via --medias to reinforce body/outfit identity.
    avatar_uuid = None
    medias_list = []
    if spec.get("character_dir"):
        avatar_uuid = resolve_avatar(spec["character_dir"])
        fullbody_path = os.path.join(spec["character_dir"], "fullbody.png")
        if os.path.exists(fullbody_path):
            fullbody_uuid = resolve_image(fullbody_path)
            medias_list.append(fullbody_uuid)

    # --- Resolve product (dual-path) ---
    # Returns a tagged dict:
    #   {"type": "product_id", "uuid": <entity-uuid>} → URL-having: pass via --product_ids
    #   {"type": "media_ref",  "uuid": <upload-uuid>} → manual product: pass via --medias
    product_uuid = None
    if spec.get("product_image"):
        product_result = resolve_product(spec["product_image"])
        if product_result["type"] == "product_id":
            product_uuid = product_result["uuid"]
        elif product_result["type"] == "media_ref":
            # Manual product: append the product image upload UUID to medias
            # (alongside fullbody outfit-lock). No --product_ids passed.
            medias_list.append(product_result["uuid"])

    # Normalize medias_list back to None if empty (helper expects None or non-empty list)
    if not medias_list:
        medias_list = None

    # --- Versioned output filename ---
    existing = sorted(output_dir.glob(f"{output_name}_v*.mp4"))
    next_v = len(existing) + 1
    out_path = output_dir / f"{output_name}_v{next_v}.mp4"

    # --- Generate ---
    print(f"\nGenerating Marketing Studio Video ({mode_label} → mode={mode_slug})")
    print(f"  duration:   {duration}s")
    print(f"  resolution: {resolution}")
    print(f"  aspect:     {aspect_ratio}")
    print(f"  audio:      {'on' if generate_audio else 'off'}")
    print(f"  avatar:     {avatar_uuid or '(none)'}")
    print(f"  product:    {product_uuid or '(none — passed via medias)'}")
    print(f"  medias:     {medias_list if medias_list else '(none)'}")

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

    # --- Download + sidecar ---
    result_url = job.get("result_url")
    if not result_url:
        sys.exit(f"Job completed but no result_url in response: {json.dumps(job)[:500]}")

    download(result_url, out_path)
    save_job_uuid(job, out_path)

    print(f"\n✅ Done. Saved:\n  {out_path}")


if __name__ == "__main__":
    main()

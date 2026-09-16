#!/usr/bin/env python3
"""
product-ugc-generator.py — Product UGC image and video pipeline (Higgsfield CLI).

Two stages:
  --image   Generate a UGC selfie of a character holding a product (9:16 2K via nano_banana_2)
  --video   Animate the selfie into a talking-head video (9:16 via veo3_1)

When --image and --video are both passed in a single invocation, the video
stage uses the image stage's job UUID directly — no re-upload.

Image inputs:
  Image 1 — product being held
  Image 2 — character headshot (identity reference)

Usage (run from project root):
  python3 scripts/product-ugc-generator.py brands/[brand]/product-ugc/[output-name] --image
  python3 scripts/product-ugc-generator.py brands/[brand]/product-ugc/[output-name] --video
  python3 scripts/product-ugc-generator.py brands/[brand]/product-ugc/[output-name] --image --video

Outputs:
  [output-name]_v1.png       (increments on each run)
  [output-name]-run1.mp4     (increments on each run)
"""

import argparse
import json
import sys
from pathlib import Path

from _higgsfield import run_higgsfield_image, run_higgsfield_video, download, resolve_image, save_job_uuid


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

UGC_IMAGE_PROMPT = """Photorealistic UGC-style iPhone front-camera selfie. The subject's face and identity must exactly match Image 2. High angle shot — the subject is {action}, phone raised above at arm's length, looking directly into the camera with a candid, natural expression. Their other hand holds the product clearly visible toward the camera, fully in frame. Every detail of the product must be 100% accurate to Image 1 — replicate all labels, text, and branding exactly.

---

Scene: {location}
Outfit: {clothing}
Frame: Compact selfie close-up — face centered, head to upper chest, minimal space above the hairline.
Light: Soft, ambient natural light — subtle catchlights in the eyes.
Aesthetic: Authentic iPhone quality — raw sensor feel, natural shallow-focus background blur. Skin looks real: visible pores, fine surface texture, no smoothing or retouching.
Negative Prompt: No visible phone, no hands holding a phone, no mirrors, no artificial lighting."""


# ---------------------------------------------------------------------------
# Module-level UUID stash for intra-process handoff between --image and --video
# ---------------------------------------------------------------------------

_last_image_job_id = None


# ---------------------------------------------------------------------------
# Image stage
# ---------------------------------------------------------------------------

def create_image(output_dir: Path, spec: dict) -> None:
    global _last_image_job_id

    character_dir = Path(spec["character_dir"])
    product_image = Path(spec["product_image"])
    action        = spec.get("action", "")
    location      = spec.get("location", "")
    clothing      = spec.get("clothing", "")

    headshot = character_dir / "headshot.png"

    for label, path in [
        ("product image", product_image),
        ("character headshot", headshot),
    ]:
        if not path.exists():
            sys.exit(f"Missing {label}: {path}")

    prompt = UGC_IMAGE_PROMPT.format(
        action=action,
        location=location,
        clothing=clothing,
    )
    (output_dir / "image-prompt.txt").write_text(prompt)

    print(f"\n{output_dir.name} — UGC image")
    print("Model: nano_banana_2")
    print("Generating UGC selfie...")

    job = run_higgsfield_image(
        "nano_banana_2",
        prompt,
        images=[resolve_image(str(product_image)), resolve_image(str(headshot))],
        aspect_ratio="9:16",
        extra=["--resolution", "2k"],
    )

    output_name = spec.get("output_name", output_dir.name)
    existing = sorted(output_dir.glob(f"{output_name}_v*.png"))
    next_version = len(existing) + 1
    out_path = output_dir / f"{output_name}_v{next_version}.png"
    download(job["result_url"], out_path)
    save_job_uuid(job, out_path)

    _last_image_job_id = job["id"]

    print(f"  saved → {out_path.name}")
    print(f"\nDone. {out_path}")


# ---------------------------------------------------------------------------
# Video stage
# ---------------------------------------------------------------------------

def create_video(output_dir: Path, spec: dict) -> None:
    output_name = spec.get("output_name", output_dir.name)

    # Source selection. If the image stage just ran in this invocation, use
    # its job UUID directly (no re-upload). Otherwise, fall back to the
    # saved PNG on disk.
    image_ref = None
    image_stem = None

    if _last_image_job_id:
        image_ref = _last_image_job_id
        existing = sorted(output_dir.glob(f"{output_name}_v*.png"))
        if existing:
            image_stem = existing[-1].stem
        else:
            image_stem = f"{output_name}_v1"
    else:
        chosen = spec.get("video_image_version")
        if chosen:
            image_path = output_dir / f"{output_name}_v{chosen}.png"
        else:
            candidates = sorted(output_dir.glob(f"{output_name}_v*.png"))
            if not candidates:
                sys.exit(f"No image found in {output_dir}. Run --image first.")
            image_path = candidates[-1]

        if not image_path.exists():
            sys.exit(f"Image not found: {image_path}")

        image_ref = resolve_image(str(image_path))
        image_stem = image_path.stem

    action   = spec.get("action", "")
    script   = spec.get("script", "")
    delivery = spec.get("voice_notes", "")
    duration = str(spec.get("duration", "6"))

    if duration not in {"4", "6", "8"}:
        sys.exit(f"Duration must be 4, 6, or 8 seconds. Got: '{duration}'")

    sections = []
    if action:
        sections.append(f"Scene: {action}")
    if script:
        sections.append(f"Spoken: {script}")
    if delivery:
        sections.append(f"Voice: {delivery}")
    sections.append("The subject moves naturally but keeps the product visible and in frame throughout the entire shot.")
    video_prompt = "\n".join(sections)

    (output_dir / "video-prompt.txt").write_text(video_prompt)

    print(f"\n{output_name} — UGC video")
    print(f"Model: veo3_1 ({duration}s, 9:16, quality=high)")
    print("Generating...")

    job = run_higgsfield_video(
        "veo3_1",
        video_prompt,
        image=image_ref,
        aspect_ratio="9:16",
        duration=int(duration),
        quality="high",
    )

    existing_runs = sorted(output_dir.glob(f"{image_stem}-run*.mp4"))
    next_run = len(existing_runs) + 1
    out_path = output_dir / f"{image_stem}-run{next_run}.mp4"
    print("  Saving video...", end=" ", flush=True)
    download(job["result_url"], out_path)
    save_job_uuid(job, out_path)
    print("done")
    print(f"\nDone. {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate a product UGC selfie image and/or talking-head video.")
    parser.add_argument("output_dir", help="Output folder containing product-ugc-spec.json")
    parser.add_argument("--image", action="store_true", help="Run the image generation stage")
    parser.add_argument("--video", action="store_true", help="Run the video generation stage")
    args = parser.parse_args()

    if not args.image and not args.video:
        sys.exit("Specify --image, --video, or both.")

    output_dir = Path(args.output_dir)
    spec_path  = output_dir / "product-ugc-spec.json"

    if not spec_path.exists():
        sys.exit(f"product-ugc-spec.json not found at {spec_path}")

    with open(spec_path) as f:
        spec = json.load(f)

    if args.image:
        create_image(output_dir, spec)
    if args.video:
        create_video(output_dir, spec)


if __name__ == "__main__":
    main()

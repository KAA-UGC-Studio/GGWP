#!/usr/bin/env python3
"""
generate-character-fullbody-kie.py — generate a character's full-body casting
digital from an existing headshot, via kie.ai Nano Banana Pro.

Mirrors the Higgsfield character full-body step, but on the kie.ai backend:
  1. Upload <character_dir>/headshot.png → public URL
  2. nano-banana-pro image-to-image, using the headshot as the face reference
  3. Download result → <character_dir>/fullbody.png

Usage:
    python scripts/generate-character-fullbody-kie.py brands/saturdays/characters/dianti
"""

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _kie

MODEL = "nano-banana-pro"
ASPECT = "3:4"
RESOLUTION = "2K"


def _characteristics(character_dir: Path) -> str:
    spec_path = character_dir / "character-spec.json"
    if not spec_path.exists():
        return ""
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    parts = [spec.get("characteristics", "")]
    for field in ("top", "bottom", "shoes", "accessories"):
        val = spec.get(field)
        if val:
            parts.append(f"{field}: {val}")
    return "\n".join(p for p in parts if p)


def _build_prompt(characteristics: str) -> str:
    return (
        "Full-length studio casting digital of the exact same woman shown in the "
        "reference image. Preserve her facial identity, skin tone, and features "
        "precisely. Full body visible head to feet, standing straight and facing "
        "the camera in a neutral relaxed casting pose, arms at her sides, natural "
        "expression. She keeps the same beige/nude chiffon hijab as the reference, "
        "styled cleanly, worn with a simple modern modest outfit — plain neutral "
        "long-sleeve top and straight-leg trousers, clean minimal shoes. "
        "Plain light-grey seamless studio backdrop, soft even clinical studio "
        "lighting, sharp focus, photorealistic, natural proportions, 3:4 vertical "
        "full-body framing.\n\n"
        f"Character reference:\n{characteristics}"
    )


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: python scripts/generate-character-fullbody-kie.py <character_dir>")

    character_dir = Path(sys.argv[1]).resolve()
    if not character_dir.is_dir():
        sys.exit(f"Character directory not found: {character_dir}")

    headshot = character_dir / "headshot.png"
    if not headshot.exists():
        sys.exit(f"headshot.png not found in {character_dir}")

    out_path = character_dir / "fullbody.png"

    print(f"Character: {character_dir.name}")
    credits = _kie.get_credit()
    print(f"kie.ai credits: {credits}")
    if credits <= 0:
        sys.exit("No kie.ai credits — top up at https://kie.ai/pricing")

    face_url = _kie.upload_file(str(headshot))
    prompt = _build_prompt(_characteristics(character_dir))

    print(f"Generating full-body via {MODEL} ({RESOLUTION}, {ASPECT})…")
    task_id = _kie.create_task(MODEL, {
        "prompt": prompt,
        "image_input": [face_url],
        "aspect_ratio": ASPECT,
        "resolution": RESOLUTION,
        "output_format": "png",
    })
    print(f"  task: {task_id}")
    urls = _kie.poll_task(task_id, timeout_min=20)
    if not urls:
        sys.exit("Task completed but returned no result URLs.")

    _kie.download(urls[0], out_path)
    print(f"✅ Saved: {out_path}")


if __name__ == "__main__":
    main()

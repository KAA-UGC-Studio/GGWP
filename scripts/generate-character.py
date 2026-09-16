#!/usr/bin/env python3
"""
generate-character.py — Character generation pipeline (Higgsfield CLI).

Produces a headshot, a full-body casting digital and a six-angle face sheet
for a brand character, using the physical characteristics saved in
character-spec.json.

Usage (run from project root):
  python3 scripts/generate-character.py brands/[brand]/characters/[name]
  python3 scripts/generate-character.py brands/[brand]/characters/[name] --multiangle-only
  python3 scripts/generate-character.py brands/[brand]/characters/[name] --no-multiangle

Step 1: headshot                   →  nano_banana_2 (text-to-image, or
                                      image-reference when the spec face-locks
                                      to a reference photo)
Step 2: image-reference full body  →  nano_banana_2 with Step 1's job_id
Step 3: six-angle face sheet       →  nano_banana_2 with Step 1's job_id

Outputs saved to brands/[brand-name]/characters/[character-name]/
  headshot.png
  fullbody.png
  multiangle.png      (re-runs version as multiangle_v2.png, _v3.png, ...)
"""

import argparse
import json
import sys
from pathlib import Path

from _higgsfield import run_higgsfield_image, download, resolve_image, save_job_uuid


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

HEADSHOT_PROMPT = """Clean front-facing studio portrait. Figure looking straight into the lens.

Character: {characteristics}

Clothing: {clothing}

Facial features and skin texture: Clean natural skin, no makeup, no retouching. Natural skin captured at full detail — slightly visible pores, minimal freckling, minimal natural skin irregularities, realistic skin texture. Skin completely unedited, no smoothing, no corrections. Keep natural facial asymmetry intact. Groomed but natural brows and lashes. Minimal flyaway hairs. Subtle realistic under-eye texture.

Pose and shot framing: Upright posture, head held straight. Tight vertical headshot framing, from just above the head down to the chin line. Eyes looking straight into the camera. Neutral facial expression, no smile. Neck straight and relaxed. Keep clothing out of the frame.

Light: Direct on-camera flash, aimed straight at the model. Every skin detail clearly visible. Subtle specular highlights across the T-zone. Minimal shadow behind the model, flat on the backdrop. No softbox or beauty lighting.

Camera specs: Full-frame camera, 75–85mm lens, f/8 aperture. Full frame sharp, no blurring. 3:4 vertical format, minimal natural grain. 5750–5800K white balance, daylight neutral. No colour grading.

Environment: Clean pale grey background, no texture."""


# Headshot variant used when the spec face-locks the character to a real
# person's photo (`reference_mode: "face_lock"`). The reference is passed as
# an image ref; the prompt keeps the same studio recipe as HEADSHOT_PROMPT so
# face-locked and generated characters look like the same casting session.
REFERENCE_HEADSHOT_PROMPT = """Clean front-facing studio portrait of the exact same person as the reference image. Preserve their facial identity precisely — bone structure, eye shape and colour, nose, lips, skin tone and natural skin detail all matched to the reference. Figure looking straight into the lens.

Character: {characteristics}

Clothing: {clothing}

Facial features and skin texture: Clean natural skin, no makeup, no retouching. Natural skin captured at full detail — slightly visible pores, minimal freckling, minimal natural skin irregularities, realistic skin texture. Skin completely unedited, no smoothing, no corrections. Keep natural facial asymmetry intact. Groomed but natural brows and lashes. Minimal flyaway hairs. Subtle realistic under-eye texture.

Pose and shot framing: Upright posture, head held straight. Tight vertical headshot framing, from just above the head down to the chin line. Eyes looking straight into the camera. Neutral facial expression, no smile. Neck straight and relaxed. Keep clothing out of the frame.

Light: Direct on-camera flash, aimed straight at the model. Every skin detail clearly visible. Subtle specular highlights across the T-zone. Minimal shadow behind the model, flat on the backdrop. No softbox or beauty lighting.

Camera specs: Full-frame camera, 75–85mm lens, f/8 aperture. Full frame sharp, no blurring. 3:4 vertical format, minimal natural grain. 5750–5800K white balance, daylight neutral. No colour grading.

Environment: Clean pale grey background, no texture."""


FULLBODY_PROMPT = """Full body studio shot. Face and full anatomical structure matched exactly to the reference image — bone structure, body proportions and gender alignment preserved throughout.

Character: {characteristics}

Facial reference: Maintain exact face consistency with the reference image. Groomed but natural brows and lashes, minimal flyaway hairs, subtle realistic under-eye texture. Skin completely unedited — slightly visible pores, minimal freckling, natural facial asymmetry intact. Matching the reference throughout.

Pose and framing: Full body visible, small gap at top and bottom. Upright relaxed stance, arms at sides, chest parallel to the lens. Eyes looking straight into the camera, neutral facial expression.

Clothing: {clothing}

Camera specs: Full-frame camera, 75–85mm lens, f/8 aperture. Sharp from head to feet, no blurring. 3:4 vertical format, minimal natural grain. 5750–5800K white balance, daylight neutral. No colour grading.

Environment: Same pale grey background as the reference image, no texture."""


MULTIANGLE_PROMPT = """Six-panel casting angle sheet of the exact same person as the reference image. One single image divided into a clean grid, 2 columns by 3 rows, six head-and-shoulders portraits separated by thin white gutters. No captions, no labels, no borders, no numbering.

Character: {characteristics}

Panel order, left to right then top to bottom:
1. Front view at eye level, looking straight into the lens.
2. Three-quarter view, head turned about 30 degrees to her left, eyes following the same direction.
3. Three-quarter view, head turned about 30 degrees to her right.
4. Tighter front view from a slightly low angle, looking straight into the lens.
5. Full side profile, 90 degrees, looking off frame.
6. Front view with a slight head turn and a slight high angle, eyes on the lens.

Identity: Face matched exactly to the reference image in every panel — bone structure, eye shape and colour, nose, lips, jawline, skin tone and natural facial asymmetry all identical. Same hairstyle and same parting in every panel. Same clothing in every panel: {clothing_top}.

Facial features and skin texture: Clean natural skin, no makeup, no retouching, slightly visible pores, minimal freckling, realistic skin texture. Neutral expression in every panel, no smile.

Light and environment: Identical flat clinical studio light in all six panels, direct on-camera flash, minimal shadow. Clean pale grey seamless background, no texture, identical in every panel.

Camera specs: Full-frame camera, 75–85mm lens, f/8 aperture. Sharp throughout, minimal natural grain, 5750–5800K white balance, no colour grading."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _next_version(path: Path) -> Path:
    """Return `path` if free, else the next `<stem>_vN<suffix>` that is.

    Angle sheets version rather than overwrite (`multiangle.png`,
    `multiangle_v2.png`, ...) so an earlier sheet a downstream skill already
    uploaded keeps working. Downstream skills read the HIGHEST version.
    """
    if not path.exists():
        return path
    version = 2
    while True:
        candidate = path.with_name(f"{path.stem}_v{version}{path.suffix}")
        if not candidate.exists():
            return candidate
        version += 1


def latest_multiangle(character_dir: Path):
    """Return the highest-versioned angle sheet in the folder, or None."""
    sheets = sorted(character_dir.glob("multiangle*.png"))
    return sheets[-1] if sheets else None


def _clothing(spec: dict) -> str:
    parts = [
        spec.get("top", "White t-shirt"),
        spec.get("bottom", "Blue jeans"),
        spec.get("shoes", "White Air Force 1s"),
    ]
    accessories = spec.get("accessories", "")
    if accessories:
        parts.append(accessories)
    return ", ".join(parts)


def _check_consent(spec: dict, character_dir: Path) -> None:
    """Refuse to face-lock a real person without a recorded consent block.

    The likeness of a real person ends up in ads, so `reference_mode:
    "face_lock"` requires `consent.status` in character-spec.json (a dated
    verbal yes is enough — see skills/character-creator/SKILL.md).
    """
    consent = spec.get("consent") or {}
    if not consent.get("status"):
        sys.exit(
            f"Refusing to face-lock: {character_dir}/character-spec.json has "
            f'reference_mode "face_lock" but no consent.status.\n'
            f"Record consent for the person in the reference photo first "
            f"(see skills/character-creator/SKILL.md, Step 2)."
        )


def generate_multiangle(character_dir: Path, characteristics: str, spec: dict, face_ref) -> Path:
    """Generate the six-angle face sheet from an existing headshot reference."""
    prompt = MULTIANGLE_PROMPT.format(
        characteristics=characteristics,
        clothing_top=spec.get("top", "White t-shirt"),
    )
    job = run_higgsfield_image(
        "nano_banana_2",
        prompt,
        images=[face_ref],
        aspect_ratio="9:16",
        extra=["--resolution", "2k"],
    )
    out_path = _next_version(character_dir / "multiangle.png")
    download(job["result_url"], out_path)
    save_job_uuid(job, out_path)
    print(f"  {out_path.name} saved")
    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a character's headshot, full body and six-angle face sheet."
    )
    parser.add_argument("character_dir", help="brands/[brand]/characters/[character-name]")
    parser.add_argument(
        "--multiangle-only",
        action="store_true",
        help="Only generate the angle sheet, from the existing headshot.png.",
    )
    parser.add_argument(
        "--no-multiangle",
        action="store_true",
        help="Skip the angle sheet (headshot + full body only).",
    )
    args = parser.parse_args()

    character_dir = Path(args.character_dir)
    spec_path = character_dir / "character-spec.json"

    if not spec_path.exists():
        sys.exit(f"character-spec.json not found at {spec_path}")

    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)

    character_name  = spec.get("character_name", character_dir.name)
    characteristics = spec.get("characteristics", "").strip()

    if not characteristics:
        sys.exit("character-spec.json has no characteristics.")

    clothing = _clothing(spec)

    headshot_path = character_dir / "headshot.png"
    fullbody_path = character_dir / "fullbody.png"

    # ── Angle sheet only — reuse the headshot that is already on disk ────────
    if args.multiangle_only:
        if not headshot_path.exists():
            sys.exit(
                f"--multiangle-only needs an existing headshot at {headshot_path}. "
                f"Run without the flag to generate the character first."
            )
        print(f"\nGenerating angle sheet: {character_name}")
        generate_multiangle(
            character_dir, characteristics, spec, resolve_image(str(headshot_path))
        )
        print(f"\nAngle sheet ready → {character_dir}/")
        return

    # ── Reference photo (optional) ───────────────────────────────────────────
    # "face_lock" → the result IS the person in the photo, so the reference is
    # passed to the headshot call. "inspired" needs nothing here: the operator
    # already turned the photo into `characteristics` during the skill.
    reference_mode = (spec.get("reference_mode") or "").strip()
    reference_image = spec.get("reference_image")
    face_lock = reference_mode == "face_lock"

    if face_lock:
        _check_consent(spec, character_dir)
        if not reference_image:
            sys.exit('reference_mode is "face_lock" but character-spec.json has no reference_image.')
        reference_path = character_dir / reference_image
        if not reference_path.exists():
            sys.exit(f"Reference image not found: {reference_path}")

    print(f"\nGenerating character: {character_name}")

    print("Step 1 — headshot")
    if face_lock:
        print(f"  face-locked to {reference_image}")
        job = run_higgsfield_image(
            "nano_banana_2",
            REFERENCE_HEADSHOT_PROMPT.format(characteristics=characteristics, clothing=clothing),
            images=[resolve_image(str(reference_path))],
            aspect_ratio="3:4",
            extra=["--resolution", "2k"],
        )
    else:
        job = run_higgsfield_image(
            "nano_banana_2",
            HEADSHOT_PROMPT.format(characteristics=characteristics, clothing=clothing),
            aspect_ratio="3:4",
            extra=["--resolution", "2k"],
        )
    download(job["result_url"], headshot_path)
    save_job_uuid(job, headshot_path)
    headshot_job_id = job["id"]
    print("  headshot.png saved")

    print("Step 2 — full body")
    job = run_higgsfield_image(
        "nano_banana_2",
        FULLBODY_PROMPT.format(characteristics=characteristics, clothing=clothing),
        images=[headshot_job_id],
        aspect_ratio="3:4",
        extra=["--resolution", "2k"],
    )
    download(job["result_url"], fullbody_path)
    save_job_uuid(job, fullbody_path)
    print("  fullbody.png saved")

    if not args.no_multiangle:
        print("Step 3 — angle sheet")
        generate_multiangle(character_dir, characteristics, spec, headshot_job_id)

    print(f"\nCharacter ready → {character_dir}/")


if __name__ == "__main__":
    main()

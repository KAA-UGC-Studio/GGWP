#!/usr/bin/env python3
"""
generate-ugc-content-kie.py — UGC-style video on the kie.ai backend.

The kie.ai analogue of generate-ugc-content.py (Higgsfield). kie.ai has no
Marketing Studio Video pipeline, so this builds the video in two stages:

  Stage 1 — Nano Banana Pro: compose a still of the character USING/WEARING the
            product (character headshot + product image as reference inputs).
  Stage 2 — routed video model: Gemini Omni Flash (talking-head with spoken
            dialogue, the default — supersedes Veo 3.1), Kling 2.6 (realistic
            + sound effects, no dialogue), Kling 3.0 (cinematic multi-shot, no
            dialogue) or Seedance 2.0 Fast (dynamic motion, no dialogue)
            animates the still. Routed from the brief; on failure the script retries
            once on veo3_fast (legacy but proven talking-head path).

Reads a spec JSON (see skills/ugc-content-kie/SKILL.md) and writes a versioned
MP4 (+ the intermediate still) into the spec's folder.

Usage:
    python scripts/generate-ugc-content-kie.py brands/saturdays/ugc-content-kie/tryon/dianti-...-tryon
"""

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _kie

STILL_MODEL = "nano-banana-pro"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Video model routing — picked from the brief.
# "speaks" models voice the spoken script; non-speaking models get a
# dialogue-free composed prompt (motion + ambient sound carry the story).
VIDEO_MODELS = {
    "gemini-omni-flash": {
        "endpoint": "jobs",
        "slug": "gemini-omni-video",
        "speaks": True,
        "label": "Gemini Omni Flash — best talking-head w/ dialogue (supersedes Veo 3.1)",
    },
    "veo3_fast": {
        "endpoint": "veo",
        "speaks": True,
        "label": "Veo 3.1 Fast — talking-head w/ dialogue (legacy, fallback only)",
    },
    "veo3": {
        "endpoint": "veo",
        "speaks": True,
        "label": "Veo 3.1 Quality — talking-head w/ dialogue (legacy)",
    },
    "kling-2.6": {
        "endpoint": "jobs",
        "slug": "kling-2.6/image-to-video",
        "speaks": False,
        "label": "Kling 2.6 — realistic motion + sound effects, no dialogue",
    },
    "kling-3.0": {
        "endpoint": "jobs",
        "slug": "kling-3.0/video",
        "speaks": False,
        "label": "Kling 3.0 — cinematic motion, native ambient audio, no dialogue (its dialogue mode is zh/en only)",
    },
    "seedance-2-fast": {
        "endpoint": "jobs",
        "slug": "bytedance/seedance-2-fast",
        "speaks": False,
        "label": "Seedance 2.0 Fast — dynamic physical motion, no dialogue",
    },
    "seedance-2-5": {
        "endpoint": "jobs",
        "slug": "bytedance/seedance-2-5",
        "speaks": False,
        "label": "Seedance 2.5 — best physics + prompt-following, up to 30s in one call, no dialogue (priciest)",
    },
}

# Aspect ratios bytedance/seedance-2-5 accepts; anything else 400s, and its
# default ("adaptive") just follows the first frame.
SEEDANCE_25_ASPECTS = ("1:1", "4:3", "3:4", "16:9", "9:16", "21:9")

# The only aspect ratios kling-3.0/video accepts; anything else 400s.
KLING_3_ASPECTS = ("16:9", "9:16", "1:1")
MAX_SEEDANCE_25_SECONDS = 30
DEFAULT_VIDEO_MODEL = "gemini-omni-flash"
FALLBACK_VIDEO_MODEL = "veo3_fast"


def _load_spec(spec_dir: Path) -> dict:
    spec_path = spec_dir / "ugc-content-kie-spec.json"
    if not spec_path.exists():
        sys.exit(f"Spec not found: {spec_path}")
    try:
        return json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        sys.exit(f"Bad spec JSON: {err}")


def _resolve(path_str: str) -> Path:
    """Resolve a spec path relative to project root (specs use repo-relative paths)."""
    p = Path(path_str)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


def _character_identity(character_dir: Path) -> str:
    spec_path = character_dir / "character-spec.json"
    if not spec_path.exists():
        return ""
    try:
        return json.loads(spec_path.read_text(encoding="utf-8")).get("characteristics", "")
    except (OSError, json.JSONDecodeError):
        return ""


def _compose_still_prompt(spec: dict, identity: str) -> str:
    if spec.get("still_prompt"):
        return spec["still_prompt"]
    product = spec.get("product_name") or "the product"
    setting = spec.get("setting", "")
    return (
        "Photorealistic vertical UGC-style photo. The exact same person from the "
        "FIRST reference image (preserve their facial identity, skin tone, and hair "
        "or head covering precisely) is naturally wearing/using the product shown "
        f"in the SECOND reference image — {product}. Casual authentic phone-camera "
        f"selfie energy, looking toward camera. {setting}. Natural believable "
        "lighting, candid framing.\n\n"
        f"Character reference:\n{identity}"
    )


def _compose_video_prompt(spec: dict, spoken: bool = True) -> str:
    if spec.get("video_prompt"):
        return spec["video_prompt"]
    scene = spec.get("scene", "")
    hero = spec.get("hero", "")
    if not spoken:
        # Kling / Seedance path — no spoken dialogue, motion carries the story.
        return (
            f"{scene} Natural handheld UGC-style motion — no spoken dialogue, "
            "authentic ambient sound only. Keep the product clearly visible and "
            "the subject's face and identity consistent throughout the shot."
        )
    return (
        f"{scene} She speaks casually and warmly to camera in Indonesian (Bahasa "
        "Indonesia), like a real UGC creator sharing a genuine recommendation"
        + (f", naturally mentioning that {hero.lower()}" if hero else "")
        + ". Handheld selfie feel, authentic ambient audio, natural lip-sync."
    )


def _run_video_stage(
    video_model: str,
    video_prompt: str,
    still_url: str,
    aspect: str,
    duration: int,
    resolution: str,
) -> list:
    """Dispatch to the routed video model. Veo keeps its dedicated endpoint."""
    cfg = VIDEO_MODELS[video_model]
    if cfg["endpoint"] == "veo":
        return _kie.generate_veo_video(
            prompt=video_prompt,
            image_urls=[still_url],
            model=video_model,
            aspect_ratio=aspect,
            duration=duration,
            resolution=resolution,
            timeout_min=30,
        )
    if video_model == "gemini-omni-flash":
        task_input = {
            "prompt": video_prompt,
            "image_urls": [still_url],
            "aspect_ratio": aspect,
            # omni accepts only 4/6/8/10s, as a string
            "duration": str(duration if duration in (4, 6, 8, 10) else 8),
            "resolution": resolution,
        }
    elif video_model == "kling-2.6":
        task_input = {
            # schema: image_urls max 1, duration "5" | "10", sound required
            "prompt": video_prompt,
            "image_urls": [still_url],
            "duration": "5" if duration <= 5 else "10",
            "sound": True,
        }
    elif video_model == "kling-3.0":
        task_input = {
            "prompt": video_prompt,
            "image_urls": [still_url],
            # cost guardrail: std mode, capped at 10s (pro/4K tiers cost far more)
            "duration": str(min(duration, 10)),
            "mode": "std",
            "sound": True,
            # required even in single-shot mode: without it createTask fails
            # with "multi_shots cannot be empty"
            "multi_shots": False,
        }
        # aspect_ratio is an enum here, unlike the other models — an
        # unsupported ratio 400s, so let the still set the shape instead.
        if aspect in KLING_3_ASPECTS:
            task_input["aspect_ratio"] = aspect
    elif video_model == "seedance-2-5":
        task_input = {
            # schema: first/last frame and the reference_* arrays are mutually
            # exclusive — we send a first frame, so the arrays stay unused
            "prompt": video_prompt,
            "first_frame_url": still_url,
            # integer here (2.0 Fast takes a string), 4-30s
            "duration": min(duration, MAX_SEEDANCE_25_SECONDS),
            # cost guardrail: 720p is 63 cr/s, 1080p 114 — pinned, not passed through
            "resolution": "720p",
            "generate_audio": True,
        }
        if aspect in SEEDANCE_25_ASPECTS:
            task_input["aspect_ratio"] = aspect
    else:  # seedance-2-fast
        task_input = {
            "prompt": video_prompt,
            "first_frame_url": still_url,
            "duration": str(duration),
            "generate_audio": True,
        }
    task_id = _kie.create_task(cfg["slug"], task_input)
    return _kie.poll_task(task_id, timeout_min=30)


def _next_version(out_dir: Path, output_name: str) -> int:
    existing = list(out_dir.glob(f"{output_name}_v*.mp4"))
    nums = []
    for f in existing:
        m = re.search(rf"{re.escape(output_name)}_v(\d+)\.mp4$", f.name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: python scripts/generate-ugc-content-kie.py <spec_dir>")

    spec_dir = Path(sys.argv[1]).resolve()
    spec = _load_spec(spec_dir)

    output_name = spec["output_name"]
    character_dir = _resolve(spec["character_dir"])
    product_image = _resolve(spec["product_image"])
    headshot = character_dir / "headshot.png"

    for p in (headshot, product_image):
        if not p.exists():
            sys.exit(f"Required input missing: {p}")

    # New specs use video_model; legacy specs used veo_model — both accepted.
    video_model = spec.get("video_model") or spec.get("veo_model") or DEFAULT_VIDEO_MODEL
    if video_model not in VIDEO_MODELS:
        print(f"  ⚠️  Unknown video_model '{video_model}' — using {DEFAULT_VIDEO_MODEL}")
        video_model = DEFAULT_VIDEO_MODEL
    aspect = spec.get("aspect_ratio", "9:16")
    duration = int(spec.get("duration", 8))
    resolution = spec.get("resolution", "1080p")

    print(f"Output: {output_name}   (mode: {spec.get('mode')})")
    credits = _kie.get_credit()
    print(f"kie.ai credits: {credits}")
    if credits <= 0:
        sys.exit("No kie.ai credits — top up at https://kie.ai/pricing")

    version = _next_version(spec_dir, output_name)

    # ── Stage 1 — compose the still (character wearing/using the product) ──
    print("Stage 1/2 — composing still via Nano Banana Pro…")
    face_url = _kie.upload_file(str(headshot))
    product_url = _kie.upload_file(str(product_image))
    still_prompt = _compose_still_prompt(spec, _character_identity(character_dir))

    still_urls = _kie.generate_image(
        prompt=still_prompt,
        model=STILL_MODEL,
        aspect_ratio=aspect,
        extra_input={
            "image_input": [face_url, product_url],
            "resolution": "2K",
            "output_format": "png",
        },
        timeout_min=15,
    )
    if not still_urls:
        sys.exit("Stage 1 returned no still image.")
    still_path = spec_dir / f"{output_name}_still_v{version}.png"
    _kie.download(still_urls[0], still_path)
    print(f"  still saved: {still_path.name}")

    # ── Stage 2 — animate the still via the routed video model ──
    spoken = VIDEO_MODELS[video_model]["speaks"]
    print(f"Stage 2/2 — animating via {VIDEO_MODELS[video_model]['label']} ({duration}s {resolution})…")
    video_prompt = _compose_video_prompt(spec, spoken)
    try:
        video_urls = _run_video_stage(
            video_model, video_prompt, still_urls[0], aspect, duration, resolution
        )
    except SystemExit as err:
        # Routed model failed — retry once on the proven fallback (mirrors the
        # generate-with-fallback). Fallback speaks, so recompose spoken.
        if video_model == FALLBACK_VIDEO_MODEL:
            raise
        print(f"  ⚠️  {video_model} failed ({err}) — retrying on {FALLBACK_VIDEO_MODEL}…")
        video_model = FALLBACK_VIDEO_MODEL
        video_prompt = _compose_video_prompt(spec, spoken=True)
        # Veo supports 4/6/8s only — cap longer routed durations on fallback
        video_urls = _run_video_stage(
            video_model, video_prompt, still_urls[0], aspect, min(duration, 8), resolution
        )
    if not video_urls:
        sys.exit("Stage 2 completed but returned no video URL.")
    video_path = spec_dir / f"{output_name}_v{version}.mp4"
    _kie.download(video_urls[0], video_path)

    remaining = _kie.get_credit()
    print(f"✅ Saved: {video_path}  (video model: {video_model})")
    print(f"   still:  {still_path.name}")
    print(f"   kie.ai credits remaining: {remaining} (used ~{credits - remaining})")


if __name__ == "__main__":
    main()

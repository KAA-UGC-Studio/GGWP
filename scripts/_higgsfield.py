"""
_higgsfield.py — shared helpers for Higgsfield CLI generation.

All generation scripts in this project subprocess-call the `higgsfield`
binary through these functions so the JSON parsing, error surfacing, and
aspect-ratio remapping live in one place.

Auth is global (`higgsfield auth login`) — no API key in `.env`.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests

# On Windows the npm-installed CLI is a .cmd/.ps1 shim, which subprocess
# can't launch by bare name — resolve the real path once via PATH lookup.
HIGGSFIELD_BIN = shutil.which("higgsfield") or "higgsfield"


# ---------------------------------------------------------------------------
# Aspect ratio
# ---------------------------------------------------------------------------

# Higgsfield's image models (gpt_image_2, nano_banana_2) do not accept 4:5.
# The existing spec JSON files use 4:5 heavily — remap to the closest
# supported portrait ratio.
ASPECT_REMAP = {
    "4:5": "3:4",
}


def remap_aspect(aspect_ratio: str) -> str:
    """Return a Higgsfield-supported aspect ratio. Prints a notice on remap."""
    if not aspect_ratio:
        return aspect_ratio
    remapped = ASPECT_REMAP.get(aspect_ratio, aspect_ratio)
    if remapped != aspect_ratio:
        print(f"  aspect remap: {aspect_ratio} → {remapped}")
    return remapped


def _clean_prompt(s: str) -> str:
    """Collapse newlines/whitespace in a CLI string arg to a single line.

    Higgsfield's Windows CLI (higgsfield.cmd v0.1.40) misreads --prompt /
    --brand_context / --product_context when their value contains literal
    newlines: the argument boundary is silently broken, which then drops
    the next --image reference and submits the job with no product photo.
    Mac/Linux shells handle multiline args correctly, so this is a pure
    Windows-CLI workaround — no behavioral change on macOS.

    Reported by Ahmed Saad on first ship day. Applied to every string arg
    that the CLI parses positionally.
    """
    if not s:
        return s
    return " ".join(str(s).split())


# ---------------------------------------------------------------------------
# Higgsfield CLI call
# ---------------------------------------------------------------------------

def _run_cli(args: list) -> dict:
    """
    Run `higgsfield <args> --wait --wait-timeout 30m --json` and return the first job dict.

    The default `--wait` timeout is 10m, which is too short for longer
    marketing_studio_video jobs (15s output can exceed 10m of server time).
    Bumping to 30m has no downside for shorter jobs — they return as soon as
    the job's status flips to 'completed'.

    On nonzero exit: prints stderr verbatim and exits.
    On status != 'completed': prints status + any error info and exits.
    """
    full_args = [HIGGSFIELD_BIN,*args, "--wait", "--wait-timeout", "30m", "--json"]
    result = subprocess.run(full_args, capture_output=True, text=True, encoding="utf-8")

    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout or "higgsfield CLI failed\n")
        sys.exit(1)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as err:
        sys.exit(f"Could not parse higgsfield JSON output: {err}\nOutput: {result.stdout[:500]}")

    if not isinstance(payload, list) or not payload:
        sys.exit(f"Unexpected higgsfield response shape: {result.stdout[:500]}")

    job = payload[0]
    status = job.get("status")
    if status != "completed":
        err = job.get("error") or job.get("error_message") or ""
        sys.exit(f"Job ended with status '{status}'. {err}")

    return job


# ---------------------------------------------------------------------------
# UUID indexing (sidecar files)
# ---------------------------------------------------------------------------

# Sidecar format (Phase 3.0): 3-line plain text next to the source file at `<path>.uuid`.
#   Line 1: the Higgsfield UUID (upload id for user files, job id for generated files)
#   Line 2: the file's mtime at the time the sidecar was written (float)
#   Line 3: the Higgsfield cloudfront URL (optional — present for upload sidecars, may be absent for legacy 2-line sidecars and for job-output sidecars where URL isn't needed)
# On reuse, current mtime is compared against stored mtime — if they differ,
# the file is treated as changed and re-uploaded.
# Line 3 is needed by `resolve_avatar()` (Marketing Studio Avatar creation requires --image-url).
# Legacy 2-line sidecars from Phase 2 still parse cleanly; URL is returned as None and
# downstream callers can either look it up via `upload list` or trigger a re-upload.


def _read_sidecar(sidecar_path: str):
    """Returns (uuid, mtime, url) from a sidecar file, or (None, None, None) if missing/malformed.

    URL is None for 2-line (legacy) sidecars and for sidecars where no URL was captured.
    """
    if not os.path.exists(sidecar_path):
        return (None, None, None)
    try:
        with open(sidecar_path) as f:
            lines = f.read().strip().split("\n")
        if len(lines) >= 2:
            uuid_str = lines[0].strip()
            mtime = float(lines[1].strip())
            url = lines[2].strip() if len(lines) >= 3 and lines[2].strip() else None
            return (uuid_str, mtime, url)
    except (ValueError, OSError):
        pass
    return (None, None, None)


def _write_sidecar(sidecar_path: str, uuid_str: str, mtime: float, url: str = None) -> None:
    """Write a sidecar. 3-line if URL provided, 2-line if not.

    The 3-line form is preferred (captures URL for Marketing Studio entity creation).
    The 2-line fallback exists for job-output sidecars where URL isn't relevant.
    """
    with open(sidecar_path, "w") as f:
        f.write(f"{uuid_str}\n{mtime}\n")
        if url:
            f.write(f"{url}\n")


# Module-level cache of upload IDs known to exist on the Higgsfield account.
# Populated lazily on first stale-check, refreshed when a stale UUID forces re-upload.
_known_upload_ids = None


def _get_known_upload_ids(force_refresh: bool = False) -> set:
    """Return the set of upload UUIDs currently visible to the account.

    Cached at module level so we only hit `upload list` once per process. The
    paged `upload list --size 50` covers the most recent 50 uploads — UUIDs
    older than that may not be present and will be treated as stale (forcing
    a re-upload). Cheap false positive: an extra upload call. Real safety:
    we never pass UUIDs Higgsfield has garbage-collected to downstream calls.
    """
    global _known_upload_ids
    if _known_upload_ids is not None and not force_refresh:
        return _known_upload_ids

    result = subprocess.run(
        [HIGGSFIELD_BIN, "upload", "list", "--image", "--size", "50", "--json"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        # Don't block — if we can't verify, fall through and let downstream calls error.
        _known_upload_ids = set()
        return _known_upload_ids

    try:
        uploads = json.loads(result.stdout)
    except json.JSONDecodeError:
        _known_upload_ids = set()
        return _known_upload_ids

    if not isinstance(uploads, list):
        _known_upload_ids = set()
        return _known_upload_ids

    _known_upload_ids = {u.get("id") for u in uploads if u.get("id")}
    return _known_upload_ids


def resolve_image(path: str) -> str:
    """
    Return a Higgsfield UUID for a local file.

    If a sidecar (`<path>.uuid`) exists AND its stored mtime matches the file's
    current mtime AND the stored UUID is still alive on Higgsfield's side,
    return the stored UUID. Otherwise upload the file via `higgsfield upload
    create`, write/update the sidecar (3-line including cloudfront URL), and
    return the new UUID.

    Stale-UUID defense: Higgsfield garbage-collects uploads over time. A sidecar
    can hold a UUID that no longer exists server-side, causing downstream
    `media_input` lookups to fail with "Media input not found". This function
    pre-verifies the UUID against the most recent 50 uploads before trusting
    the sidecar; if missing, it forces a fresh re-upload + sidecar rewrite.

    Errors out cleanly if the file doesn't exist or the upload fails.
    """
    if not os.path.exists(path):
        sys.exit(f"resolve_image: file not found: {path}")

    sidecar_path = path + ".uuid"
    current_mtime = os.path.getmtime(path)

    stored_uuid, stored_mtime, _stored_url = _read_sidecar(sidecar_path)
    if stored_uuid and stored_mtime == current_mtime:
        if stored_uuid in _get_known_upload_ids():
            return stored_uuid
        print(f"  sidecar UUID stale (Higgsfield garbage-collected), re-uploading: {path}")

    # Upload required (no sidecar, or mtime changed)
    print(f"  uploading: {path}")
    result = subprocess.run(
        [HIGGSFIELD_BIN, "upload", "create", path, "--json"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout or "higgsfield upload failed\n")
        sys.exit(1)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as err:
        sys.exit(f"Could not parse upload JSON: {err}\nOutput: {result.stdout[:500]}")

    new_uuid = payload.get("id")
    new_url = payload.get("url")  # cloudfront URL — captured at upload time for later use
    if not new_uuid:
        sys.exit(f"Upload response missing 'id': {result.stdout[:500]}")

    _write_sidecar(sidecar_path, new_uuid, current_mtime, url=new_url)
    return new_uuid


def get_upload_url(path: str) -> str:
    """
    Return the Higgsfield cloudfront URL for a local file's upload.

    Reads the 3-line sidecar. If URL is missing (2-line legacy sidecar), looks it
    up via `upload list` paginated search by UUID. If still not found, re-uploads
    to obtain a fresh URL.

    Used by `resolve_avatar()` and any other caller that needs `--image-url`.
    """
    if not os.path.exists(path):
        sys.exit(f"get_upload_url: file not found: {path}")

    # Ensure an upload exists first.
    uuid_str = resolve_image(path)

    # Re-read sidecar to get URL.
    sidecar_path = path + ".uuid"
    _stored_uuid, _stored_mtime, stored_url = _read_sidecar(sidecar_path)
    if stored_url:
        return stored_url

    # Legacy 2-line sidecar — look up URL via upload list.
    found_url = _lookup_upload_url(uuid_str)
    if found_url:
        # Backfill sidecar to 3-line for next time.
        current_mtime = os.path.getmtime(path)
        _write_sidecar(sidecar_path, uuid_str, current_mtime, url=found_url)
        return found_url

    # URL not findable via list — re-upload to get a fresh one.
    print(f"  re-uploading for URL: {path}")
    # Force re-upload by touching/invalidating: just remove sidecar and recurse.
    try:
        os.remove(sidecar_path)
    except OSError:
        pass
    resolve_image(path)
    _stored_uuid, _stored_mtime, stored_url = _read_sidecar(sidecar_path)
    if not stored_url:
        sys.exit(f"get_upload_url: could not recover URL for {path} after re-upload")
    return stored_url


def _lookup_upload_url(target_uuid: str, max_pages: int = 10, page_size: int = 50) -> str:
    """Look up a cloudfront URL by upload UUID via paginated `upload list --json`.

    Returns the URL or None if not found within max_pages.
    """
    for _ in range(max_pages):
        result = subprocess.run(
            [HIGGSFIELD_BIN, "upload", "list", "--image", "--size", str(page_size), "--json"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode != 0:
            return None
        try:
            uploads = json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
        if not isinstance(uploads, list):
            return None
        for entry in uploads:
            if entry.get("id") == target_uuid:
                return entry.get("url")
        # Naive paging: in this CLI version `upload list` does not surface a cursor
        # in JSON output; we stop after one page. Fallback strategy is re-upload.
        break
    return None


def save_job_uuid(job: dict, output_path) -> None:
    """
    Write a sidecar next to a generated file containing the job's UUID + the
    file's current mtime. Call after `download(job["result_url"], output_path)`.

    Silently no-ops if the job dict is malformed or the file isn't on disk —
    callers should not branch on this.
    """
    output_path = str(output_path)
    job_id = job.get("id")
    if not job_id:
        return
    if not os.path.exists(output_path):
        return
    sidecar_path = output_path + ".uuid"
    current_mtime = os.path.getmtime(output_path)
    _write_sidecar(sidecar_path, job_id, current_mtime)


def resolve_avatar(character_dir: str) -> str:
    """
    Return a Marketing Studio Avatar entity UUID for a character.

    Reads `<character_dir>/character-spec.json` for the character name.
    Uses `<character_dir>/headshot.png` as the avatar source.
    Sidecar at `<character_dir>/headshot.png.avatar.uuid` stores (avatar_uuid, headshot_mtime, preview_url).

    Cascading invalidation: if `headshot.png`'s current mtime differs from the
    mtime stored in the avatar sidecar, the avatar entity is recreated. This
    prevents stale server-side entities pointing at outdated uploads.

    Used by Marketing Studio Video / DTC Ads / any skill that wants a
    `--avatars [{id, type: "custom"}]` reference.
    """
    character_dir = str(character_dir)
    if not os.path.isdir(character_dir):
        sys.exit(f"resolve_avatar: character directory not found: {character_dir}")

    headshot_path = os.path.join(character_dir, "headshot.png")
    if not os.path.exists(headshot_path):
        sys.exit(f"resolve_avatar: headshot.png not found in {character_dir}")

    spec_path = os.path.join(character_dir, "character-spec.json")
    if not os.path.exists(spec_path):
        sys.exit(f"resolve_avatar: character-spec.json not found in {character_dir}")
    try:
        with open(spec_path) as f:
            spec = json.load(f)
        character_name = spec.get("character_name") or os.path.basename(character_dir)
    except (OSError, json.JSONDecodeError) as err:
        sys.exit(f"resolve_avatar: failed to read character-spec.json: {err}")

    avatar_sidecar_path = headshot_path + ".avatar.uuid"
    current_headshot_mtime = os.path.getmtime(headshot_path)

    # Cascading invalidation check — if headshot.png has been modified since the
    # avatar entity was created, the entity points at a stale upload.
    stored_avatar_uuid, stored_source_mtime, _stored_preview_url = _read_sidecar(avatar_sidecar_path)
    if stored_avatar_uuid and stored_source_mtime == current_headshot_mtime:
        return stored_avatar_uuid

    # Need to create (or re-create) the avatar entity.
    print(f"  creating Marketing Studio Avatar: {character_name}")

    # Ensure upload exists + capture cloudfront URL.
    upload_uuid = resolve_image(headshot_path)
    cdn_url = get_upload_url(headshot_path)

    result = subprocess.run(
        [HIGGSFIELD_BIN, "marketing-studio", "avatars", "create",
         "--name", character_name,
         "--image", upload_uuid,
         "--image-url", cdn_url,
         "--json"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout or "avatars create failed\n")
        sys.exit(1)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as err:
        sys.exit(f"Could not parse avatars create JSON: {err}\nOutput: {result.stdout[:500]}")

    if not isinstance(payload, list) or not payload:
        sys.exit(f"Unexpected avatars create response shape: {result.stdout[:500]}")

    avatar_entity = payload[0]
    avatar_uuid = avatar_entity.get("id")
    preview_url = avatar_entity.get("preview_url")
    if not avatar_uuid:
        sys.exit(f"avatars create response missing 'id': {result.stdout[:500]}")

    _write_sidecar(avatar_sidecar_path, avatar_uuid, current_headshot_mtime, url=preview_url)
    return avatar_uuid


def resolve_product(product_image_path: str) -> dict:
    """
    Return a tagged dict describing how to reference a product in
    Marketing Studio Video / DTC Ads calls.

    Two paths based on whether the product has a `page_url` in products.json:

      {"type": "product_id", "uuid": <Marketing Studio Product entity UUID>}
        — for URL-having products. Uses `products fetch --url` to create a
          full Marketing Studio Product entity (with auto-scraped 4 image angles,
          title, description). Caller passes via `--product_ids` (best quality
          path; Higgsfield uses the full entity context).
        — `.product.uuid` sidecar caches the entity UUID + primary media URL.

      {"type": "media_ref", "uuid": <upload UUID for the product image>}
        — for manual products (empty page_url). Delegates to resolve_image()
          to ensure the local image is uploaded; returns the upload UUID.
          No Marketing Studio Product entity is created (the `products create`
          CLI command returns HTTP 405 server-side as of 0.1.40 — we work
          around it). Caller passes this UUID via `--medias` as a media_input
          reference alongside any other media (e.g. fullbody for outfit lock).
        — Uses the standard `.uuid` upload sidecar via resolve_image().

    The product image must live under `brands/<brand>/product-images/<filename>`
    so that the corresponding `brands/<brand>/products.json` entry can be looked
    up to retrieve the product's `page_url`.

    Cascading invalidation for URL-having products: if the source product image
    mtime drifted past the stored mtime, the product entity is re-created
    (it may point at a stale upload).

    Used by Marketing Studio Video / DTC Ads / any skill that needs to
    reference a product visually.
    """
    product_image_path = str(product_image_path)
    if not os.path.exists(product_image_path):
        sys.exit(f"resolve_product: product image not found: {product_image_path}")

    # Locate the products.json entry by filename to retrieve page_url.
    filename = os.path.basename(product_image_path)
    products_json_path = _find_products_json_for(product_image_path)
    if not products_json_path:
        sys.exit(
            f"resolve_product: could not locate products.json for {product_image_path}. "
            f"Expected layout: brands/<brand>/product-images/<file> + brands/<brand>/products.json"
        )

    try:
        with open(products_json_path) as f:
            index = json.load(f)
    except (OSError, json.JSONDecodeError) as err:
        sys.exit(f"resolve_product: failed to read {products_json_path}: {err}")

    entry = None
    for product in index.get("products", []):
        if product.get("filename") == filename:
            entry = product
            break
    if not entry:
        sys.exit(
            f"resolve_product: no entry in {products_json_path} matches filename '{filename}'. "
            f"Re-run /brand-dna-builder to register the product, or add it to products.json manually."
        )

    page_url = entry.get("page_url") or ""
    product_name = entry.get("name") or filename

    # ────────────────────────────────────────────────────────────────────
    # Manual-product path: no page_url → return media_ref
    # ────────────────────────────────────────────────────────────────────
    if not page_url:
        print(f"  resolving manual product (no URL) as media reference: {product_name}")
        upload_uuid = resolve_image(product_image_path)
        return {"type": "media_ref", "uuid": upload_uuid}

    # ────────────────────────────────────────────────────────────────────
    # URL-having product path: fetch (or reuse cached) Marketing Studio Product entity
    # ────────────────────────────────────────────────────────────────────
    product_sidecar_path = product_image_path + ".product.uuid"
    current_mtime = os.path.getmtime(product_image_path)

    # Cascading invalidation check.
    stored_product_uuid, stored_source_mtime, _stored_url = _read_sidecar(product_sidecar_path)
    if stored_product_uuid and stored_source_mtime == current_mtime:
        return {"type": "product_id", "uuid": stored_product_uuid}

    print(f"  fetching Marketing Studio Product: {product_name} ({page_url})")
    result = subprocess.run(
        [HIGGSFIELD_BIN, "marketing-studio", "products", "fetch",
         "--url", page_url,
         "--wait",
         "--json"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout or "products fetch failed\n")
        sys.exit(1)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as err:
        sys.exit(f"Could not parse products fetch JSON: {err}\nOutput: {result.stdout[:500]}")

    # products fetch returns a single object (NOT an array, unlike avatars create).
    if not isinstance(payload, dict):
        sys.exit(f"Unexpected products fetch response shape (expected object): {result.stdout[:500]}")

    status = payload.get("status")
    if status != "completed":
        fail_reason = payload.get("fail_reason") or ""
        sys.exit(f"products fetch ended with status '{status}'. {fail_reason}")

    product_uuid = payload.get("id")
    # Pull the primary media URL for the sidecar (for diagnostics / future skills).
    primary_url = None
    for media in payload.get("medias", []):
        if media.get("is_primary"):
            primary_url = media.get("url")
            break
    if not primary_url and payload.get("medias"):
        primary_url = payload["medias"][0].get("url")

    if not product_uuid:
        sys.exit(f"products fetch response missing 'id': {result.stdout[:500]}")

    _write_sidecar(product_sidecar_path, product_uuid, current_mtime, url=primary_url)
    return {"type": "product_id", "uuid": product_uuid}


def _find_products_json_for(product_image_path: str) -> str:
    """Given a product image path, walk up directories to find the brand's products.json.

    Expected layout: brands/<brand>/product-images/<file>.<ext>
    Returns the path to brands/<brand>/products.json, or None if not found.
    """
    abs_path = os.path.abspath(product_image_path)
    parent = os.path.dirname(abs_path)
    # parent should end with "product-images"; brand dir is its parent.
    if os.path.basename(parent) != "product-images":
        return None
    brand_dir = os.path.dirname(parent)
    candidate = os.path.join(brand_dir, "products.json")
    if os.path.exists(candidate):
        return candidate
    return None


def _warn_if_too_many_refs(images) -> None:
    """Print a warning if more than 8 image refs are being passed (Higgsfield operational limit)."""
    if images and len(images) > 8:
        print(f"  ⚠️  Passing {len(images)} image refs — Higgsfield CLI typically fails above 8.")


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

def run_higgsfield_image(
    model: str,
    prompt: str,
    images=None,
    aspect_ratio=None,
    quality=None,
    extra=None,
) -> dict:
    """
    Submit an image generation job. Returns the job dict.

    `images` is a list of paths or UUIDs, passed as `--image <x>` one per
    item, in order (Higgsfield preserves order in the medias array).
    """
    args = ["generate", "create", model, "--prompt", _clean_prompt(prompt)]

    if images:
        _warn_if_too_many_refs(images)
        for ref in images:
            args.extend(["--image", str(ref)])

    if aspect_ratio:
        args.extend(["--aspect_ratio", remap_aspect(aspect_ratio)])

    if quality:
        args.extend(["--quality", quality])

    if extra:
        args.extend(extra)

    return _run_cli(args)


# ---------------------------------------------------------------------------
# Video generation
# ---------------------------------------------------------------------------

def run_higgsfield_video(
    model: str,
    prompt: str,
    image: str,
    aspect_ratio: str = "9:16",
    duration: int = 6,
    quality: str = "high",
    model_variant: str = "veo-3-1-fast",
    extra=None,
) -> dict:
    """
    Submit a video generation job. Returns the job dict.

    `image` is a single path or UUID. Higgsfield's veo3_1 schema has no
    prompt-enhancement or audio toggle — both are server-side defaults.
    """
    args = [
        "generate", "create", model,
        "--prompt", _clean_prompt(prompt),
        "--image", str(image),
        "--aspect_ratio", aspect_ratio,
        "--duration", str(duration),
        "--quality", quality,
        "--model", model_variant,
    ]

    if extra:
        args.extend(extra)

    return _run_cli(args)


# ---------------------------------------------------------------------------
# Marketing Studio Video
# ---------------------------------------------------------------------------

def run_marketing_studio_video(
    prompt: str,
    avatar_uuid: str = None,
    product_uuid: str = None,
    medias: list = None,
    mode: str = "ugc",
    aspect_ratio: str = "9:16",
    duration: int = 8,
    resolution: str = "1080p",
    generate_audio: bool = True,
) -> dict:
    """
    Submit a Marketing Studio Video job. Returns the job dict.

    Call shape locked via Phase 3.1 smoke tests:
      --avatars     '[{"id":"<avatar_uuid>","type":"custom"}]'
      --product_ids '["<product_uuid>"]'
      --medias      '[{"role":"image","data":{"type":"media_input","id":"<upload_uuid>"}}]'
      --mode        one of: ugc, ugc_how_to, ugc_unboxing, product_review, ugc_virtual_try_on
                            (plus product_showcase, tv_spot, wild_card, virtual_try_on)
      --prompt      composed brief (Higgsfield enhances server-side)

    Audio defaults ON. Brief is enhanced server-side into a screenplay-style prompt,
    so callers should pass a minimal scene-description (3-slot brief works well).

    medias is a list of upload UUIDs to include as additional image references —
    used for outfit/body identity reinforcement when the avatar was built from
    a single image (typical case: pass the character's fullbody.png upload UUID).
    """
    args = [
        "generate", "create", "marketing_studio_video",
        "--prompt", _clean_prompt(prompt),
        "--mode", mode,
        "--aspect_ratio", aspect_ratio,
        "--duration", str(duration),
        "--resolution", resolution,
        "--generate_audio", "true" if generate_audio else "false",
    ]

    if avatar_uuid:
        args.extend([
            "--avatars",
            json.dumps([{"id": avatar_uuid, "type": "custom"}]),
        ])

    if product_uuid:
        args.extend([
            "--product_ids",
            json.dumps([product_uuid]),
        ])

    if medias:
        media_objs = [
            {"role": "image", "data": {"type": "media_input", "id": m}}
            for m in medias
        ]
        args.extend(["--medias", json.dumps(media_objs)])

    return _run_cli(args)


# ---------------------------------------------------------------------------
# Marketing Studio Video — orphan-resistant submit + poll path
# ---------------------------------------------------------------------------
# The `--wait` path above blocks for the whole render. If Higgsfield's gateway
# returns a transient 5xx (e.g. 502) mid-wait, the local call fails even though
# the job completed server-side — and marketing_studio_video jobs can't be found
# via `generate list`, so the result orphans and a re-run double-generates.
#
# These functions split submit (returns the job id immediately) from polling
# (`generate get <id>`, retried on transient errors). The caller persists the id
# the moment it's created, so any failure is recoverable by id instead of by a
# duplicate generation.

def _build_msv_args(prompt, avatar_uuid, product_uuid, medias, mode,
                    aspect_ratio, duration, resolution, generate_audio) -> list:
    """Build the `generate create marketing_studio_video` arg list (no --wait/--json)."""
    args = [
        "generate", "create", "marketing_studio_video",
        "--prompt", _clean_prompt(prompt),
        "--mode", mode,
        "--aspect_ratio", aspect_ratio,
        "--duration", str(duration),
        "--resolution", resolution,
        "--generate_audio", "true" if generate_audio else "false",
    ]
    if avatar_uuid:
        args.extend(["--avatars", json.dumps([{"id": avatar_uuid, "type": "custom"}])])
    if product_uuid:
        args.extend(["--product_ids", json.dumps([product_uuid])])
    if medias:
        media_objs = [
            {"role": "image", "data": {"type": "media_input", "id": m}}
            for m in medias
        ]
        args.extend(["--medias", json.dumps(media_objs)])
    return args


def submit_marketing_studio_video(
    prompt: str,
    avatar_uuid: str = None,
    product_uuid: str = None,
    medias: list = None,
    mode: str = "ugc",
    aspect_ratio: str = "9:16",
    duration: int = 8,
    resolution: str = "1080p",
    generate_audio: bool = True,
) -> dict:
    """
    Submit a Marketing Studio Video job WITHOUT --wait. Returns the created job
    dict (contains 'id' and an initial 'status') immediately, so the caller can
    persist the id and poll. The long wait happens in poll_job(), where a
    transient error re-polls by id instead of re-submitting (no duplicate).
    """
    args = _build_msv_args(prompt, avatar_uuid, product_uuid, medias, mode,
                           aspect_ratio, duration, resolution, generate_audio)
    result = subprocess.run([HIGGSFIELD_BIN,*args, "--json"], capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout or "marketing_studio_video submit failed\n")
        sys.exit(1)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as err:
        sys.exit(f"Could not parse submit JSON: {err}\nOutput: {result.stdout[:500]}")
    if not isinstance(payload, list) or not payload:
        sys.exit(f"Unexpected submit response shape: {result.stdout[:500]}")
    item = payload[0]
    # Some CLI versions return a bare job-id string instead of a full job dict.
    if isinstance(item, str):
        return {"id": item, "status": "pending"}
    return item


def get_job(job_id: str):
    """
    Fetch a single job by id via `generate get <id> --json`.

    Returns the job dict on success, or None on a transient error (nonzero exit
    or unparseable output) so the caller can retry — we already hold the id, so
    retrying never causes a duplicate generation.
    """
    result = subprocess.run(
        [HIGGSFIELD_BIN, "generate", "get", job_id, "--json"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    job = payload[0] if isinstance(payload, list) and payload else payload
    return job if isinstance(job, dict) else None


# Statuses that mean "stop polling".
TERMINAL_STATUSES = {"completed", "failed", "nsfw", "canceled", "cancelled"}


def poll_job(job_id: str, interval: int = 15, timeout_min: int = 30) -> dict:
    """
    Poll `generate get <id>` until the job reaches a terminal status, then return it.

    Transient errors (get_job returns None — e.g. a 502 gateway blip) are retried;
    re-polling by id never causes a duplicate. On timeout, exits with a recovery
    hint (the id stays valid for later `generate get`).
    """
    waited = 0
    while waited < timeout_min * 60:
        job = get_job(job_id)
        if job is not None and job.get("status") in TERMINAL_STATUSES:
            return job
        time.sleep(interval)
        waited += interval
    sys.exit(
        f"Timed out after {timeout_min}m polling job {job_id}. It may still be running — "
        f"recover later with: higgsfield generate get {job_id} --json"
    )


# ---------------------------------------------------------------------------
# Product Photoshoot (prompt-enhanced image modes)
# ---------------------------------------------------------------------------

import re

# Filename format: hf_<YYYYMMDD>_<HHMMSS>_<uuid>.png (two timestamp segments before the UUID)
_PHOTOSHOOT_FILENAME_UUID_RE = re.compile(r"hf_\d+_\d+_([0-9a-f-]{36})\.png", re.IGNORECASE)


def _extract_uuid_from_photoshoot_url(url: str) -> str:
    """Pull the job UUID out of a product-photoshoot result URL.

    product-photoshoot's response shape is `{"failed": [...], "urls": [...]}`
    with NO job-id field — unlike every other Higgsfield endpoint. The job
    UUID is embedded in the result PNG's filename as `hf_<unix-ts>_<uuid>.png`,
    which we parse out so downstream sidecars can still record a stable UUID.

    Returns the extracted UUID string, or empty string if the URL doesn't match.
    """
    if not url:
        return ""
    match = _PHOTOSHOOT_FILENAME_UUID_RE.search(url)
    return match.group(1) if match else ""


def run_product_photoshoot(
    mode: str,
    prompt: str,
    images: list,
    aspect_ratio: str,
    brand_context: str = "",
    product_context: str = "",
) -> dict:
    """
    Submit a `higgsfield product-photoshoot create` job. Returns a status dict.

    The product-photoshoot endpoint is a two-stage internal pipeline (enhancer +
    gpt_image_2 @ 2k). Its response shape differs from every other Higgsfield
    endpoint — `{"failed": [...], "urls": [...]}` instead of an array of job
    objects — so this helper does its own JSON parsing instead of going through
    `_run_cli`.

    Return shape:
      {"status": "completed", "url": <first-url>, "job_uuid": <extracted-uuid>}
        — happy path. job_uuid is parsed from the filename `hf_<ts>_<uuid>.png`
          so callers can write a 2-line .uuid sidecar via `save_job_uuid`.
      {"status": "nsfw", "url": None, "job_uuid": None}
        — backend NSFW classifier rejected the job. Caller (skill, not script)
          handles the auto-sanitize-and-retry path. Credits are still consumed
          server-side on nsfw, so retries should be deliberate.
      Anything else (HTTP error, malformed response, generic failure) → exits
      with a clear stderr message, matching `_run_cli`'s behavior.

    `images` is a list of **FILE PATHS** passed as `--image <path>` one per
    item in order. **Note**: product-photoshoot does NOT accept upload UUIDs as
    `--image` despite the CLI help text saying it should — passing a UUID
    returns "Not Found". This is undocumented CLI behavior. The CLI does its
    own internal upload when given a file path. Callers should pass paths.

    `aspect_ratio` is required by the skill's locked rules — always pass explicit.
    Mode defaults of 4:5 are invalid input values on this endpoint, so this
    helper also runs `remap_aspect()` defensively.
    """
    if not images:
        sys.exit("run_product_photoshoot: at least one --image is required")

    args = [
        "product-photoshoot", "create",
        "--mode", mode,
        "--aspect_ratio", remap_aspect(aspect_ratio),
        "--prompt", _clean_prompt(prompt),
        "--timeout", "15m",
        "--json",
    ]
    _warn_if_too_many_refs(images)
    for ref in images:
        args.extend(["--image", str(ref)])
    if brand_context:
        args.extend(["--brand_context", _clean_prompt(brand_context)])
    if product_context:
        args.extend(["--product_context", _clean_prompt(product_context)])

    result = subprocess.run([HIGGSFIELD_BIN,*args], capture_output=True, text=True, encoding="utf-8")

    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout or "higgsfield CLI failed\n")
        sys.exit(1)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as err:
        sys.exit(f"Could not parse product-photoshoot JSON: {err}\nOutput: {result.stdout[:500]}")

    if not isinstance(payload, dict):
        sys.exit(f"Unexpected product-photoshoot response shape (expected object): {result.stdout[:500]}")

    failed = payload.get("failed") or []
    urls = payload.get("urls") or []

    # NSFW detection: failed entries are strings like "<uuid>: job ended with status \"nsfw\"".
    if failed and any("nsfw" in str(entry).lower() for entry in failed):
        return {"status": "nsfw", "url": None, "job_uuid": None}

    # Other failure modes that aren't NSFW.
    if failed and not urls:
        sys.exit(f"product-photoshoot failed: {failed[0]}")

    if not urls:
        sys.exit(f"product-photoshoot returned no URLs: {result.stdout[:500]}")

    first_url = urls[0]
    return {
        "status": "completed",
        "url": first_url,
        "job_uuid": _extract_uuid_from_photoshoot_url(first_url),
    }


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download(url: str, dest: Path, timeout: int = 300) -> None:
    """Download a result asset to disk."""
    with requests.get(url, timeout=timeout, stream=True) as response:
        response.raise_for_status()
        dest.write_bytes(response.content)

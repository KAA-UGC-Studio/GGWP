"""
_kie.py — shared helpers for kie.ai image & video generation.

Parallel to `_higgsfield.py`, but kie.ai has NO CLI: it's a REST API using a
Bearer key and an async submit-then-poll flow. All kie.ai scripts import these
functions so auth, task polling, error surfacing, and result download live in
one place.

Auth: set `KIE_API_KEY` (env var) OR put `KIE_API_KEY=...` in the project-root
`.env` file. Get a key at https://kie.ai/api-key.

API surface (https://api.kie.ai):
  GET  /api/v1/chat/credit            → remaining credits (data: int)
  POST /api/v1/jobs/createTask        → {model, input:{...}} → data.taskId
  GET  /api/v1/jobs/recordInfo?taskId → data.state + data.resultJson
"""

import base64
import json
import mimetypes
import os
import sys
import time
from pathlib import Path

import requests

BASE_URL = "https://api.kie.ai"
CREATE_TASK = f"{BASE_URL}/api/v1/jobs/createTask"
RECORD_INFO = f"{BASE_URL}/api/v1/jobs/recordInfo"
CREDIT = f"{BASE_URL}/api/v1/chat/credit"

# Veo 3.1 video has its own submit/poll endpoints (separate from the unified jobs
# API). The /veo/generate endpoint serves Veo 3.1: model "veo3" = Veo 3.1 Quality,
# "veo3_fast" = Veo 3.1 Fast.
VEO_GENERATE = f"{BASE_URL}/api/v1/veo/generate"
VEO_RECORD = f"{BASE_URL}/api/v1/veo/record-info"

# File upload lives on a separate host (kie.ai's temp CDN). Uploaded files are
# public and auto-expire after ~3 days, so we cache the URL with a freshness TTL.
FILE_UPLOAD_BASE64 = "https://kieai.redpandaai.co/api/file-base64-upload"
_UPLOAD_TTL_SECONDS = 2 * 24 * 3600  # re-upload if the cached URL is older than 2 days

# Terminal states returned by recordInfo's data.state.
_TERMINAL = {"success", "fail"}


# ---------------------------------------------------------------------------
# Auth / config
# ---------------------------------------------------------------------------

def _project_root() -> Path:
    """Project root = parent of this scripts/ directory."""
    return Path(__file__).resolve().parent.parent


def _load_dotenv_value(key: str) -> str:
    """Minimal .env reader — returns the value for `key`, or '' if absent.

    Avoids a python-dotenv dependency (requirements.txt only pins `requests`).
    Parses simple `KEY=VALUE` lines, ignoring blanks, comments, and optional
    surrounding quotes. Environment variables always take precedence.
    """
    env_path = _project_root() / ".env"
    if not env_path.exists():
        return ""
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def get_api_key() -> str:
    """Return the kie.ai API key, or exit with guidance.

    The project `.env` is the source of truth and takes precedence over any
    machine-level `KIE_API_KEY` environment variable (a stale env var otherwise
    silently shadows the key saved in the project).
    """
    key = _load_dotenv_value("KIE_API_KEY") or os.environ.get("KIE_API_KEY", "").strip()
    if not key:
        sys.exit(
            "KIE_API_KEY not set.\n"
            "  1. Get a key at https://kie.ai/api-key\n"
            "  2. Add it to the project-root .env file:  KIE_API_KEY=your_key_here\n"
            "     (or set it as an environment variable)"
        )
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# File upload (local file → public URL)
# ---------------------------------------------------------------------------

def upload_file(path: str, upload_path: str = "images/pynk") -> str:
    """
    Upload a local file to kie.ai's temp storage and return its public URL.

    Nano Banana Pro (and other image-to-image models) require reference images
    as publicly reachable URLs — they cannot take raw bytes. This base64-uploads
    the file and returns `data.downloadUrl`.

    Result is cached in a `<path>.kie.url` sidecar (url, mtime, upload_epoch).
    The cache is reused only if the file is unchanged AND the upload is younger
    than the ~3-day server expiry (we use a 2-day TTL for safety).
    """
    p = Path(path)
    if not p.exists():
        sys.exit(f"upload_file: file not found: {path}")

    sidecar = Path(str(p) + ".kie.url")
    current_mtime = p.stat().st_mtime
    cached = _read_url_sidecar(sidecar)
    if cached:
        url, mtime, uploaded_at = cached
        if mtime == current_mtime and (time.time() - uploaded_at) < _UPLOAD_TTL_SECONDS:
            return url

    print(f"  uploading to kie.ai: {p.name}")
    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    payload = {
        "base64Data": f"data:{mime};base64,{b64}",
        "uploadPath": upload_path,
        "fileName": p.name,
    }
    try:
        resp = requests.post(FILE_UPLOAD_BASE64, headers=_headers(), json=payload, timeout=180)
    except requests.RequestException as err:
        sys.exit(f"kie.ai file upload failed (network): {err}")

    if resp.status_code == 401:
        sys.exit("kie.ai auth failed (401) on upload — check KIE_API_KEY.")
    if resp.status_code != 200:
        sys.exit(f"kie.ai file upload HTTP {resp.status_code}: {resp.text[:400]}")

    body = resp.json()
    if not body.get("success") and body.get("code") != 200:
        sys.exit(f"kie.ai file upload error: {body.get('msg')}")

    url = (body.get("data") or {}).get("downloadUrl")
    if not url:
        sys.exit(f"kie.ai file upload returned no downloadUrl: {resp.text[:400]}")

    _write_url_sidecar(sidecar, url, current_mtime, time.time())
    return url


def _read_url_sidecar(sidecar: Path):
    """Return (url, mtime, upload_epoch) from a .kie.url sidecar, or None."""
    if not sidecar.exists():
        return None
    try:
        lines = sidecar.read_text(encoding="utf-8").strip().split("\n")
        if len(lines) >= 3:
            return (lines[0].strip(), float(lines[1].strip()), float(lines[2].strip()))
    except (OSError, ValueError):
        pass
    return None


def _write_url_sidecar(sidecar: Path, url: str, mtime: float, uploaded_at: float) -> None:
    sidecar.write_text(f"{url}\n{mtime}\n{uploaded_at}\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Credits
# ---------------------------------------------------------------------------

def get_credit() -> int:
    """Return remaining kie.ai credits (int). Exits on auth/transport error."""
    try:
        resp = requests.get(CREDIT, headers=_headers(), timeout=30)
    except requests.RequestException as err:
        sys.exit(f"kie.ai credit check failed (network): {err}")

    if resp.status_code == 401:
        sys.exit("kie.ai auth failed (401) — check KIE_API_KEY is valid.")
    if resp.status_code != 200:
        sys.exit(f"kie.ai credit check HTTP {resp.status_code}: {resp.text[:300]}")

    body = resp.json()
    if body.get("code") != 200:
        sys.exit(f"kie.ai credit check error: {body.get('msg')}")
    return int(body.get("data") or 0)


# ---------------------------------------------------------------------------
# Task submit + poll
# ---------------------------------------------------------------------------

def create_task(model: str, task_input: dict) -> str:
    """
    Submit a generation task. Returns the taskId.

    `model` is a kie.ai model slug (e.g. "google/nano-banana" for image,
    "google/veo3-fast" for video). `task_input` is the model's `input` object
    (prompt, image_urls, aspect_ratio, etc. — model-specific).
    """
    payload = {"model": model, "input": task_input}
    try:
        resp = requests.post(CREATE_TASK, headers=_headers(), json=payload, timeout=60)
    except requests.RequestException as err:
        sys.exit(f"kie.ai createTask failed (network): {err}")

    if resp.status_code == 401:
        sys.exit("kie.ai auth failed (401) — check KIE_API_KEY is valid.")
    if resp.status_code == 402:
        sys.exit("kie.ai reports insufficient credits (402). Top up at https://kie.ai/pricing")
    if resp.status_code != 200:
        sys.exit(f"kie.ai createTask HTTP {resp.status_code}: {resp.text[:400]}")

    body = resp.json()
    if body.get("code") != 200:
        sys.exit(f"kie.ai createTask error (code {body.get('code')}): {body.get('msg')}")

    task_id = (body.get("data") or {}).get("taskId")
    if not task_id:
        sys.exit(f"kie.ai createTask returned no taskId: {resp.text[:400]}")
    return task_id


def poll_task(task_id: str, interval: int = 6, timeout_min: int = 20) -> list:
    """
    Poll recordInfo until the task reaches a terminal state. Returns the list of
    result URLs on success; exits with failMsg on failure or on timeout.

    Transient network errors are retried (we hold the taskId, so re-polling is
    always safe and never double-charges).
    """
    waited = 0
    while waited < timeout_min * 60:
        try:
            resp = requests.get(
                RECORD_INFO, headers=_headers(),
                params={"taskId": task_id}, timeout=30,
            )
        except requests.RequestException:
            time.sleep(interval)
            waited += interval
            continue

        if resp.status_code == 200:
            data = (resp.json() or {}).get("data") or {}
            state = data.get("state")
            if state == "success":
                return _extract_result_urls(data)
            if state == "fail":
                sys.exit(
                    f"kie.ai task {task_id} failed: "
                    f"{data.get('failMsg') or data.get('failCode') or 'unknown error'}"
                )
            # waiting / queuing / generating → keep polling

        time.sleep(interval)
        waited += interval

    sys.exit(
        f"Timed out after {timeout_min}m polling kie.ai task {task_id}. "
        f"It may still be running — check https://kie.ai/logs"
    )


def _extract_result_urls(data: dict) -> list:
    """Pull result URLs out of recordInfo's data.resultJson (a JSON string)."""
    raw = data.get("resultJson")
    if not raw:
        return []
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        return []
    return parsed.get("resultUrls") or []


# ---------------------------------------------------------------------------
# High-level generation
# ---------------------------------------------------------------------------

def generate_image(
    prompt: str,
    model: str = "google/nano-banana",
    image_urls: list = None,
    aspect_ratio: str = None,
    extra_input: dict = None,
    timeout_min: int = 20,
) -> list:
    """
    Generate image(s). Returns a list of result image URLs.

    `image_urls` — optional reference images (for edit / image-to-image models).
    `extra_input` — any model-specific input fields to merge in.
    """
    task_input = {"prompt": prompt}
    if image_urls:
        task_input["image_urls"] = image_urls
    if aspect_ratio:
        task_input["aspect_ratio"] = aspect_ratio
    if extra_input:
        task_input.update(extra_input)
    task_id = create_task(model, task_input)
    return poll_task(task_id, timeout_min=timeout_min)


def generate_video(
    prompt: str,
    model: str = "google/veo3-fast",
    image_urls: list = None,
    aspect_ratio: str = "9:16",
    extra_input: dict = None,
    timeout_min: int = 30,
) -> list:
    """
    Generate a video. Returns a list of result video URLs.

    `image_urls` — optional first-frame / reference image for image-to-video.
    Video renders are slower, so the default poll timeout is higher.
    """
    task_input = {"prompt": prompt, "aspect_ratio": aspect_ratio}
    if image_urls:
        task_input["image_urls"] = image_urls
    if extra_input:
        task_input.update(extra_input)
    task_id = create_task(model, task_input)
    return poll_task(task_id, timeout_min=timeout_min)


# ---------------------------------------------------------------------------
# Veo 3.1 video (dedicated endpoint)
# ---------------------------------------------------------------------------

def generate_veo_video(
    prompt: str,
    image_urls: list = None,
    model: str = "veo3_fast",
    aspect_ratio: str = "9:16",
    duration: int = 8,
    resolution: str = "1080p",
    timeout_min: int = 30,
) -> list:
    """
    Generate a Veo 3.1 video. Returns a list of result video URLs.

    model: "veo3_fast" (Veo 3.1 Fast) or "veo3" (Veo 3.1 Quality).
    image_urls: 1 image → the video unfolds around it (image-to-video);
                omit for pure text-to-video.
    """
    task_id = _veo_submit(prompt, image_urls, model, aspect_ratio, duration, resolution)
    return _veo_poll(task_id, timeout_min=timeout_min)


def _veo_submit(prompt, image_urls, model, aspect_ratio, duration, resolution) -> str:
    payload = {
        "prompt": prompt,
        "model": model,
        "aspect_ratio": aspect_ratio,
        "duration": duration,
        "resolution": resolution,
    }
    if image_urls:
        payload["imageUrls"] = image_urls
    try:
        resp = requests.post(VEO_GENERATE, headers=_headers(), json=payload, timeout=60)
    except requests.RequestException as err:
        sys.exit(f"kie.ai veo generate failed (network): {err}")

    if resp.status_code == 401:
        sys.exit("kie.ai auth failed (401) — check KIE_API_KEY.")
    if resp.status_code == 402:
        sys.exit("kie.ai reports insufficient credits (402). Top up at https://kie.ai/pricing")
    if resp.status_code != 200:
        sys.exit(f"kie.ai veo generate HTTP {resp.status_code}: {resp.text[:400]}")

    body = resp.json()
    if body.get("code") != 200:
        sys.exit(f"kie.ai veo generate error (code {body.get('code')}): {body.get('msg')}")

    task_id = (body.get("data") or {}).get("taskId")
    if not task_id:
        sys.exit(f"kie.ai veo generate returned no taskId: {resp.text[:400]}")
    return task_id


def _veo_poll(task_id: str, interval: int = 10, timeout_min: int = 30) -> list:
    """Poll /veo/record-info until successFlag is terminal. Returns result URLs."""
    waited = 0
    while waited < timeout_min * 60:
        try:
            resp = requests.get(
                VEO_RECORD, headers=_headers(),
                params={"taskId": task_id}, timeout=30,
            )
        except requests.RequestException:
            time.sleep(interval)
            waited += interval
            continue

        if resp.status_code == 200:
            data = (resp.json() or {}).get("data") or {}
            flag = data.get("successFlag")
            if flag == 1:
                response = data.get("response") or {}
                return response.get("resultUrls") or response.get("fullResultUrls") or []
            if flag in (2, 3):
                sys.exit(
                    f"kie.ai veo task {task_id} failed: "
                    f"{data.get('errorMessage') or data.get('errorCode') or 'unknown error'}"
                )
            # flag 0 (or None) → still generating

        time.sleep(interval)
        waited += interval

    sys.exit(
        f"Timed out after {timeout_min}m polling kie.ai veo task {task_id}. "
        f"Check https://kie.ai/logs"
    )


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download(url: str, dest: Path, timeout: int = 300) -> None:
    """Download a result asset to disk."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, timeout=timeout, stream=True) as response:
        response.raise_for_status()
        dest.write_bytes(response.content)

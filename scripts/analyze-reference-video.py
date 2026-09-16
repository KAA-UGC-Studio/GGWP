#!/usr/bin/env python3
"""
analyze-reference-video.py — watch a reference video so /ugc-clone can read it.

A language model cannot play a video. This script turns one into things it can
read: keyframes, a shot list derived from real scene cuts, and a timestamped
transcript. Everything lands in a brand-agnostic cache so a second clone of the
same reference (different brand or product) skips the work.

Usage (run from project root):
  python scripts/analyze-reference-video.py "Referensi/Video Referensi/Skin100.mp4"
  python scripts/analyze-reference-video.py "https://www.tiktok.com/@user/video/123" --slug hook-tutorial
  python scripts/analyze-reference-video.py ref.mp4 --segment 0:12-0:30
  python scripts/analyze-reference-video.py ref.mp4 --force --no-transcribe

Output → Referensi/Video Referensi/_analysis/<slug>/
  source.mp4        the reference (downloaded or copied)
  frames/           JPEG keyframes, named <index>_<timestamp>s.jpg
  transcript.txt    timestamped lines, plus transcript.json
  metadata.json     duration, aspect, fps, scene cuts, frame index, transcript

Requires ffmpeg/ffprobe on PATH, plus yt-dlp (URLs) and faster-whisper
(transcription) from requirements.txt.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

CACHE_ROOT = Path("Referensi/Video Referensi/_analysis")

# Scene-change score above which ffmpeg's `select` filter calls it a cut. 0.3 is
# the usual starting point: lower floods a jump-cut UGC clip with false cuts,
# higher misses cuts between similar-looking shots.
SCENE_THRESHOLD = 0.3

# A model reads every frame we extract, so this caps how much it has to look at.
DEFAULT_MAX_FRAMES = 80


# ---------------------------------------------------------------------------
# Shell helpers
# ---------------------------------------------------------------------------

def _run(args: list, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", **kwargs)


def _require(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        sys.exit(f"{tool} not found on PATH. See requirements.txt / install {tool} first.")
    return path


def _parse_timecode(value: str) -> float:
    """Accept 12, 12.5, 1:05 or 1:02:03 and return seconds."""
    parts = str(value).strip().split(":")
    try:
        numbers = [float(p) for p in parts]
    except ValueError:
        sys.exit(f"Could not read timecode: {value}")
    seconds = 0.0
    for number in numbers:
        seconds = seconds * 60 + number
    return seconds


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return slug or "reference"


# ---------------------------------------------------------------------------
# Input resolution
# ---------------------------------------------------------------------------

def resolve_source(source: str, out_dir: Path) -> Path:
    """Download (URL) or copy (local path) the reference into the cache folder."""
    dest = out_dir / "source.mp4"
    if dest.exists():
        print(f"  source already cached: {dest}")
        return dest

    if re.match(r"^https?://", source, re.IGNORECASE):
        _require("yt-dlp")
        print(f"  downloading: {source}")
        result = _run([
            "yt-dlp",
            "-f", "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
            "--merge-output-format", "mp4",
            "-o", str(dest),
            source,
        ])
        if result.returncode != 0 or not dest.exists():
            sys.exit(f"yt-dlp failed:\n{result.stderr or result.stdout}")
        return dest

    src_path = Path(source)
    if not src_path.exists():
        sys.exit(f"Reference not found: {src_path}")
    shutil.copy2(src_path, dest)
    print(f"  copied: {src_path.name}")
    return dest


# ---------------------------------------------------------------------------
# Probing
# ---------------------------------------------------------------------------

def probe(video: Path) -> dict:
    _require("ffprobe")
    result = _run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-show_entries", "stream=codec_type,width,height,r_frame_rate",
        "-of", "json", str(video),
    ])
    if result.returncode != 0:
        sys.exit(f"ffprobe failed:\n{result.stderr}")

    data = json.loads(result.stdout)
    info = {"duration": float(data.get("format", {}).get("duration") or 0.0),
            "width": None, "height": None, "fps": None, "has_audio": False}

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and info["width"] is None:
            info["width"] = stream.get("width")
            info["height"] = stream.get("height")
            rate = stream.get("r_frame_rate") or "0/1"
            try:
                num, den = rate.split("/")
                info["fps"] = round(float(num) / float(den), 3) if float(den) else None
            except (ValueError, ZeroDivisionError):
                info["fps"] = None
        elif stream.get("codec_type") == "audio":
            info["has_audio"] = True

    if info["width"] and info["height"]:
        info["aspect"] = _aspect_label(info["width"], info["height"])
    return info


def _aspect_label(width: int, height: int) -> str:
    """Nearest common social aspect ratio, so the prompt can state one."""
    ratio = width / height
    known = {"9:16": 9 / 16, "3:4": 3 / 4, "1:1": 1.0, "4:5": 4 / 5,
             "4:3": 4 / 3, "16:9": 16 / 9, "21:9": 21 / 9}
    return min(known, key=lambda k: abs(known[k] - ratio))


# ---------------------------------------------------------------------------
# Scene cuts + frames
# ---------------------------------------------------------------------------

def detect_cuts(video: Path, start: float, end: float) -> list:
    """Return the timestamps (seconds) where ffmpeg sees a scene change."""
    _require("ffmpeg")
    args = ["ffmpeg", "-hide_banner"]
    if start:
        args += ["-ss", str(start)]
    args += ["-i", str(video)]
    if end:
        args += ["-t", str(end - start)]
    args += ["-filter:v", f"select='gt(scene,{SCENE_THRESHOLD})',showinfo",
             "-f", "null", "-"]

    result = _run(args)
    cuts = [round(start + float(m), 3)
            for m in re.findall(r"pts_time:([0-9.]+)", result.stderr or "")]
    return sorted(set(cuts))


def plan_timestamps(start: float, end: float, cuts: list, fps: float, max_frames: int) -> list:
    """Cut frames first, then an even grid, thinned evenly to the cap.

    Cut frames are what a shot list is built from, so they survive thinning;
    the grid frames only fill in what happens inside a long shot.
    """
    cut_frames = [round(c + 0.08, 3) for c in cuts if start <= c <= end]

    grid, step, t = [], 1.0 / fps if fps > 0 else 1.0, start
    while t < end:
        grid.append(round(t, 3))
        t += step

    def _thin(values: list, limit: int) -> list:
        if limit <= 0 or len(values) <= limit:
            return values
        stride = len(values) / limit
        return [values[int(i * stride)] for i in range(limit)]

    cut_frames = _thin(cut_frames, max_frames)
    remaining = max_frames - len(cut_frames)
    grid = [g for g in grid if all(abs(g - c) > 0.35 for c in cut_frames)]
    grid = _thin(grid, remaining)

    return sorted(set(cut_frames + grid))


def extract_frames(video: Path, timestamps: list, frames_dir: Path) -> list:
    _require("ffmpeg")
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)

    written = []
    for index, timestamp in enumerate(timestamps, start=1):
        name = f"{index:03d}_{timestamp:07.2f}s.jpg"
        out_path = frames_dir / name
        result = _run([
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-ss", str(timestamp), "-i", str(video),
            "-frames:v", "1", "-q:v", "3", "-y", str(out_path),
        ])
        if result.returncode == 0 and out_path.exists():
            written.append({"file": name, "t": timestamp})
    print(f"  frames: {len(written)} written → {frames_dir}")
    return written


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def transcribe(video: Path, out_dir: Path, model_name: str, start: float, end: float) -> dict:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("  faster-whisper not installed — skipping transcript "
              "(pip install faster-whisper)")
        return {}

    _require("ffmpeg")
    audio_path = out_dir / "audio.wav"
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if start:
        args += ["-ss", str(start)]
    args += ["-i", str(video)]
    if end:
        args += ["-t", str(end - start)]
    args += ["-vn", "-ac", "1", "-ar", "16000", "-y", str(audio_path)]

    if _run(args).returncode != 0 or not audio_path.exists():
        print("  no audio track — skipping transcript")
        return {}

    print(f"  transcribing with faster-whisper ({model_name}) …")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(audio_path), vad_filter=True)

    lines = []
    for segment in segments:
        lines.append({
            "start": round(start + segment.start, 2),
            "end": round(start + segment.end, 2),
            "text": segment.text.strip(),
            # Whisper's own confidence. /ugc-clone flags low-confidence lines
            # with ❓ at Gate 1 instead of quietly trusting them.
            "logprob": round(getattr(segment, "avg_logprob", 0.0), 3),
        })

    audio_path.unlink(missing_ok=True)

    transcript = {
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "segments": lines,
    }
    (out_dir / "transcript.json").write_text(
        json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "transcript.txt").write_text(
        "\n".join(f"[{l['start']:6.2f} - {l['end']:6.2f}] {l['text']}" for l in lines)
        or "(no speech detected)", encoding="utf-8")
    print(f"  transcript: {len(lines)} segments, language={info.language} "
          f"({transcript['language_probability']})")
    return transcript


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract keyframes, scene cuts and a transcript from a reference video.")
    parser.add_argument("source", help="Local path or URL (TikTok / IG / YouTube).")
    parser.add_argument("--slug", help="Cache folder name. Default: the file/video name.")
    parser.add_argument("--segment", help="Clone only part of it, e.g. 0:12-0:30.")
    parser.add_argument("--fps", type=float, default=1.0,
                        help="Grid frames per second (default 1).")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES,
                        help=f"Frame cap (default {DEFAULT_MAX_FRAMES}).")
    parser.add_argument("--whisper-model", default="small",
                        help="faster-whisper model size (default small).")
    parser.add_argument("--no-transcribe", action="store_true", help="Skip the transcript.")
    parser.add_argument("--force", action="store_true", help="Redo even if cached.")
    args = parser.parse_args()

    slug = _slugify(args.slug or Path(args.source).stem)
    out_dir = CACHE_ROOT / slug
    metadata_path = out_dir / "metadata.json"

    if metadata_path.exists() and not args.force:
        cached = json.loads(metadata_path.read_text(encoding="utf-8"))
        print(f"\nCached analysis → {out_dir}  (--force to redo)")
        _print_summary(cached, out_dir)
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nAnalyzing reference → {out_dir}")

    video = resolve_source(args.source, out_dir)
    info = probe(video)

    start, end = 0.0, info["duration"]
    if args.segment:
        if "-" not in args.segment:
            sys.exit("--segment needs a range, e.g. 0:12-0:30")
        raw_start, raw_end = args.segment.split("-", 1)
        start, end = _parse_timecode(raw_start), _parse_timecode(raw_end)
        if end <= start or end > info["duration"] + 0.5:
            sys.exit(f"--segment outside the video (duration {info['duration']:.2f}s)")

    if (end - start) > 60:
        print(f"  ⚠️  {end - start:.0f}s is long for a clone reference — consider "
              f"--segment to pick one part.")

    cuts = detect_cuts(video, start, end)
    print(f"  scene cuts: {len(cuts)}"
          + (f" at {', '.join(f'{c:.2f}s' for c in cuts[:12])}" if cuts else " (single take)"))

    timestamps = plan_timestamps(start, end, cuts, args.fps, args.max_frames)
    frames = extract_frames(video, timestamps, out_dir / "frames")

    transcript = {} if args.no_transcribe else transcribe(
        video, out_dir, args.whisper_model, start, end)

    metadata = {
        "slug": slug,
        "source": args.source,
        "segment": {"start": start, "end": end},
        "video": info,
        "scene_cuts": cuts,
        "frames": frames,
        "transcript": transcript,
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    _print_summary(metadata, out_dir)


def _print_summary(metadata: dict, out_dir: Path) -> None:
    info = metadata.get("video", {})
    segment = metadata.get("segment", {})
    print("\n─── ANALYSIS READY ───\n")
    print(f"  Duration:   {info.get('duration', 0):.2f}s "
          f"(analyzed {segment.get('start', 0):.2f}–{segment.get('end', 0):.2f}s)")
    print(f"  Format:     {info.get('width')}x{info.get('height')} "
          f"({info.get('aspect')}) @ {info.get('fps')}fps")
    print(f"  Audio:      {'yes' if info.get('has_audio') else 'no'}")
    print(f"  Scene cuts: {len(metadata.get('scene_cuts', []))}")
    print(f"  Frames:     {len(metadata.get('frames', []))} in {out_dir / 'frames'}")
    transcript = metadata.get("transcript") or {}
    if transcript:
        print(f"  Transcript: {len(transcript.get('segments', []))} segments "
              f"({transcript.get('language')}) in {out_dir / 'transcript.txt'}")
    print(f"\n  Next: read the frames in order, then write the Gate-1 breakdown.\n")


if __name__ == "__main__":
    main()

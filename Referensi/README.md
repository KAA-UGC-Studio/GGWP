# Referensi/ — reference material

Source material the skills draw on. Not generated output — this is the input library.

## `Karakter Template/`

Casting references: one folder per character archetype (ANDI, BILQIS, PAK FIRMAN, RETNO, …),
each holding face and body reference photos.

`/character-creator` uses these as the reference photo when you build a brand character from a
template instead of from scratch. Pick the archetype that fits the brand's audience — the
skill locks the face to that reference so every later shot of that character matches.

## `Other Insight/`

Photography and cinematography cheat sheets (PDF):

- `ANGLE CHEAT SHEET.pdf`
- `FRAMING _ DISTANCE CHEAT SHEET.pdf`
- `PHOTOGRAPHY LIGHTING CHEAT SHEET.pdf`
- `PROFESSIONAL POSING.pdf`
- `VIDEO MOVEMENT CHEAT SHEET.pdf`

These are the vocabulary behind the prompts — the terms in `docs/ai-tools-knowledge.md`
("Universal prompt craft") come from here. Read them when a generation keeps coming out flat:
the fix is usually a more specific angle, lens distance, or light direction, not a longer prompt.

## `Video Referensi/`

**Ships empty — you fill it.** Drop reference videos here (or let `/ugc-clone` download one from
a TikTok / Instagram / YouTube URL), then run:

```
/ugc-clone
```

It watches the video — scene cuts, camera movement, dialogue, pacing — recommends a video model,
and writes prompts in English and Indonesian adapted to your brand and product. It never
generates; you take the prompts to `/ugc-content-kie` or `/ugc-content`.

Analysis output is cached under `_analysis/<slug>/` (extracted frames, transcript, metadata).
That cache is bulky and rebuildable, so it is gitignored — regenerate it any time with:

```bash
python scripts/analyze-reference-video.py "Referensi/Video Referensi/<your-video>.mp4"
```

Requires `ffmpeg` and `ffprobe` on your `PATH`, plus `yt-dlp` and `faster-whisper`
(`pip install -r requirements.txt`).

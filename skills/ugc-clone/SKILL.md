---
name: ugc-clone
description: Run when the user wants to clone, copy or remake a reference video — "bikin kayak video ini", "clone this TikTok", "recreate this ad" — with their own brand, product and character. Watches the reference (scene cuts, movement, framing, dialogue), recommends a generation model from the operator's model knowledge, and writes ready-to-paste prompts in English and Indonesian. It NEVER generates.
---

# UGC Clone

Takes a reference video and turns it into prompts that recreate its idea for the active brand — same energy and structure, your character, your product, your claims.

**This skill never generates anything.** It ends with prompt files the operator pastes into Higgsfield, kie.ai or an official app. No credits are spent except the (free, local) analysis.

Three checkpoints, in order:
1. **Gate 1** — the breakdown of the reference, for the operator to correct
2. **Gate 2** — the plan: adaptation, model, platform, duration, scene split, dialogue
3. **Write** the prompt files

**Prerequisites**
- Brand DNA via `/brand-dna-builder`
- A product in `products.json`, ideally with `product-dna/<slug>.md`
- A character via `/character-creator` (optional — some references are hands-only)
- `ffmpeg` on PATH, and `pip install -r requirements.txt` (yt-dlp, faster-whisper)

---

## Step 0 — Called from `/ugc-studio`?

If the orchestrator already resolved brand, product and character, skip to **Step 4**. Otherwise start at Step 1.

---

## Step 1 — Select brand

Open `./brands/` for subfolders containing `brand-dna.md`. One match — use it and confirm. Several — list and ask. None — point to `/brand-dna-builder`.

Read `brand-dna.md`. Voice, colors, photography style and Hard Rules all constrain the prompt later.

---

## Step 2 — Select product

Read `brands/[brand]/products.json`, present a numbered list, user picks one.

Then read `brands/[brand]/product-dna/<slug>.md` (slug = product `filename` without extension). **The dialogue is written from these facts** — never invent claims.

If there's no DNA file: run `/product-dna` for this product (auto-fills from `page_url` when there is one). If the user insists on skipping, ask just three questions — category, two main benefits, the call to action — and save a minimal DNA file marked ⚠️ so downstream runs know it's thin.

For Indonesian brands, prefer the **Copy — Bahasa Indonesia** section for anything spoken.

---

## Step 3 — Select character

Look in `brands/[brand]/characters/`. One — use it and confirm. Several — list and ask.

Also offer: **"Skip — this video is hands-only or product-only."** Plenty of unboxing and demo references never show a face.

If the chosen character has no `multiangle*.png`, offer it:

> "This character has no angle sheet. Video models hold a face much better with one, especially on ¾ and profile shots. Generate it? ~$0.12 — `python3 scripts/generate-character.py <dir> --multiangle-only`"

Read `character-spec.json` for identity, clothing and tone.

---

## Step 4 — Get the reference video

Ask for the reference, offering what's already on disk:

```
Which video should I clone?

  1. Referensi/Video Referensi/Skin100.mp4
  2. …(other files in that folder)

  Or paste a path, or a TikTok / Instagram / YouTube URL.
```

If the reference runs longer than ~60s, say so and offer to clone one part (`--segment 0:12-0:30`). A 15–30s segment clones far better than a 3-minute video.

---

## Step 5 — Watch it

Run from the project root:

```bash
python scripts/analyze-reference-video.py "<path-or-url>" --slug <ref-slug>
```

Add `--segment 0:12-0:30` for part of it, `--force` to redo a cached analysis.

This writes `Referensi/Video Referensi/_analysis/<ref-slug>/` — `frames/`, `transcript.txt`, `metadata.json`. The cache is **brand-agnostic**: if it already exists from an earlier clone, reuse it and say so.

Then actually look at it:
1. **Read `metadata.json`** — duration, aspect, fps, scene-cut timestamps.
2. **Read the frames in order.** Read them in batches (one tool call per batch, several frames per call); their filenames carry the timestamp.
3. **Read `transcript.txt`.** Any segment with a low `logprob` in `transcript.json`, or any word that doesn't fit the product's category, gets a ❓ at Gate 1.

**A transcript is not automatically a script.** Whisper transcribes whatever it hears, including the music. Song lyrics, a low `language_probability` (under ~0.6), or lines that have nothing to do with the product all mean the same thing: this reference has **no spoken dialogue**, just a music bed. Say so at Gate 1, record the music's feel in the post-production notes, and plan a dialogue-free clone — or offer to add a voiceover the reference never had, as an explicit change at Gate 2.

Build the breakdown using the vocabulary in `docs/ai-tools-knowledge.md` ("Universal prompt craft") and the operator's cheat sheets in `Referensi/Other Insight/` — real framing, angle and movement terms, not vague description.

Two things to check on every reference, because both change the prompt:

- **Mirrored footage.** Front-camera selfies are usually mirrored, so any label in frame reads backwards. That's a artifact of the reference, never something to reproduce — the prompt must ask for the product label facing camera and correctly readable. Note it at Gate 1 so the operator knows you saw it.
- **Whose product is it?** A reference often features a *different* brand's product, in a different shape (jar vs tube, pump vs dropper). Say which product is in the reference, and flag at Gate 2 where the action has to change because ours isn't the same shape — a hand scooping a pad out of a tub can't be copied for a squeeze tube.

### Gate 1 — analysis review

Write `analysis.md` into the cache folder and show it in chat:

```
─── REFERENCE ───

  File:       Skin100.mp4          Duration: 17.3s    Format: 720x1280 (9:16) @30fps
  Cuts:       4                    Audio: yes         Spoken: Bahasa Indonesia

─── SHOT LIST ───

  #  Time        Framing            Angle        Camera          Action
  1  0.0–4.5s    medium close-up    eye level    handheld, still  applies gel to cheek, looks at lens
  2  4.5–6.8s    medium close-up    eye level    jump cut         sweeps gel to hairline
  …

─── AUDIO ───

  Music:      soft lo-fi, calm
  SFX:        fingertip taps on skin (ASMR)
  Dialogue:   [0.0–3.2] "…"   ❓ "poremizing" unclear at 2.1s

─── ON SCREEN ───

  0–3s   caption top-centre: "…"

─── WHY IT WORKS ───

  Hook:     first 1.5s — product already on the face, no intro
  Pacing:   4 cuts in 17s, each beat one action
  Close:    product held to lens, label legible

─── I'M NOT SURE ABOUT ───

  ❓ …
```

Ask: **"Anything I got wrong or should look at again?"** Apply corrections before Gate 2.

---

## Step 6 — Plan the adaptation

Read `docs/ai-tools-knowledge.md` (model cards, quick picker, prompt craft) and `docs/kie-pricing.md` (costs).

**Adaptation.** This is a clone of the *idea*, not a copy of the frames. Keep what makes it work — the hook, the beat structure, the pacing. Change what should be better for this brand, and say why. Swap in the brand's setting, the character, the product and its real claims. Never reuse the reference brand's claims.

**Model.** Route from the Gate-1 findings using the quick picker. Show the top pick plus 1–2 alternatives, each with a one-line reason and a cost. One model for the whole video. Flag the trade-offs honestly — e.g. Seedance mispronouncing Bahasa, Kling 3.0 not speaking it at all, Omni Flash being weak on wide shots.

**Platform.** Ask where they'll paste it (Higgsfield / kie.ai / official app), defaulting to their last answer. It decides the prompt's syntax and how references attach.

**Duration and split.** Default to the reference's duration, rounded to what the model accepts. One multi-shot prompt if it fits; otherwise split into clips at the model's maximum and chain them (each clip's end frame is the next clip's start frame). State the split plainly.

**Dialogue.** Draft it in the brand's language from the product DNA, matching the reference's beat structure, ~2.5 words per second, 5–10 words per line. Keep the platform's language limits in mind.

**Assets.** List what gets uploaded: `headshot.png`, `multiangle.png`, `fullbody.png`, the product image, and any start/end frames to be generated first.

### Gate 2 — plan review

```
─── ADAPTATION ───

  Keep:       [what carries over from the reference and why]
  Change:     [what improves for this brand and why]

─── PLAN ───

  Brand:      [brand]              Product:   [product]
  Character:  [character | none — hands only]
  Model:      [pick] — [one-line reason]
  Alternatives: [alt] — [trade-off] · [alt] — [trade-off]
  Platform:   [Higgsfield / kie.ai / official]
  Duration:   [N]s → [1 clip, multi-shot | N clips of Xs, chained]
  Aspect:     [from the reference]
  Est. cost:  ~[credits] (~$[x] / Rp [y])   [or "check price on the platform"]

─── DIALOGUE (Bahasa Indonesia) ───

  [0–3s]   "…"
  [3–7s]   "…"

─── ASSETS TO UPLOAD ───

  1. headshot.png      (face)
  2. multiangle.png    (face, other angles)
  3. [product].png     (product)
```

Outside the block: **"Edit anything above, or say 'go' and I'll write the prompts."** Loop until they say go.

---

## Step 7 — Write the prompt files

Create `brands/[brand]/ugc-clone/[character]-[product]-[ref-slug]/` (use `handsonly` in place of the character when there is none). Re-runs version the files as `_v2`.

Write four things:

**1. `prompt-en.md`** — what gets pasted. In the chosen model's native syntax (`docs/ai-tools-knowledge.md` has the per-model formats). The house format, from `brands/skin1004/product-ugc/kirana-skin100-remake/kling-prompt-en.txt`:

```
[aspect] vertical, [N]s, [look and shooting style]. Start exactly on the start frame[ and end exactly on the end frame]. Keep the same [person, hair, outfit, location, light] throughout. Real skin texture, no beauty filter.

Shot 1 (0-4.5s): [one flowing action sentence — framing, angle, camera move, what happens]

Shot 2 (4.5-6.8s): [Jump cut, …]

Audio: [music, SFX] — [dialogue, or "No voiceover, no dialogue."]

Avoid: face changing between shots, extra fingers, warped or misspelled label, text overlays, subtitles.
```

Each section of the file:
- **Start-frame image prompt** (per clip) — identity-locked, references in order (headshot first, product second), label text quoted, describing only the first frame. Plus an end-frame prompt when the model reads one.
- **Video prompt** (per clip) — as above.
- **References to upload** — the files, in order, with the platform's slot names.
- **Settings** — model, duration, aspect, resolution.

**2. `prompt-id.md`** — the same thing in Indonesian, for reading and for sharing with a client. **Dialogue stays in Bahasa in both files** — translating the spoken line into English in `prompt-en.md` would make the model speak English.

**3. Post-production notes** (a section in both files) — overlay text with timings, captions, music feel, SFX, and the cuts to make in CapCut. **None of this goes in the generation prompt** — video models garble text.

**4. `ugc-clone-spec.json`**:

```json
{
  "output_name": "kirana-poremizing-light-gel-cream-skin100",
  "brand": "skin1004",
  "character_dir": "brands/skin1004/characters/kirana",
  "product_image": "brands/skin1004/product-images/poremizing-light-gel-cream.png",
  "product_name": "Poremizing Light Gel Cream",
  "reference": {
    "slug": "skin100",
    "source": "Referensi/Video Referensi/Skin100.mp4",
    "analysis": "Referensi/Video Referensi/_analysis/skin100/",
    "segment": [0, 17.3]
  },
  "platform": "kie.ai",
  "video_model": "kling-3.0",
  "start_frame_model": "nano-banana-pro",
  "aspect_ratio": "9:16",
  "duration": 15,
  "clips": 1,
  "dialogue_language": "id",
  "generated": false
}
```

`generated` stays `false` — this skill never generates.

---

## Step 8 — Hand off

Confirm the paths, then stop:

```
Prompts ready:
  brands/[brand]/ugc-clone/[output-name]/prompt-en.md   ← paste this
  brands/[brand]/ugc-clone/[output-name]/prompt-id.md   ← for reading / the client
  Analysis: Referensi/Video Referensi/_analysis/[ref-slug]/

Paste prompt-en.md into [platform], upload the references in the listed order, and the post-production notes cover the edit.
```

Do not offer to generate. If the user asks to generate anyway, point them to `/ugc-content` (Higgsfield) or `/ugc-content-kie` — those skills own generation.

---

## Iteration

- **Different model or platform:** reopen Gate 2, re-pick, rewrite the prompts (`_v2`). The analysis is reused.
- **Different product or brand, same reference:** run again — Step 5 finds the cached analysis and skips straight to Gate 1 confirmation.
- **Reference didn't read well:** re-run the analyzer with `--fps 2` (more frames) or `--whisper-model medium` (better transcript, slower).

---

## Notes

- **Never generates.** No Higgsfield, kie.ai or MCP generation calls from this skill — not even "just the start frame".
- **The analysis cache is brand-agnostic** and lives beside the reference videos. `source.mp4`, `frames/` and `audio.wav` are gitignored; `analysis.md`, `transcript.txt` and `metadata.json` are kept.
- **Never face-lock the person in the reference video.** They inform the casting type at most — see `/character-creator` Step 2.
- **Claims come from product DNA**, never from the reference brand's script. Copy structure, not substance.
- **Text belongs in post.** Overlays, captions and subtitles are for CapCut, never the prompt.
- **Costs** come from `docs/kie-pricing.md` for kie models; anything else is "check price on the platform" — never invent a number.

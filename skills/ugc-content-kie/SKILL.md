---
name: ugc-content-kie
description: Run when the user wants a UGC-style video generated on the kie.ai backend (instead of Higgsfield) — talking-head, unboxing, tutorial, review, or try-on. kie.ai analogue of /ugc-content. Builds the video in two stages (Nano Banana Pro still → routed video model: Gemini Omni Flash / Kling 2.6 / Kling 3.0 / Seedance 2.0, auto-picked from the brief). Auto-fills brief from product-dna + brand-dna. Use when Higgsfield has no credits or the user asks for the kie.ai path.
---

# UGC Content (kie.ai)

Generates a branded UGC-style video on the **kie.ai** backend. Same five modes as `/ugc-content`, but kie.ai has no Marketing Studio Video pipeline, so the video is built in two stages:

1. **Nano Banana Pro** — composes a still of the character wearing/using the product (character headshot + product image as references).
2. **Routed video model** — animates that still. Auto-picked from the brief: **Gemini Omni Flash** when the character speaks (the normal case — supersedes Veo 3.1), **Kling 2.6** for realistic no-dialogue motion with sound effects, **Kling 3.0** for cinematic multi-shot no-dialogue motion, **Seedance 2.0 Fast** for fast physical demo motion, **Seedance 2.5** when the brief needs top-tier physics or a clip longer than 10s. Failures retry once on `veo3_fast` (legacy but proven).

Each output is a versioned MP4 saved under `./brands/[brand-name]/ugc-content-kie/[mode]/[output-name]/` (kept separate from Higgsfield `/ugc-content` outputs).

**Prerequisites:**
- Brand DNA via `/brand-dna-builder`
- A product in `products.json` (URL-having or manual — both work; the product image is used as a visual reference)
- A character via `/character-creator` (uses `headshot.png`; imported characters work too)
- kie.ai connected — `KIE_API_KEY` in project `.env` (verify with `python scripts/kie-check.py`)

---

## Step 1 — Select brand

Open `./brands/` for subfolders containing `brand-dna.md`. One match — use it and confirm. Multiple — list and ask. None — point to `/brand-dna-builder`.

---

## Step 2 — Select character

Look in `./brands/[brand-name]/characters/` for character folders. One — use and confirm. Multiple — list and ask. None — point to `/character-creator`.

Read `character-spec.json` for identity context (used to preserve face/identity in the Stage 1 still). Only `headshot.png` is required; `fullbody.png` is optional here.

---

## Step 3 — Select product

Read `brands/[brand-name]/products.json`, present a numbered list, user picks one. Both URL-having and manual products work — the product image is uploaded and passed to Nano Banana Pro as a visual reference (no URL needed).

Read `brands/[brand-name]/product-dna/<slug>.md` if it exists for facts to feed the brief. Slug = product filename without extension. **If the product-dna has a "Copy — Bahasa Indonesia" section, prefer it for the Hero/dialogue** (Gemini Omni Flash speaks the dialogue aloud, incl. Bahasa Indonesia — localized copy sounds authentic for Indonesian brands).

---

## Step 4 — Select mode

```
Pick a video mode:

  1. UGC        — realistic social-media style video, casual selfie energy
  2. Tutorial   — step-by-step explainer or how-to
  3. Unboxing   — package-reveal sequence (hands-only is fine)
  4. Review     — presenter giving an authentic opinion
  5. Try-On     — virtual try-on of CLOTHING or ACCESSORIES (fashion/eyewear)
```

Map to `mode`: `ugc`, `tutorial`, `unboxing`, `review`, `tryon`.

---

## Step 5 — Compose brief + settings, then show ONE preview

**Pass A — compose the brief pre-fill:**
- **Setting:** inferred from product category + mode
- **Scene:** ONE flowing action sentence (character + product + mode action). NEVER a comma-list of beats — write it as one natural motion so the spoken dialogue flows.
- **Hero:** top 1-2 lines from product-dna "Key benefits" (prefer the Bahasa copy for Indonesian brands). EMPTY by default for Try-On and Unboxing.

**Pass B — default settings (operator can override):**
- Aspect: `9:16` (default)
- Duration: `8s` (Gemini Omni Flash supports 4 / 6 / 8 / 10s; Veo 3.1 4 / 6 / 8s; Kling 2.6 5 / 10s; Kling 3.0 up to 10s here; **Seedance 2.5 up to 30s in one call** — every other model here stops at 10s)
- Resolution: `1080p`
- Video model — **route it from the brief you just composed**, then show the pick + one-line reason:
  - Character speaks to camera (UGC / Review / Tutorial with dialogue — the normal case) → `gemini-omni-flash` (**Gemini Omni Flash** — best talking-head incl. Bahasa Indonesia; most realistic in close-up, weaker on wide shots). `veo3_fast` / `veo3` (Veo 3.1 — legacy, superseded) only on explicit request.
  - No spoken dialogue, realistic motion with sound effects → `kling-2.6` (**Kling 2.6**).
  - No spoken dialogue, cinematic mood or multi-shot product-in-motion (many Unboxing / Try-On briefs) → `kling-3.0` (**Kling 3.0**, native ambient audio; its dialogue mode is zh/en only — never for Indonesian scripts).
  - No dialogue, fast energetic physical motion (hands demoing, quick cuts) → `seedance-2-fast` (**Seedance 2.0 Fast**).
  - No dialogue, and either the best physical realism or a clip longer than 10s is genuinely needed → `seedance-2-5` (**Seedance 2.5** — renders up to 30s in one call and reads a closing frame; the priciest model here at 63 cr/s @720p, so state the cost before running it).
- Dialogue language: default to the brand's language (Bahasa Indonesia for Indonesian brands; else English). Dialogue only exists on the speaking models (Gemini Omni Flash / legacy Veo) — Kling/Seedance clips are dialogue-free by design.
- Audio: ON (locked — the speaking model voices the script; Kling/Seedance generate ambient audio / sound effects)

**Render this single block in chat:**

```
─── BRIEF ───

  Setting:    [final Setting]
  Scene:      [final Scene]
  Hero:       [final Hero]


─── SETTINGS ───

  Mode:          [Mode label]
  Character:     [character name]
  Product:       [product name]
  Aspect:        [9:16 / 1:1 / 16:9]
  Duration:      [N]s
  Resolution:    [720p / 1080p]
  Video model:   [gemini-omni-flash / kling-2.6 / kling-3.0 / seedance-2-fast / seedance-2-5 (veo3_fast / veo3 legacy)] — [one-line reason from the routing rules]
  Dialogue:      [language / — (no dialogue on Kling/Seedance)]
  Est. cost:     ~[still + video] credits   (Nano Banana Pro still ~35 + video model — see cost reference; Omni Flash pricing TBD, record the first receipt)
```

**OUTSIDE the code block**, on a plain line:

> Edit any line above, or say **'go'** to generate.

Loop, recomposing on edits, until the operator says 'go'.

**Cost reference (kie.ai credits):**
- Nano Banana Pro still (2K): ~35 cr
- Gemini Omni Flash: mid price, slightly above Veo 3.1 Fast — exact kie.ai pricing TBD; record the first run's receipt into `docs/kie-pricing.md`
- Veo 3.1 Fast, 8s w/ audio: ~60 cr (legacy) · Veo 3.1 Quality: ~400 cr (legacy)
- Kling 2.6 / Kling 3.0 (std, ≤10s) / Seedance 2.0 Fast: pricing varies — check kie.ai/pricing or `docs/kie-pricing.md` before first use

**Anti-patterns (same as /ugc-content):** no boilerplate scene descriptors, no invented "she says:" dialogue lines (the speaking model writes/speaks the script from the brief), don't dump ingredient lists, don't write Scene as a comma-list.

---

## Step 6 — Generate

1. Slug the output name: `[character-slug]-[product-slug]-[mode]` (product-slug = product `filename` minus extension; never strip articles).

2. Create folder: `brands/[brand]/ugc-content-kie/[mode]/[output-name]/`

3. Write `ugc-content-kie-spec.json` to that folder using EXACTLY this format:

```json
{
  "output_name": "dianti-saturdays-clear-green-sunglasses-tryon",
  "brand": "saturdays",
  "character_dir": "brands/saturdays/characters/dianti",
  "product_image": "brands/saturdays/product-images/saturdays-clear-green-sunglasses.webp",
  "product_name": "SATURDAYS Ashley Ti — Crystal Sunglasses",
  "mode": "tryon",
  "setting": "Bright minimalist café by a window, weekend morning",
  "scene": "Dianti slips on the Ashley Ti sunglasses and turns to camera with an easy smile",
  "hero": "Gagang titanium Jepang — ringan dipakai seharian",
  "aspect_ratio": "9:16",
  "duration": 8,
  "resolution": "1080p",
  "video_model": "gemini-omni-flash"
}
```

- `product_name` — human-readable, used in the still prompt.
- `video_model` — the routed pick from Step 5: `gemini-omni-flash` / `kling-2.6` / `kling-3.0` / `seedance-2-fast` / `seedance-2-5` (`veo3_fast` / `veo3` accepted as legacy). Legacy `veo_model` is still accepted; omitted or unknown values default to `gemini-omni-flash`.
- `still_prompt` / `video_prompt` — OPTIONAL overrides. If omitted, the script composes them from the slots (identity-locked still; on the speaking path Bahasa/English UGC dialogue referencing the Hero benefit; on Kling/Seedance a dialogue-free motion prompt).

4. Run from project root:
   ```bash
   python scripts/generate-ugc-content-kie.py brands/[brand]/ugc-content-kie/[mode]/[output-name]
   ```
   Stage 1 uploads the headshot + product image and composes the still; Stage 2 animates it via the routed video model (auto-retrying once on `veo3_fast` if the routed model fails). Auto-versions `_v1`, `_v2`, … and also keeps the intermediate still (`_still_v1.png`).

5. Confirm saved paths:
   > `…/[output-name]_v1.mp4`  (video)
   > `…/[output-name]_still_v1.png`  (composed still)

6. Ask: "Happy with the output? Regenerate (`_v2`), adjust the brief, tweak the still, or move on?"

---

## Iteration

- **Regenerate same brief:** re-run the script → `_v2.mp4`.
- **Adjust brief:** edit the spec slots (or set explicit `still_prompt` / `video_prompt`), re-run.
- **Talking-head quality:** `gemini-omni-flash` is the default and best pick; `veo3_fast` (~60 cr) / `veo3` (~400 cr) are legacy alternatives on explicit request.
- **Different energy:** switch `video_model` in the spec — `kling-2.6` for realistic motion + sound effects, `kling-3.0` for cinematic no-dialogue motion, `seedance-2-fast` for fast physical motion, `seedance-2-5` for the best physics or a clip past 10s — and re-run.
- **Switch mode:** run again, pick a different mode → different `ugc-content-kie/[mode]/` subfolder.

---

## Notes

- **Backend split:** this skill is the kie.ai path; `/ugc-content` is the Higgsfield path. They write to different folders (`ugc-content-kie/` vs `ugc-content/`) and never collide. Pick kie.ai when Higgsfield is out of credits.
- **Two-stage = two charges:** every run consumes a Nano Banana Pro still charge + a video-model charge. Regenerating re-runs both stages.
- **Identity preservation** relies on the headshot as the FIRST reference image and the product as the SECOND, with an explicit identity-lock instruction in the still prompt. If the face drifts, regenerate or refine `still_prompt`.
- **Durations:** Gemini Omni Flash 4 / 6 / 8 / 10s; Veo 3.1 4 / 6 / 8s only; Kling 2.6 5 / 10s. Audio is generated server-side (dialogue + ambience) — there is no audio-off toggle.
- **Model routing** (`scripts/generate-ugc-content-kie.py`): spoken script → Gemini Omni Flash (Veo legacy); no dialogue → Kling 2.6 (realistic + SFX), Kling 3.0 (cinematic) or Seedance (motion). Only the speaking models voice dialogue — Kling 3.0's own dialogue mode is zh/en only and Seedance mispronounces Indonesian, so keep both dialogue-free here. The script caps Kling 3.0 at 10s `std` mode as a cost guardrail, pins Seedance 2.5 to 720p (63 cr/s; 1080p is 114) and caps it at 30s, and falls back to `veo3_fast` (with a spoken prompt) if the routed model fails — that fallback is 8s max, so a long Seedance 2.5 run degrades to a short clip.
- **Gemini Omni Flash framing:** it shines in close-up talking-head shots and is weaker on wide shots — keep the Scene close/medium framing on the speaking path.
- **Dialogue language:** default follows the brand; for Indonesian brands the script instructs the speaking model to speak Bahasa Indonesia and pulls the Hero from the product-dna Bahasa copy when available.
- **Uploads are cached** via `<file>.kie.url` sidecars (kie.ai temp URLs expire ~3 days; the helper re-uploads when stale).

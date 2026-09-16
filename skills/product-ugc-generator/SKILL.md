---
name: product-ugc-generator
description: Run when the user wants to create a UGC selfie of a character holding a product, generate product UGC content, or create a talking-head video of a character with a product. Takes a character and product image, generates a photorealistic iPhone selfie of the character holding the product, then continues into a UGC talking-head video via Veo 3.1. Output saved under the active brand folder.
---

# Product UGC Generator

Two-stage workflow:
1. **UGC image** — photorealistic iPhone front-camera selfie of the character holding a product at 9:16 2K
2. **UGC video** — talking-head video from the selfie at 9:16 1080p via Veo 3.1

**Prerequisites:** Brand DNA set up via `/brand-dna-builder` and a character created via `/character-creator`.

Output saved to `./brands/[brand-name]/product-ugc/[output-name]/`.

---

## Step 1 — Select brand

Open `./brands/` and look for any subfolder with a `brand-dna.md` file inside. One match — proceed with it and confirm which brand is active. Several matches — display the options and ask which one to work with. No matches — the brand setup hasn't been done yet, point them to `/brand-dna-builder`.

---

## Step 2 — Select character

Look inside `./brands/[brand-name]/characters/` for available character folders. One found — use it and confirm. Several found — display the options and ask which one to use. No characters yet — they need to create one first with `/character-creator`.

Read `brands/[brand-name]/characters/[character-name]/character-spec.json` to get the clothing fields.

---

## Step 3 — Select product

Check `brands/[brand-name]/studio-shots/` first. Studio shots are saved one level deep inside subfolders — look inside each subfolder for image files. If any exist, display them as a numbered list and suggest using one:

```
Studio shots available:

  1. [folder name]
  2. [folder name]
  ...

Which product? Pick a number — or say "product images" to browse product-images/ instead.
```

If no studio shots exist, fall back to `brands/[brand-name]/product-images/` and display everything found. If the product they want isn't there, ask them to drop the image into that folder before continuing — remind them: lowercase, hyphens, no spaces — e.g. `energy-drink-pink.jpg`.

Wait for the user to confirm before proceeding. Use the exact file path in the spec.

**Load product-dna alongside brand-dna:**

Once the product is selected, derive its slug from the product image filename (no extension). Read `brands/[brand-name]/product-dna/<slug>.md` if it exists. Hold both `brand-dna.md` (loaded in Step 1) and `product-dna.md` as live context for Step 4. If `product-dna.md` doesn't exist for this product, proceed with brand-dna only.

---

## Step 4 — Creative brief

Ask:

> "I have your brand DNA and product. Want me to write the creative brief, or would you prefer to describe it yourself?"

**Auto path:**
Read `brands/[brand-name]/brand-dna.md` in full. Use the brand's voice adjectives, target audience, and positioning to write a brief that sounds like a real person from that audience — not an ad.

Write:
- **Action** — where the character is and their body position (e.g. standing outside a gym, sitting at a café, walking along a street) — one short phrase. Do not describe what they do with their hands or the product — the image prompt handles product placement automatically.
- **Location** — a visual scene, not a prompt instruction — specific enough to picture (e.g. "street outside a city gym, late evening, neon-lit" not "outdoor location")
- **Script** — what they say in the video. 24–25 words — written to fill an 8-second video naturally. Must name or reference the product. Written as something the target audience would actually say to a friend — casual, specific, with a natural hook. The 24-25 words should advertise the product — use `product-dna.md` (Key benefits, Notable absences, Positioning) as the source for what the script says about it, rather than inventing claims. No generic lines ("I love this product", "you need to try this").
- **Voice notes** — how they should sound. Derive directly from the brand's voice adjectives — e.g. "warm and casual, like talking to a friend" or "direct and confident, dry humour". Do not ask the user for this separately.

Present the full brief once:

> "Here's the creative brief:
> Action: [action]
> Location: [location]
> Script: '[script]'
> Voice: [voice notes]
> Happy with this, or want to tweak anything?"

Never skip this review step. Always wait for confirmation before moving on.

**Manual path:**
Ask in one message:

> "What's happening, where, and what do they say? (e.g. stepping out of the gym, 'I started keeping one of these in my bag and now I don't know how I trained without it.')"

Extract action, location, script, and voice notes from their response. If they don't mention voice notes, derive from brand DNA.

---

## Step 5 — Name and write spec

Derive a slug from the character name, product name, and a short location word — e.g. `pynki-energy-drink-market`. Ask the user to confirm or rename.

Create the output folder and write the spec:

```
brands/[brand-name]/product-ugc/[output-name]/
  product-ugc-spec.json
```

**product-ugc-spec.json:**
```json
{
  "output_name": "pynki-energy-drink-market",
  "brand": "[brand-name]",
  "character_dir": "brands/[brand-name]/characters/[character-name]",
  "product_image": "brands/[brand-name]/studio-shots/[folder]/[file].png",
  "action": "walking through a busy market, mid-stride",
  "location": "outdoor market in Marrakech, late afternoon",
  "clothing": "[pulled from character-spec.json — top, bottom, shoes, accessories]",
  "script": "Okay I'm just gonna say it — PYNK is my go-to right now.",
  "voice_notes": "",
  "duration": "",
  "video_image_version": ""
}
```

`video_image_version` is the version number only — e.g. `"1"` for `_v1.png`, `"2"` for `_v2.png`. Never write `"v1"` or the full filename.

`clothing` is read directly from the character spec — do not ask the user for it.

**Auto path:** Write `voice_notes` from the brief in Step 4 and `duration` as `"8"`. Leave `video_image_version` blank — it gets filled in Step 8 after image review.

**Manual path:** Leave `voice_notes` and `duration` blank — both get filled in Step 8 after image review.

---

## Step 6 — Generate image

From the project root, run:

```bash
python3 scripts/product-ugc-generator.py brands/[brand-name]/product-ugc/[output-name] --image
```

This pulls the product image, headshot, and clothing description from the spec and generates the UGC selfie.

Cost: ~$0.12

---

## Step 7 — Review image

Confirm the save path:
`brands/[brand-name]/product-ugc/[output-name]/[output-name]_v1.png`

Ask:

> "How does it look?
> - **Keep it** — move on to the video
> - **Regenerate** — same brief, new variation
> - **Adjust** — change the action, location, or product and regenerate"

Each run saves a new file — `_v1`, `_v2`, `_v3` — no previous version is replaced.

If multiple versions exist when the user is ready to continue, list them and ask which one to use for the video.

---

## Step 8 — Voice notes and duration

**Auto path:** Duration is already set to 8s and voice notes are already in the spec from Step 4. Just update `video_image_version` in `product-ugc-spec.json` and move straight to Step 9.

**Manual path:** Calculate the suggested duration from the script word count:
- Up to 15 words → 4s
- 16–21 words → 6s
- 22–27 words → 8s
- Over 27 words → warn: "Your script is [X] words — this will likely feel rushed or get cut off at 8s. Consider trimming to 27 words or under before generating."

Ask in one message:

> "Two things before the video:
> - How should they sound? (e.g. 'warm and casual, slight American accent', 'excited and upbeat')
> - Your script is [X] words — I'd suggest [Xs]. Want to go with that or choose a different length? Options: 4s, 6s, or 8s"

Update `product-ugc-spec.json` with `voice_notes`, `duration`, and `video_image_version`.

---

## Step 9 — Generate video

From the project root, run:

```bash
python3 scripts/product-ugc-generator.py brands/[brand-name]/product-ugc/[output-name] --video
```

Sends the confirmed image to Veo 3.1 together with the assembled video prompt — action, script, voice notes, and the product visibility instruction. Output at 1080p 9:16.

Cost per generation: $0.60 for 4s, $0.90 for 6s, $1.20 for 8s

---

## Step 10 — Present result

Confirm the save path:
`brands/[brand-name]/product-ugc/[output-name]/[output-name]-run1.mp4`

Ask:

> "How does the video look?
> - **Done** — what would you like to do next?
> - **Regenerate** — same script and settings, new generation
> - **Adjust** — change the script, voice notes, or duration and re-run"

---

## Notes

- Each brand keeps its own `product-ugc/` folder — different brands never interfere with each other
- Better input image = better product fidelity. Use a clean packshot where the label and branding are fully visible — the model can only render what's clearly shown in the reference. If the product looks wrong, improve the source image before regenerating.
- Veo 3.1 includes audio in every render — the script text drives it, nothing to configure separately
- Only 4s, 6s, and 8s are valid durations — Veo 3.1 rejects anything else
- **One-shot mode:** Skip the image review and run both stages together:
  ```bash
  python3 scripts/product-ugc-generator.py brands/[brand-name]/product-ugc/[output-name] --image --video
  ```
  Only use this when you're confident in the brief — the image won't be reviewed before the video runs.

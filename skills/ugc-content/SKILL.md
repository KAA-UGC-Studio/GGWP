---
name: ugc-content
description: Run when the user wants to create a UGC-style video — talking-head, unboxing, tutorial, product review, or virtual try-on. Wraps Higgsfield Marketing Studio Video with 5 mode-aware paths. Auto-fills brief from product-dna + brand-dna; character avatar and product entity are resolved silently. Output saved under the active brand folder.
---

# UGC Content

Generates a Marketing Studio Video — branded UGC-style video — through Higgsfield. One skill, five modes. Each output is a versioned MP4 saved under `./brands/[brand-name]/ugc-content/[mode]/[output-name]/`.

**Prerequisites:**
- Brand DNA set up via `/brand-dna-builder`
- A product registered in `products.json` (any product — URL-having or manually added without URL; both paths work)
- A character created via `/character-creator` (the headshot becomes the avatar; the fullbody is used as an outfit-lock reference)

---

## Step 1 — Select brand

Open `./brands/` and check for subfolders containing a `brand-dna.md`. One match — use it and confirm. Multiple matches — list them and ask which one. None — point them to `/brand-dna-builder`.

---

## Step 2 — Select character

Look inside `./brands/[brand-name]/characters/` for available character folders. One found — use it and confirm. Multiple found — list them and ask. None — they need to create one first via `/character-creator`.

Read `brands/[brand-name]/characters/[character-name]/character-spec.json` for context (the character's name, clothing, look) — used in scene composition during the brief step.

---

## Step 3 — Select product

Read `brands/[brand-name]/products.json` and present a numbered list of products. User picks one.

Any product in the list is selectable — both URL-having (Shopify-style) and manually added (no URL) products work. The script routes between two paths automatically based on whether the product has a `page_url`:
- URL-having products use the Marketing Studio Product entity (auto-scraped product images + metadata — highest quality).
- Manual products pass the product image upload UUID directly via `--medias` (no entity created; product image used as a media reference). Output quality is on-par at 1080p.

Read `brands/[brand-name]/product-dna/<slug>.md` if it exists, for facts to feed into the brief. Slug = product filename without extension.

---

## Step 4 — Select mode

Present the 5-mode picker:

```
Pick a video mode:

  1. UGC        — realistic social-media style video, casual selfie energy
  2. Tutorial   — step-by-step explainer or how-to
  3. Unboxing   — package-reveal sequence (hands-only is fine)
  4. Review     — presenter giving an authentic opinion
  5. Try-On     — virtual try-on of CLOTHING or ACCESSORIES (fashion items only)
```

User picks ONE number. Map the user's pick to the spec's `mode` field using lowercase labels: `ugc`, `tutorial`, `unboxing`, `review`, `tryon`.

---

## Step 5 — Compose brief + settings, then show ONE comprehensive preview

Build the full preview in TWO passes, then render it as a SINGLE fenced code block.

**Pass A — compose the brief pre-fill:**
- **Setting:** inferred from product category + mode
- **Scene:** ONE flowing action sentence using character + product + mode-appropriate action (NEVER a comma-list — see anti-patterns below)
- **Hero:** top 1-2 lines from `product-dna.md` "Key benefits" only, capped, no overflow (EMPTY by default for Try-On and Unboxing modes)

**Pass B — apply default settings (operator can override in the preview):**
- Aspect: `9:16` (default — most UGC is vertical)
- Duration: `12s` (default; operator can override freely from 1-15s)
- Resolution: `1080p` (default — production floor)
- Audio: ON (locked — do NOT show in the preview)
- Outfit-lock: ON (locked — do NOT show in the preview)

**Then render this single block in chat (copy the layout exactly, including the `─── ──` dividers and the blank line spacing):**

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
  Duration:      [Ns]   →  ~[N×rate] credits
  Resolution:    [480p / 720p / 1080p]
```

**Cost rate to use in the inline calculation** (audio always on, Marketing Studio Video):
- 480p: 3.5 cr/s
- 720p: 5 cr/s
- 1080p: 10 cr/s

**OUTSIDE the fenced code block**, on a plain chat line:

> Edit any line above, or say **'go'** to generate.

Then wait. If the operator edits any line — brief slots, aspect, duration, resolution — recompose the preview with the updated value(s), update the credit estimate accordingly, and show it again. Loop until they say 'go'.

**Mode-aware pre-fill guidance:**

| Mode | Pre-fill scene focus |
|---|---|
| UGC | Casual social moment — character holding the product, off-the-cuff line referencing the Hero benefit |
| Tutorial | Step-by-step or single-step demonstration of the product |
| Unboxing | Hands revealing the product from packaging — character may or may not appear |
| Review | Character giving an authentic opinion, mentioning Hero benefit |
| Try-On | Character wearing/using the product — clothing/accessories only |

**Notes on what NOT to do:**
- ❌ No boilerplate scene descriptors ("casual selfie-style video") — `--mode` already tells Higgsfield that
- ❌ No invented dialogue ("she says: ...") — Higgsfield's backend writes the script
- ❌ Don't dump full product-dna ingredients lists — overflow risk; cap to 1-2 Hero lines
- ❌ Don't include character clothing in the Hero — it goes in Scene if needed
- ❌ **Don't write Scene as a comma-list.** Higgsfield enumerates each comma-separated phrase as a robot-procedure beat. Example bad: `"wet hands, scooping, lathering, applying"` → script becomes `"I use the wash on damp hands. P-size. Foam it up. Massage."` (reads like a checklist). Example good: `"Sara demonstrating The Rice Wash in a single continuous motion from rinse to lather to clean skin"` (flowing → natural dialogue). Write Scene as ONE flowing action sentence, not a list of beats.
- ❌ Don't show Audio or Outfit-lock in the preview — they're locked ON and not operator choices.
- ❌ Don't put "Edit any line, or say 'go'" INSIDE the code block — it's an instruction to the operator, render as plain chat text below the block.

---

## Step 6 — Generate

1. Compose the final `--prompt` string from the three slots:
   > `"Setting: <setting>. Scene: <scene>. Hero: <hero>."`

2. Slug the output name: `[character-slug]-[product-slug]-[mode]` where:
   - `[character-slug]` = basename of `character_dir` (e.g. `sara`)
   - `[product-slug]` = the product's `filename` field in `products.json` with the extension stripped (e.g. `the-rice-wash.jpg` → `the-rice-wash`) — this is the authoritative slug, NEVER strip articles like "the"/"a"/"an"
   - `[mode]` = lowercase mode label (e.g. `ugc`, `tutorial`, `unboxing`, `review`, `tryon`)

   Example: sara character + The Rice Wash (filename `the-rice-wash.jpg`) + UGC mode → `sara-the-rice-wash-ugc`. The same combination must always resolve to the same folder so re-runs auto-version (`_v1`, `_v2`, ...) inside it rather than creating duplicate folders.

3. Create the output folder if missing:
   > `brands/[brand]/ugc-content/[mode]/[output-name]/`

4. Write `ugc-content-spec.json` to that folder using EXACTLY this format:

```json
{
  "output_name": "sara-rice-wash-ugc",
  "brand": "tatcha",
  "character_dir": "brands/tatcha/characters/sara",
  "product_image": "brands/tatcha/product-images/the-rice-wash.jpg",
  "mode": "ugc",
  "setting": "Sunlit bathroom counter, morning routine",
  "scene": "Sara holding The Rice Wash, sharing a thought between rinsing her face",
  "hero": "Gentle creamy cleanser — doesn't leave skin tight",
  "prompt": "Setting: Sunlit bathroom counter, morning routine. Scene: Sara holding The Rice Wash, sharing a thought between rinsing her face. Hero: Gentle creamy cleanser — doesn't leave skin tight.",
  "aspect_ratio": "9:16",
  "duration": 12,
  "resolution": "1080p",
  "generate_audio": true
}
```

5. Run from the project root:
   ```bash
   python3 scripts/generate-ugc-content.py brands/[brand]/ugc-content/[mode]/[output-name]
   ```

   This silently resolves the Marketing Studio entities (avatar from headshot, product from URL fetch, optional outfit-lock from fullbody) and submits the video job. `--wait` blocks until completion.

6. Confirm the saved path:
   > `brands/[brand]/ugc-content/[mode]/[output-name]/[output-name]_v1.mp4`

7. Ask: "Happy with the output? Regenerate (creates `_v2`), adjust the brief, or move to the next?"

---

## Iteration

**Regenerate same brief:** re-run the script. Auto-versions `_v2.mp4`, `_v3.mp4`, etc.

**Adjust brief and regenerate:** open the spec, edit the 3 slots + the composed `prompt` string, re-run the script.

**Switch mode for same character + product:** run `/ugc-content` again, pick a different mode. Lands in a different `ugc-content/[new-mode]/` subfolder.

---

## Notes

- **Outfit lock is permanently ON.** The character's `fullbody.png` is always passed via `--medias` when a character is provided. Verified through round-1 testing — significantly improves outfit consistency vs single-headshot avatar alone.
- **Prompt enhancement is server-side.** Higgsfield rewrites the brief into a full screenplay-style prompt before generating. The 3-slot brief is intentionally minimal — Higgsfield's backend writes the script, shot list, and dialogue from the facts you provide.
- **Audio is always on.** Higgsfield generates audio (dialogue + room tone) server-side. No toggle for off in this skill.
- **Character avatar = headshot only.** Marketing Studio avatars are built from a single image. To compensate for outfit/body drift, the fullbody.png is passed as a `medias` reference during the video call. Sidecars: `headshot.png.avatar.uuid` (the Marketing Studio Avatar entity) and `fullbody.png.uuid` (the upload UUID for the outfit reference).
- **Stale UUID handling:** Higgsfield garbage-collects old uploads. `resolve_image()` verifies UUIDs against the account's recent upload list and re-uploads if a sidecar's UUID has expired.
- **Manual products handled via medias fallback:** Higgsfield's `marketing-studio products create` endpoint returns HTTP 405 server-side. The skill works around this by passing the product image upload UUID via `--medias` (alongside the fullbody outfit-lock reference) instead of `--product_ids`. No Marketing Studio Product entity is created for manual products. Output quality validated as on-par with URL-having products at 1080p. The underlying Higgsfield bug remains unfixed — re-test after CLI upgrades.

---
name: product-visual
description: Run when the user wants to generate a brand-faithful product image in one of 7 mode-tuned styles — lifestyle scene, closeup with hands, Pinterest moodboard, wide hero banner, model holding the product, surreal conceptual shot, or aesthetic restyle of an existing render. Wraps Higgsfield's product-photoshoot endpoint. Auto-fills brand and product context from `brand-dna.md` + `product-dna.md` per a locked per-mode pull table; the user reviews + edits one structured brief before generation. Outputs versioned PNGs under the active brand folder.
---

# Product Visual

Generates a brand-faithful product image through Higgsfield's mode-tuned `product-photoshoot` endpoint. One skill, seven photo modes. Each output is a versioned PNG saved under `./brands/[brand-name]/product-visual/[output-name]/`.

**Prerequisites:**
- Brand DNA set up via `/brand-dna-builder`
- The product registered in `products.json` and a Product DNA file created via `/product-dna` (recommended — some modes use ingredients to drive props)
- A character created via `/character-creator` (optional — only for the `virtual_model_tryout` mode if the user wants identity-locked output)

This skill is for **product in a context** (scene, mood, banner, model, concept, restyle). For a clean studio shot use `/studio-shot-generator`. For placing a product into a specific scene reference image use `/product-shot-generator`. They coexist.

---

## Behavior on re-invocation (CRITICAL — read first)

**Every time `/product-visual` is invoked, ALWAYS start from Step 1 (Select brand).** Do NOT continue from a prior state in the conversation. Do NOT re-use specs, briefs, output names, or any context from earlier generations in this chat. Each `/product-visual` invocation is a brand-new flow — fresh brand picker, fresh mode picker, fresh brief.

The iteration paths in Step 9 ("Regenerate same brief", "Adjust brief + regenerate", "Try a different mode") are conversational follow-ups within an already-running skill session — they fire WITHOUT the user re-typing `/product-visual`. The moment the user types `/product-visual` again, that's a hard reset → go back to Step 1.

---

## Step 1 — Select brand

Scan `./brands/` for subfolders containing a `brand-dna.md`:

```bash
find ./brands -maxdepth 2 -name "brand-dna.md" | sort
```

One match — use it and confirm. Multiple matches — list them and ask which one. None — point them to `/brand-dna-builder`. Ignore dotfiles like `.DS_Store`.

---

## Step 2 — Pick mode

Present the 7-mode picker as a markdown table (NOT a code block — let markdown render it cleanly):

| # | Mode | What it produces |
|---|---|---|
| 1 | Lifestyle scene | Product placed in a real-world setting — bathroom, kitchen, gym, café table, etc. |
| 2 | Closeup with hands | Intimate macro of fingertips / palm interacting with the product |
| 3 | Moodboard pin | Pinterest-style flat-lay with ingredient props arrayed around the product |
| 4 | Hero banner | Wide cinematic banner with empty space on one side for tagline copy |
| 5 | Virtual model tryout | A model holds or wears the product (optional brand character reference) |
| 6 | Conceptual product | Surreal CGI — floating / splash / dreamlike effects — the "wow" shot for campaigns |
| 7 | Restyle existing render | Take an image you've already generated and rewrite its aesthetic |

User picks ONE number. Map to the CLI mode string:

| # | User pick | CLI mode string |
|---|---|---|
| 1 | Lifestyle scene | `lifestyle_scene` |
| 2 | Closeup with hands | `closeup_product_with_person` |
| 3 | Moodboard pin | `moodboard_pin` |
| 4 | Hero banner | `hero_banner` |
| 5 | Virtual model tryout | `virtual_model_tryout` |
| 6 | Conceptual product | `conceptual_product` |
| 7 | Restyle existing render | `restyle` |

---

## Step 3 — Pick source image

**For modes 1–6** (everything except restyle):

Check `./brands/[brand]/studio-shots/` first. Studio shots are one level deep inside per-product subfolders. List any available PNGs and suggest using one — they give cleaner placements because the product is already isolated. If no studio shots exist, fall back to `./brands/[brand]/product-images/` and list those (raw scraped/manual product photos).

```bash
find ./brands/[brand]/studio-shots -maxdepth 2 -type f \( -name "*.png" -o -name "*.jpg" \) | sort
# falls back to:
find ./brands/[brand]/product-images -maxdepth 1 -type f \( -name "*.png" -o -name "*.jpg" \) | sort
```

User picks ONE file. Store its path as `product_image`.

**For mode 7 (restyle):**

Restyle works on an *existing rendered image*, not a raw product reference. Scan in this priority order:

1. `./brands/[brand]/product-visual/*/` — earlier `/product-visual` outputs (most relevant — the natural restyle source)
2. `./brands/[brand]/product-shots/*/` — `/product-shot-generator` outputs
3. `./brands/[brand]/studio-shots/*/` — `/studio-shot-generator` outputs
4. `./brands/[brand]/product-images/` — raw fallback (only if nothing else exists)

List options to the user grouped by source folder; let them pick. Store the picked file as `product_image`.

---

## Step 4 — Character reference (only for mode 5: virtual_model_tryout)

For all other modes, skip this step.

Scan `./brands/[brand]/characters/` for character subfolders. Each contains a `headshot.png` (used as the model identity reference).

- None found → skip (the backend picks a brand-appropriate model on its own)
- One found → ask "Use **[name]** as the model? (yes / no — backend picks)"
- Multiple found → list with names, ask "Which character should be the model? Or no — backend picks."

If user opts in, store `brands/[brand]/characters/[name]/headshot.png` as `character_image`. Otherwise leave it null.

The second `--image` reference makes the backend honor the identity (verified on Tatcha + sara during testing — face, hair, freckles transferred cleanly).

---

## Step 5 — Set default aspect ratio (silent — no user prompt)

Pick a sensible default per mode. **Do NOT ask the user** — the aspect ratio appears in the brief at Step 7 and the user can edit it there if they want a different ratio.

| Mode | Default |
|---|---|
| lifestyle_scene | `3:4` |
| closeup_product_with_person | `3:4` |
| moodboard_pin | `2:3` |
| hero_banner | `16:9` |
| virtual_model_tryout | `3:4` |
| conceptual_product | `3:4` |
| restyle | inherit from source image's aspect (if known, else `1:1`) |

Valid values for the brief's editable aspect ratio field: `1:1 / 4:3 / 3:4 / 16:9 / 9:16 / 3:2 / 2:3`.

**`4:5` is NOT accepted by the API.** If the user edits to `4:5`, silently remap to `3:4` (do NOT mention the remap to the user — it's internal).

Store the default as `aspect_ratio` in the spec for Step 7's brief.

---

## Step 6 — Auto-compose brand_context, product_context, and the intent prompt

This is where the system pulls from `brand-dna.md` + `product-dna.md` per the locked per-mode table below. The skill **assesses** the brand + product + mode and writes a fresh intent prompt — NOT a static template.

### Per-mode pull table (LOCKED — do NOT improvise)

| Mode | brand_context (3–5 lines) | product_context (3–5 lines) |
|---|---|---|
| lifestyle_scene | `Photography Style` (lighting + setting + mood) + `Identity` Voice line | `What it does` Tagline + top 3 from `Ingredients/materials` |
| closeup_product_with_person | `Photography Style` lighting + mood lines only (~10 words) | `What it does` Tagline only (texture cue) |
| moodboard_pin | `Identity` Voice line only | top 3 from `Ingredients/materials` + Tagline |
| hero_banner | `Photography Style` (lighting + setting + mood) + Voice | `What it does` Tagline only |
| virtual_model_tryout | `Photography Style` (lighting + setting + mood) + Voice | `What it does` Tagline only |
| conceptual_product | `Photography Style` (lighting + setting + mood) + Voice | (empty — concept-led) |
| restyle | `Identity` Voice line only | (empty — aesthetic-led) |

Read `brands/[brand]/brand-dna.md` and `brands/[brand]/product-dna/<slug>.md` (slug = `product_image`'s filename without extension). If product-dna doesn't exist, WARN the user: "No Product DNA found — context will be sparse. Output quality may suffer. Add via `/product-dna` first?" Let them proceed if they want.

### Compose ONLY the scene description

Claude writes ONE thing: a `scene_description` — a plain-language description of the shot (setting, composition, props, mood). ~15-30 words.

**Examples** (one per mode, to anchor the style):
- cleanser + lifestyle_scene → *"Sunlit bathroom counter, marble surface, soft morning daylight through a frosted window, small ceramic dish nearby."*
- energy drink + moodboard_pin → *"Performance lifestyle moodboard, modern editorial flat-lay aesthetic. Product centered as the hero anchor, ingredients arranged with clean negative space."*
- skincare + conceptual_product → *"Surreal floating product, weightless, ribbon of cream curling around it like calligraphy ink in air. Pale warm-cream atmospheric void."*

**The preservation directives (top-fronted, shape-lock, preservation tail) are INFRASTRUCTURE.** They live in `scripts/generate-product-visual.py` as locked constants and are auto-concatenated at fire time. Claude NEVER writes them — they're identical for every fire, every product type (tube, jar, jacket, watch, anything). Universal.

Store the scene description in the spec as the `scene_description` field. That's all Claude needs to compose for the prompt.

### CRITICAL prompt-writing rules (LOCKED)

- ❌ **NEVER describe the product's color, finish, or material in any string** (brand_context, product_context, OR the intent prompt). The reference image carries this. Words about color always drift the render.
- ❌ NEVER mention specific hex codes anywhere.
- ❌ NEVER paraphrase the product visually.
- ❌ For modes with a person involved (closeup, virtual_model_tryout): use EXPLICIT person language ("hand wrapped around", "fingertip touching", "model holding") — NEVER vague ("partially visible held above") which leaves the product floating.
- ❌ For modes that need ingredients to drive props (lifestyle, moodboard, hero_banner, conceptual): always pass top 3 ingredients from the `Ingredients/materials` section if available. Skip cleanly if the section is empty (manual product, no ingredients tracked).
- ✅ Mention specific scene props/contextual cues — those are where the backend adds richness without hurting fidelity.

---

## Step 7 — Show structured brief, loop on edits

Render the brief in chat **as plain markdown — NOT in a code block.** Code blocks make long context strings wrap awkwardly. Use bold labels + `·` separators for short fields, and let long fields (brand_context, product_context, intent_prompt) flow on their own lines with bold labels above them. Use `---` horizontal rules between sections.

The exact layout to render:

```markdown
## Generation Brief

**Mode** · [Mode label]
**Brand** · [brand name]
**Product** · [product name]
**Source image** · `[product_image path]`
**Character ref** · [character_image path or "none — backend picks"]

---

**Brand context** *(pulled from `brand-dna.md`)*
[brand_context string]

**Product context** *(pulled from `product-dna.md`)*
[product_context string]

---

**Scene description** *(your editable description of the shot)*
> [scene_description — plain language scene/setting/composition]

---

**Aspect ratio** · [3:4 / 16:9 / 2:3 / etc.]
**Estimated cost** · ~7 credits
```

> The preservation directives (replicate exactly, preserve proportions, do not substitute) are auto-attached behind the scenes — not shown in the brief. They're locked infrastructure, identical for every fire.

(The example above is shown inside a markdown code fence so you can see the exact characters to render. When you render it for the user, DROP the outer fence — render the markdown directly.)

**Then, on a plain chat line BELOW the brief:**

> Edit any field above (brand context, product context, scene description, aspect ratio…), or say **'go'** to generate.

Then wait. If the operator edits any field, recompose the brief with the updated value(s) and re-render. Loop until they say 'go'.

**Common edits to expect:**
- Aspect ratio change (e.g. `9:16` for socials, `1:1` for grid feed)
- Scene description rewrite (different setting, different scene direction)
- Brand context trim (operator wants less brand voice carryover)
- Product context trim (operator wants no ingredients pulled)

---

## Step 8 — Generate

1. Slug the output name: `[product-slug]-[mode-hint]` where:
   - `[product-slug]` = the source image filename without extension (e.g. `the-rice-wash.jpg` → `the-rice-wash`)
   - `[mode-hint]` = one of: `lifestyle`, `closeup`, `moodboard`, `hero`, `tryout`, `conceptual`, `restyle`

   Example: Rice Wash + lifestyle_scene → `the-rice-wash-lifestyle`. Same combination must always resolve to the same folder so re-runs auto-version (`_v1`, `_v2`, ...) inside it.

2. Create the output folder if missing:
   > `brands/[brand]/product-visual/[output-name]/`

3. Write `product-visual-spec.json` to that folder using EXACTLY this format:

```json
{
  "output_name": "the-rice-wash-lifestyle",
  "brand": "tatcha",
  "mode": "lifestyle_scene",
  "product_image": "brands/tatcha/product-images/the-rice-wash.jpg",
  "character_image": null,
  "aspect_ratio": "3:4",
  "brand_context": "Photography: soft daylight, cream/marble/linen surfaces, serene quiet-luxury mood. Voice: refined, ritual-minded.",
  "product_context": "Soft cream cleanser, pH-neutral foam. Key ingredients: rice ferment, Uji green tea, Okinawa algae.",
  "scene_description": "Sunlit bathroom counter, marble surface, soft morning daylight through a frosted window, single ceramic dish nearby."
}
```

`character_image` is null for all modes except `virtual_model_tryout` (when the user opted in at Step 4).

4. Run from the project root:
   ```bash
   python3 scripts/generate-product-visual.py brands/[brand]/product-visual/[output-name]
   ```

   The script silently resolves the source image (and optional character) through the existing UUID indexing — no re-upload if either was uploaded by another skill. It submits the photoshoot job and downloads the PNG.

5. **Exit codes the skill must handle:**
   - `0` → success. The script printed the saved path. Move to Step 9.
   - `2` → **NSFW.** Backend rejected the prompt. See the NSFW retry sub-step below.
   - any other non-zero → generic failure. Surface stderr to the user, ask if they want to manually edit the prompt and try again.

### NSFW retry sub-step (Step 8b)

If the script exited with code 2:

1. **Sanitize the intent prompt** by removing or softening these known trigger words from the prompt (NOT from brand_context or product_context):
   - `lathered`, `lathering` → `worked`
   - `fingertips` (when followed by "lathering" or "intimate") → just `fingers`
   - `intimate macro` → `studio macro`
   - `dewy`, `milky` (in scene description) → drop or replace with `soft`
   - `vanity` → `bathroom counter`
   - `sweat`, `sweat towel` → `linen towel`
   - `magnetic` → `confident`
   - `wrap around body` → `held in hand`
   - `water droplets on hands` → `cleanser foam in a small ceramic dish`

   Also add `"No person, no hands."` to the end of the intent prompt if the mode is `lifestyle_scene` (suppresses the auto-hand insertion that triggered the filter).

2. **Show the user the diff** — print the sanitized intent prompt with the changes highlighted (you can just print "Removed: '<word>' / Replaced: '<a>' → '<b>'"). Brief, one or two lines.

3. **Rewrite the spec** with the sanitized prompt and re-run the script ONCE.

4. If the retry also fails (any non-zero exit code), surface the failure clearly and offer the user the option to manually rewrite the prompt and try again. **Do NOT auto-retry a third time.**

---

## Step 9 — Confirm + iteration

The script prints the saved path on success. Confirm it back to the user:

> `brands/[brand]/product-visual/[output-name]/[output-name]_v1.png`

Ask: "Happy with the output? Regenerate (creates `_v2`), adjust the brief, try a different mode, or done?"

**Iteration paths:**
- **Regenerate same brief** → re-run the script. Auto-versions `_v2.png`, `_v3.png`, etc.
- **Adjust brief + regenerate** → loop back to Step 7, edit the brief inline, re-run.
- **Try a different mode** → loop back to Step 2 (same brand, possibly same product).
- **New product, same brand** → loop back to Step 3.
- **Done** → exit.

---

## Notes

- **The product-photoshoot endpoint is a two-stage internal pipeline** (mode-tuned prompt enhancer → `gpt_image_2` @ 2k). Our skill sends SMALL inputs (~75 words across brand_context + product_context + intent prompt); the backend amplifies into a ~1100-word structured photographer-style prompt before generating. KISS our inputs — the enhancer does the heavy lifting.
- **Color/finish fidelity is the known v1 limitation.** Subtle satin gradients (e.g. Tatcha Rice Wash) lose definition. Solid-color products (e.g. PYNK can, Dewy Skin Cream) render with near-perfect fidelity. For hyper-faithful clean studio shots use `/studio-shot-generator` instead.
- **NSFW filter is sensitive on skincare-adjacent intimate language.** Closeup mode on body-care products hits the filter ~30% of the time on first try. The Step 8b sanitize-and-retry is the mitigation. Two NSFW failures in a row = surface to the user; don't auto-retry indefinitely.
- **The shape-lock directive matters** — adding the height-to-width geometry line measurably improves proportional fidelity (verified on Tatcha Dewy Milk during testing). Always include in every intent prompt.
- **No `--resolution` or `--quality` flag** on product-photoshoot — the backend forces 2k. The skill does not surface these.
- **`count = 1` is hard-locked.** Operators iterate via `_v1` → `_v2` re-runs, not multi-variant batches.
- **UUID indexing reuses across skills.** First time a product image or character headshot is referenced by ANY skill, it's uploaded and a `.uuid` sidecar is written. Subsequent references (including from `/product-visual`) reuse the cached UUID — no double-upload. The skill output PNGs ALSO get a 2-line `.uuid` sidecar so they can become source images for the restyle mode or for other future skills.
- **Backend can take prop liberties.** It may add an extra prop the user didn't ask for (we saw an amber dropper bottle hallucinated in an early Tatcha lifestyle test). For total prop control either constrain harder in the intent prompt or use `/product-shot-generator` instead.
- **Studio shots are NOT replaced by this skill.** `/product-visual` is for product-in-a-context. `/studio-shot-generator` (raw `gpt_image_2` + crafted prompt) remains the right tool for clean-backdrop hero shots.

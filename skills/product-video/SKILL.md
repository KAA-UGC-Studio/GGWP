---
name: product-video
description: Run when the user wants a cinematic (non-UGC) product video — a product-motion hero film, a bold creative spot, a multi-scene brand spot, or a cinematic virtual try-on. Wraps Higgsfield Marketing Studio Video's four non-UGC modes. Auto-fills a lean, brand-DNA-derived brief that the operator reviews and edits; product entity and optional character avatar are resolved silently. Output saved as a versioned MP4 under the active brand folder.
---

# Product Video

Generates a cinematic Marketing Studio Video through Higgsfield — the **non-UGC** counterpart to `/ugc-content`. One skill, four modes. Each output is a versioned MP4 saved under `./brands/[brand-name]/product-video/[mode]/[output-name]/`.

This skill is for **product films and cinematic spots** (no talking-head). For talking-head / selfie UGC use `/ugc-content`. For still images use `/product-visual`. They coexist.

**Design philosophy (read first):** Higgsfield's backend enhances our brief into a full multi-cut screenplay server-side — it out-prompts us. So this skill practices **minimal creative interference**: it contributes only the facts it owns (which product, which character, the brand's look + voice) plus a short mode-correct starting line, then gets out of the way. The operator drives the creative. Keep our inputs short — over-specifying makes these modes hallucinate or stiffen.

**Prerequisites:**
- Brand DNA set up via `/brand-dna-builder`
- A product registered in `products.json` (URL-having or manual — both work)
- A character via `/character-creator` (optional — only for modes that use a person)

---

## Behavior on re-invocation (CRITICAL — read first)

**Every time `/product-video` is invoked, start from Step 1.** Do NOT continue from a prior state, reuse specs, briefs, or output names from earlier in the chat. Each invocation is a fresh flow. The iteration paths in Step 7 are conversational follow-ups within an already-running session — they fire WITHOUT the user re-typing `/product-video`. The moment they type `/product-video` again, hard reset to Step 1.

---

## Step 1 — Select brand

Scan `./brands/` for subfolders containing a `brand-dna.md`:

```bash
find ./brands -maxdepth 2 -name "brand-dna.md" | sort
```

One match — use it and confirm. Multiple — list and ask. None — point to `/brand-dna-builder`. Ignore dotfiles.

---

## Step 2 — Pick mode

Present the 4-mode picker as a markdown table:

| # | Mode | What it produces | Uses a person? |
|---|---|---|---|
| 1 | **Product Motion Film** | A hero shot where the camera and effects move dynamically around the product | No |
| 2 | **Creative Video Mode** | Our most experimental mode with the product as the hero of a bold creative moment | Optional |
| 3 | **Cinematic Brand Spot** | A short multi-scene commercial leading to an end card with your tagline | Optional |
| 4 | **Editorial Try-On** | A model wearing the product, shown from multiple angles inside one video | Recommended |

User picks ONE number. Map to the spec `mode` field (the script maps these to the CLI slug — do NOT pass the CLI slug yourself):

| # | User pick | spec `mode` | → CLI `--mode` (script) |
|---|---|---|---|
| 1 | Product Motion Film | `product_motion_film` | `product_showcase` |
| 2 | Creative Video Mode | `creative_video_mode` | `wild_card` |
| 3 | Cinematic Brand Spot | `cinematic_brand_spot` | `tv_spot` |
| 4 | Editorial Try-On | `editorial_tryon` | `virtual_try_on` |

> Editorial Try-On = the **Pro** virtual try-on (`virtual_try_on`), NOT the selfie `ugc_virtual_try_on` in `/ugc-content`. Don't confuse them.

---

## Step 3 — Select product

Check `./brands/[brand]/studio-shots/` first (cleaner placements), then fall back to `./brands/[brand]/product-images/`:

```bash
find ./brands/[brand]/studio-shots -maxdepth 2 -type f \( -name "*.png" -o -name "*.jpg" \) | sort
find ./brands/[brand]/product-images -maxdepth 1 -type f \( -name "*.png" -o -name "*.jpg" \) | sort
```

User picks ONE file → store as `product_image`. Read `brands/[brand]/product-dna/<slug>.md` if it exists (slug = filename without extension) for the Tagline / materials the brief pulls. If missing, warn that context will be sparse but allow proceeding.

> **Known limitation — single product image.** This skill passes ONE product image. For Editorial Try-On the un-shown side (e.g. a jacket's back) will be **hallucinated** by the backend. Tell the operator upfront for try-on. Multi-angle intake is a planned system change, not available yet.

---

## Step 4 — Model passthrough (per-mode)

Model use is mode-dependent. Default behavior:

| Mode | Default | Behavior |
|---|---|---|
| Product Motion Film | **No model** | Product only. Skip this step. |
| Creative Video Mode | **Optional** | Offer the character; default none. |
| Cinematic Brand Spot | **Optional** | Offer the character; default none. |
| Editorial Try-On | **Recommended** | Offer the character; if declined, Higgsfield auto-casts a model. |

When offering: scan `./brands/[brand]/characters/` for character subfolders. None → skip (backend casts its own). One → ask "Use **[name]** as the model? (yes / no)". Multiple → list and ask. If opted in, store `character_dir` as `brands/[brand]/characters/[name]` (the script resolves the headshot → avatar and fullbody → outfit-lock medias). Otherwise leave `character_dir` null.

---

## Step 5 — Compose the lean brief, show it with sources, loop on edits

Read `brands/[brand]/brand-dna.md` and the product-dna file. Compose the brief **lean** — short, factual, mode-correct. The system's job is identity + a starting stub, NOT creative direction.

### Per-slot derivation (LOCKED — keep it minimal)

| Slot | Pull from | Rule |
|---|---|---|
| **Setting** | brand-dna → Photography Style `Setting` (pick ONE short cue) | One location, editable. Never force-stack locations or over-describe. |
| **Action** | mode template + product name | A clean per-mode camera/structure line (see stubs). **No props, no mood/energy words, no metaphor** — Action is the shot direction; brand identity is carried by Setting + Mood + the product image. Abstract language and forced props make the backend hallucinate. |
| **Mood** | brand-dna → Identity `Voice` (≤3 adjectives) | Emotional tone only. **No color-grade jargon** (it tints the product and hurts label fidelity). |
| **Tagline** *(Cinematic Brand Spot only)* | product-dna → `Tagline` (verbatim) | The end-card line. |
| **Detail** *(Editorial Try-On only)* | product-dna → `Ingredients / materials` (one short cue) | True construction detail so closeups render right. Keep it short — long detail confuses the model. |

### Mode stubs for the Action slot (deliberately minimal)

- Product Motion Film → `dynamic camera move and effects around the [product]`
- Creative Video Mode → `[product] as the hero of a creative video`
- Cinematic Brand Spot → `lifestyle scenes with the [product], building to a clean end card`
- Editorial Try-On → `model wearing the [product]`

### CRITICAL brief rules (LOCKED)

- ❌ **Never describe the product's color, finish, or material** in any slot — the reference image carries it. (We do NOT add product-visual's "replicate exactly / preserve proportions" boilerplate here; Marketing Studio carries the product via the entity/medias.)
- ❌ **No mood/energy words or metaphor in Action** — keep it concrete physical action.
- ❌ **No color-grade language in Mood** — emotional adjectives only.
- ❌ Don't over-specify — short briefs out-perform long ones in these modes.
- ❌ No meta-narration or stage directions inside a slot (e.g. "no presenter", "uses no model") — slots hold scene content only.
- ✅ A short status line ("Building your brief from [brand]'s DNA…") is fine so the operator knows it's working — but no internal reasoning, no "skipping the model step", no "lean brief", no plumbing.

### Render the brief — present it CLEAN as two tables

A short status line is fine; **no source attributions** (never print which DNA field a line came from — that's tutorial material), no "lean", no repeating the mode/brand. Plain markdown. **All values are dynamic** — fill from the actual brand, product, character, and settings.

Two tables: a **Summary** (inputs/settings at a glance) and the **Brief** (the editable lines). Render this shape:

```markdown
**Summary**

| | |
|---|---|
| **Mode** | [Mode label] |
| **Brand** | [brand] |
| **Product** | [product name] |
| **Model** | [character name / none] |

**Brief** — edit any line, or say **go**

| | |
|---|---|
| **Setting** | [setting] |
| **Action** | [action] |
| **Mood** | [mood] |
[| **Tagline** | [tagline] |   ← Brand Spot only]
[| **Detail** | [detail] |   ← Try-On only]
| **Aspect** | [aspect] |
| **Duration** | [duration]s |
| **Resolution** | [resolution] |

~[N] credits
```

(Drop the outer fence when rendering.)

**Defaults:** aspect `9:16`, duration `8s`, resolution `1080p` (production floor; suggest `720p` for cheaper iteration), audio ON (locked, not shown).

**Valid aspect ratios:** `1:1 / 4:3 / 3:4 / 16:9 / 9:16 / 3:2 / 2:3`. `4:5` is NOT accepted — silently remapped to `3:4` (don't mention the remap). **Duration max is 15s** — the script clamps anything higher.

**Credit estimate** (audio on): 480p 3.5 cr/s · 720p 5 cr/s · 1080p 10 cr/s. (8s @ 1080p ≈ 80 cr.)

On any edit, recompose and re-render the **Brief** table. Loop until the operator says **go**.

---

## Step 6 — Generate

1. Slug the output name: `[product-slug]-[mode-hint]` where `[mode-hint]` ∈ `motion-film`, `creative`, `brand-spot`, `tryon`. (`[product-slug]` = product image filename without extension — never strip articles.) Same combination always resolves to the same folder so re-runs auto-version.

2. Create the folder if missing:
   > `brands/[brand]/product-video/[mode]/[output-name]/`
   (`[mode]` folder ∈ `product-motion-film`, `creative-video-mode`, `cinematic-brand-spot`, `editorial-tryon`.)

3. Write `product-video-spec.json` (EXACTLY this shape; unused slots are empty strings; `character_dir` null when no model):

```json
{
  "output_name": "pynk-energy-drink-motion-film",
  "brand": "pynk",
  "mode": "product_motion_film",
  "character_dir": null,
  "product_image": "brands/pynk/product-images/pynk-energy-drink.png",
  "setting": "gym floor, soft directional daylight",
  "action": "dynamic camera move and effects around the PYNK can",
  "mood": "premium, confident, magnetic",
  "tagline": "",
  "product_detail": "",
  "prompt": "Setting: gym floor, soft directional daylight. Action: dynamic camera move and effects around the PYNK can. Mood: premium, confident, magnetic.",
  "aspect_ratio": "9:16",
  "duration": 8,
  "resolution": "1080p",
  "generate_audio": true
}
```

The **brief slots are authoritative** — the script recomposes the prompt from them at run time (`"Setting: <s>. Action: <a>. Mood: <mo>."` + ` Tagline (end card): <t>.` for Brand Spot + ` Product detail: <d>.` for Try-On). The `prompt` field is written for transparency/logging; edits to slots take effect even if `prompt` isn't updated.

4. Tell the operator ONE clean line — e.g. *"Generating your [Mode] — ~[N] credits, takes a few minutes on Higgsfield…"* — then run from the project root:
   ```bash
   python3 scripts/generate-product-video.py brands/[brand]/product-video/[mode]/[output-name]
   ```
   The script resolves the product (URL entity or manual medias) + optional avatar/outfit-lock, recomposes the prompt from the brief slots, submits the job, waits for Higgsfield to render (the "few minutes" is the video generating server-side — not a local save), downloads the MP4, writes a `.uuid` sidecar.

   *Internal (NEVER narrate to the operator):* run one job at a time in the foreground; never background-batch (a long batch can hit a wall-clock limit and get killed mid-download). Folder creation, spec writing, and MP4 version-up (`_v2`, `_v3` on re-runs) are silent plumbing — never announce them, and never comment on or "override" a prior spec; just write the current one and let the MP4 auto-version.

5. **Exit codes** (handle generally — never special-case a specific product or word):
   - `0` → success (script printed the path; go to Step 7).
   - non-zero with **`nsfw`** in stderr → a known **false positive** from Higgsfield's filter (occurs occasionally even on clean product shots; nothing saved). **Do NOT auto-retry.** Tell the operator it was a likely false positive and **ask**: retry as-is, or tweak the wording? Run again only on their answer.
   - any other non-zero → likely a **transient server-side error** (e.g. Higgsfield HTTP 502/5xx), not a brief problem. **The job may have completed on Higgsfield even though nothing downloaded locally.** Tell the operator to check their Higgsfield library first — if the video is there it worked; grab it from there. Only re-run if it's genuinely not there.

**Hard rule — one `go` = exactly ONE generation.** Never start another run on your own — not for quality, not as a retry. A new generation happens ONLY when the operator explicitly asks for it (in Step 7, or after answering an NSFW prompt).

---

## Step 7 — Confirm + iteration

Confirm the saved path:
> `brands/[brand]/product-video/[mode]/[output-name]/[output-name]_v1.mp4`

Ask: "Happy with it? Regenerate (creates `_v2`), adjust the brief, try a different mode, or done?"

- **Regenerate** → re-run the script. Auto-versions `_v2.mp4`, etc. (Useful — these modes have high seed variance.)
- **Adjust brief** → edit the spec slots, re-run (the script recomposes the prompt from them).
- **Different mode** → back to Step 2.
- **Done** → exit.

---

## Notes & known limitations

- **The backend enhances server-side.** Our short brief becomes a multi-cut screenplay. Send minimal — over-specifying degrades output. This is the core reason briefs are lean.
- **Single product image → back/un-shown sides hallucinate.** Most visible in Editorial Try-On. Multi-angle intake is a planned system change; not available yet. Be honest with the operator.
- **Creative Video Mode is high-variance by design.** Keep the brief minimal and expect to regenerate; it's the "wild" mode. Abstract/metaphor language reliably breaks it (floating-product artifacts).
- **Color-grade language tints the product.** Keep Mood to emotional adjectives only; verified to help label/color fidelity.
- **Model passthrough reuses the `/ugc-content` mechanism:** headshot → Marketing Studio Avatar entity, fullbody → `--medias` outfit-lock. No image compositing.
- **Manual products (no URL)** are passed via `--medias` (the `products create` 405 workaround); URL-having products use the full product entity. Handled automatically by `resolve_product()`.
- **`marketing_studio_video` jobs don't appear in `generate list`** — if `--wait` is interrupted, the job still completes server-side; recover the result from the Higgsfield web dashboard.
- **Value framing (be honest in positioning):** this skill's edge over Higgsfield-direct is **on-brand volume** — wired product/character assets, enforced brand identity, organized versioned output across a catalog — NOT beating the raw tool on a single hero shot. For one-off maximum-control videos, the operator may prefer Higgsfield direct.
- **`count = 1` per run.** Operators iterate via `_v2`, `_v3` re-runs.

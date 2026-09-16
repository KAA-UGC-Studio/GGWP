---
name: product-shot-generator
description: Run when the user wants to place their product into a reference scene. Takes a scene reference and a product image, then generates a product shot via GPT Image 2. Two modes — Recreate places the product directly into the reference; Recompose has Claude analyze the reference scene and rebuild it around the product. Run this after the studio shot generator to get creative lifestyle-style product images.
---

# Product Shot Generator

Takes any image as a scene reference and places your product into it. Choose how the reference is used.

Input: a scene reference image + your product image (studio shot preferred)
Output: product shot saved to `brands/[brand]/product-shots/[output-name]/`

---

## Step 1 — Identify the brand

Run:
```bash
find ./brands -maxdepth 2 -name "brand-dna.md" | sort
```

Every brand returned is available — list all of them regardless of folder structure. Extract the brand name from the folder path only — do not read the contents of brand-dna.md at this step. If more than one exists, ask which brand to work with. If only one exists, use it automatically.

---

## Step 2 — Select product image

Check `brands/[brand]/studio-shots/` first. Studio shots are saved one level deep inside subfolders — look inside each subfolder for image files. If any exist, list them and suggest using one.

If no studio shots exist, fall back to `brands/[brand]/product-images/` and list what's available.

Wait for the user to select one.

---

## Step 3 — Select scene reference

Check `brands/[brand]/product-shots/scene-references/`. List any images already there — they carry over between runs and work for any product under this brand.

If the folder is empty or doesn't exist, create it:
```bash
mkdir -p brands/[brand]/product-shots/scene-references
```

Then prompt the user:

```
Add a scene reference to:
  brands/[brand]/product-shots/scene-references/

This image defines the visual world your product will be placed into.
Use anything — a lifestyle shot, a visual you admire, a screenshot from Pinterest.

Let me know once it's in there.
```

Wait for confirmation, then list what's in the folder and ask which one to use.

---

## Step 4 — Choose mode

Ask:

> "How should I use this reference?
>
> **Recreate** — places your product directly into the reference scene. Matches camera, lighting, and composition exactly.
>
> **Recompose** — Claude analyzes the reference scene and rebuilds it around your product."

---

## Step 5 — Recompose only: analyze and build prompt

**Skip this step for Recreate — go straight to Step 6.**

Write four layers. Each layer uses only the inputs listed for it.

**Layer 1 — Style Descriptor (80–110 words)**
Read the scene reference image and the product image. Use the scene reference to write the Style Descriptor to replicate the scene. Analyze the product image and use it to replace scene objects, surfaces, and details to reflect the product. Do not describe the appearance of the product itself in this layer.
Write one dense technical paragraph covering:
- Lighting: quality (hard/soft), direction, shadow and highlight behaviour
- Color & grade: temperature, saturation, dominant palette (be specific — not "warm" but "warm sand with slight pink undertone"), contrast, grade style
- Surface & background: exact material, finish, background type, props and how they're arranged
- Composition: camera angle, product placement, negative space
- Mood: 5 precise adjectives — never generic ("nice", "clean", "beautiful")

Ignore any text or copy visible in the reference — focus only on the visual scene.

**Layer 2 — Label text (under 60 words)**
Read: product image only
Transcribe every word, number, and logo on the product label — exact spelling, exact capitalisation, exact position on the label. Label text only — do not describe product color, shape, or finish.

**Layer 3 — Placement**
> "The attached product must appear in the scene with exact photographic fidelity — shape, proportions, surface finish, and all label text and branding must match precisely. Place it into the scene at the same angle, surface, and position as the original subject. Reproduce all text as written: same spelling, same weight, same position on the product."

**Layer 4 — Product protection**
> "The product's colors, label text, and branding must match the source exactly. Lighting on the product should adapt naturally to the scene."

Combine all four layers into the final prompt. Save it — this goes into shot-spec.json.

---

## Step 6 — Confirmation summary

```
Ready to generate:

  Product:   [selected image path]
  Scene:     [selected scene path]
  Mode:      [Recreate / Recompose]
  Notes:     [notes or "none"]
  Aspect:    [ratio] (default: 3:4)
  Output:    brands/[brand]/product-shots/[output-name]/

Confirm to generate, or adjust:
  "aspect [ratio]" — 1:1 · 9:16 · 3:4 · 16:9
  "notes [text]"   — add a specific request
```

Wait for the user to confirm or adjust before moving to Step 7.

Derive `[output-name]` from the product filename + scene filename — lowercase, hyphens (e.g. `pynk-can-hand-marble`). If the scene filename is a hash or otherwise non-descriptive, use `ref-[N]` instead (e.g. `pynk-gummies-ref-1`).

---

## Step 7 — Write shot-spec.json

Create the output folder:
```
brands/[brand]/product-shots/[output-name]/
```

Write `brands/[brand]/product-shots/[output-name]/shot-spec.json`:

```json
{
  "output_name": "[output-name]",
  "brand": "[brand]",
  "product_image": "brands/[brand]/studio-shots/[selected]/[file]",
  "scene_reference": "brands/[brand]/product-shots/scene-references/[file]",
  "aspect_ratio": "[chosen ratio]",
  "notes": "[notes or empty string]",
  "mode": "recreate",
  "prompt": ""
}
```

- `mode`: `"recreate"` or `"recompose"`
- `prompt`: empty string for recreate; full four-layer prompt for recompose

---

## Step 8 — Run the script

**Recreate:**
```bash
python3 scripts/generate-product-shot.py brands/[brand]/product-shots/[output-name]
```

**Recompose:**
```bash
python3 scripts/generate-brand-shot.py brands/[brand]/product-shots/[output-name]
```

---

## Step 9 — Report back

Show the output path, then ask:

```
Saved to: brands/[brand]/product-shots/[output-name]/[filename]

How does it look?
- **Keep it** — what would you like to do next?
- **Regenerate** — same spec, new variation
- **Adjust** — change the scene reference, mode, aspect ratio, or add notes
```

**If they say Keep it:** ask "What would you like to do next?"

**If they say Regenerate:** run the same script again — a new version is created automatically, nothing is overwritten.

**If they say Adjust:**
- Scene reference → drop a new image into `brands/[brand]/product-shots/scene-references/`, update `scene_reference` in shot-spec.json
- Mode → update `mode` in shot-spec.json; if switching to recompose, re-run Step 5 to build the prompt
- Aspect ratio → update `aspect_ratio` in shot-spec.json
- Notes → update `notes` in shot-spec.json

Then re-run the script.

---

## Notes

- Studio shots give cleaner placements — the model doesn't have to guess where the product ends and the background begins
- The scene-references folder is shared across all products under this brand — one good reference works for any product
- Recreate is faithful to the reference scene. Recompose rebuilds the scene from Claude's reading — results vary more between runs
- If the reference has people, hands, or props — they come through in the output. That's intentional
- Runs never overwrite. Each generation adds a new version: _v1 → _v2 → _v3

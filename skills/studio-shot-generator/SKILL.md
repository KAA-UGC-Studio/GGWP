---
name: studio-shot-generator
description: Run when the user wants a clean studio product shot from an existing photo. Takes any product image — iPhone photo, lifestyle shot, messy background — and generates a professional clean product image. Run this before the ad generator if the product image isn't clean enough to work with.
---

# Studio Shot Generator

Turns any product photo into a clean studio product image. Reads the reference image and applies a fixed render spec for consistent technical quality.

Input: any product image from `brands/[brand]/product-images/`
Output: clean studio shot saved to `brands/[brand]/studio-shots/[output-name]/`

---

## Step 1 — Identify the brand

Check `./brands/` for existing brands. If more than one exists, ask which brand to work with. If only one exists, use it automatically.

---

## Step 2 — Select the product image

List all images in `brands/[brand]/product-images/`. Present them to the user:

```
Which product image do you want to turn into a studio shot?

  1. [filename]
  2. [filename]
  ...
```

Wait for the user to select one. Then read the selected image using the Read tool — you need to visually analyse it.

---

## Step 3 — Build the prompt

### Prompt — do not modify

```
The reference image defines every detail of the product. Reproduce it without alteration — every colour, every surface, every text element, and every proportion must match the reference exactly as photographed. Do not alter any element of the product. Reproduce all text as written: same spelling, same weight, same position on the product.

Light the product with a single soft overhead source. Even coverage, no hard shadows.

Background: [BACKGROUND_PLACEHOLDER] — flat solid colour, no gradient, no texture, nothing bleeding in from the product.

Product centred and upright in the frame, with even space around it. No hands, no props, no studio equipment.
```

Replace `[BACKGROUND_PLACEHOLDER]` with the chosen background. This is the full prompt.

---

## Step 4 — Show confirmation summary

Present this before generating:

```
Ready to generate your studio shot:

  Product:     [selected filename]
  Background:  [chosen background] (default: clean white)
  Aspect:      [chosen ratio] (default: 1:1 — square)
  Output:      brands/[brand]/studio-shots/[output-name]/

Confirm to generate, or adjust first:
  "background [color or description]" — change background
  "aspect [ratio]" — options: 1:1, 9:16, 3:4, 16:9
```

Wait for the user to confirm or adjust. Apply any changes before moving to Step 5.

Derive `[output-name]` from the product filename — lowercase, hyphens (e.g. `classic-lotion-spf-30`).

---

## Step 5 — Write studio-shot-spec.json

Create the output folder:
```
brands/[brand]/studio-shots/[output-name]/
```

Write `brands/[brand]/studio-shots/[output-name]/studio-shot-spec.json`:

```json
{
  "output_name": "[output-name]",
  "brand": "[brand]",
  "product_image": "brands/[brand]/product-images/[selected-image]",
  "background": "[chosen background]",
  "aspect_ratio": "[chosen ratio]",
  "prompt": "[prompt with background filled in]"
}
```

---

## Step 6 — Run the script

```bash
python3 scripts/generate-studio-shot.py brands/[brand]/studio-shots/[output-name]
```

---

## Step 7 — Report back

Show the output path, then ask:

```
Saved to: brands/[brand]/studio-shots/[output-name]/[filename]

How does it look?
- **Keep it** — what would you like to do next?
- **Regenerate** — same spec, new variation
- **Adjust** — change background, aspect ratio, or add notes
```

**If they say Keep it:** ask "What would you like to do next?"

**If they say Regenerate:** run the script again — a new version is created automatically:
```
python3 scripts/generate-studio-shot.py brands/[brand]/studio-shots/[output-name]
```

**If they say Adjust:**
- Background → update `background` in `studio-shot-spec.json`
- Aspect ratio → update `aspect_ratio` in `studio-shot-spec.json`
- Notes → add to the `prompt` field in `studio-shot-spec.json`

Then re-run the script.

---

## Notes

- GPT Image 2 text rendering varies between runs — if text comes out wrong, just regenerate.
- Each run auto-increments — [output-name]_v1.png → v2 → v3 — no output is ever overwritten.

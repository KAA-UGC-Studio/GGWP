---
name: character-creator
description: Run when the user wants to create a character, generate a model, or build a casting digital. Collects physical characteristics (from brand DNA, from a reference photo, or by hand), generates a headshot, a full-body casting digital and a six-angle face sheet via the Higgsfield CLI, and saves them under the active brand folder. Output is a matched set ready for outfit, shoot and video workflows.
---

# Character Creator

Generates a matched casting set for a brand character.

Three images are produced:
1. **Headshot** — tight casting portrait, straight-on, clinical studio lighting
2. **Full body** — full-length casting digital using the headshot as face reference
3. **Angle sheet** — six head-and-shoulders angles in one grid, using the headshot as face reference

All saved to `./brands/[brand-name]/characters/[character-name]/`.

The angle sheet is what keeps a face consistent when a video model turns the character's head — video skills upload it alongside the headshot. It costs ~$0.12 and is on by default.

---

## Step 1 — Select brand

Open `./brands/` and check for subfolders containing a `brand-dna.md` file. One match — use it and confirm the brand name. Several matches — list them and ask which to work with. None — brand setup hasn't been done yet, point them to `/brand-dna-builder`.

---

## Step 2 — Choose how to build the character

Ask in one message:

> "How would you like to build this character?
>
> **1 — Auto:** I read your brand DNA and propose a character that fits the brand.
> **2 — From a reference photo:** you give me a photo, and I either build a similar-looking new person from it, or lock the character to that exact face.
> **3 — Manual:** you fill in the characteristics form yourself."

If no `brand-dna.md` exists, option 1 is unavailable — offer 2 and 3.

### Path 1 — Auto

Read `brand-dna.md`, analyse the brand's target audience, positioning and mood, then fill out a complete character sheet that fits the brand. Present it for review and ask if they want to adjust anything before proceeding.

### Path 2 — From a reference photo

Ask for the photo's path (or let them drop it into the character folder). Then ask which of the two modes they want — the difference matters:

> "Two ways to use this photo:
>
> **A — Inspired by (default):** I read the photo's features and generate a **new person** who looks similar. No one's likeness is copied.
> **B — Face-lock:** the character **is** the person in the photo. Because their real likeness ends up in ads, I need to record their consent first."

**Mode A — Inspired by:**
1. Look at the photo and fill in the characteristics form (Step 3's fields) from what you see.
2. Show the filled form and say plainly which values came from the photo and which you inferred.
3. Let the user edit, then continue to Step 4.
4. Copy the photo into the character folder as `reference.[ext]` and set `reference_mode: "inspired"` in the spec. The script does **not** pass it to the model — it's kept as provenance.

**Mode B — Face-lock:**
1. Ask the consent questions and record the answers verbatim:
   - Who is the person, and what is their relationship to the brand?
   - Have they agreed to their likeness being used in this brand's ads? (a verbal yes is enough to proceed — a written release is better)
   - Any limits on scope or time?
   - Do we have the rights to the photo itself (was it taken by or for us, rather than pulled from social media)?
2. Copy the photo into the character folder as `reference.[ext]`.
3. Set `reference_mode: "face_lock"`, `reference_image: "reference.[ext]"` and the `consent` block in the spec (format in Step 5).
4. Fill in the characteristics form from the photo as in Mode A — the prompt still needs it.

**The person in a reference *video* is never face-locked.** If the user wants a character like the creator in a video they're cloning, use Mode A and describe only the casting type (age range, styling, energy), not that individual.

Without consent recorded, `generate-character.py` refuses to run in face-lock mode. That refusal is the guardrail — don't work around it by pasting the photo in some other way.

### Path 3 — Manual

Go to Step 3.

---

## Step 3 — Collect characteristics

Ask the user for all of the following in one grouped message. Copy the form below exactly as written — do not reformat, reword, or remove the examples.

```
Let's build your character. Fill in what applies — leave anything blank that doesn't fit:

IDENTITY
Age:
Gender:
Nationality:

FACE
Skin tone:
Jawline:
Face shape:
Eye shape:
Eye colour:
Eyebrows:
Nose:
Lips:
Facial hair:
Freckles / skin details:
Cheekbones:

HAIR
Colour:
Style:

BUILD
Height:
Body type:

CLOTHING
Top:         (e.g. White oversized hoodie)
Bottom:      (e.g. Blue jeans)
Shoes:       (e.g. White Air Force 1s)
Accessories: (e.g. Gold chain, black cap)

LOOK
Tone:        (e.g. Raw and authentic, polished editorial, sporty, luxury, street)
```

Confirm the full list back to the user before proceeding. Ask if they want to change anything before generating. If clothing fields are left blank, use the defaults silently — do not ask about or mention any other skill.

---

## Step 4 — Name the character

Ask: "What would you like to name this character? This becomes the folder name — e.g. `sofia`, `kai`, `brand-hero`."

Slug the name: lowercase, hyphens, no spaces or special characters.

---

## Step 5 — Write character-spec.json

Create the folder and write the spec file:

```
brands/[brand-name]/characters/[character-name]/
  character-spec.json
  characteristics.md
  reference.[ext]          (only when Step 2 Path 2 was used)
```

**character-spec.json — use EXACTLY this format:**
```json
{
  "character_name": "[character-name]",
  "brand": "[brand-name]",
  "characteristics": "Age: 28\nGender: Male\nNationality: Brazilian\nSkin tone: Deep warm brown\nFace shape: Square\nJawline: Strong\nEye shape: Deep-set\nEye colour: Dark brown\nEyebrows: Thick, natural\nNose: Broad, straight\nLips: Medium, defined\nHair colour: Black\nHair style: Short, low fade\nHeight: Tall\nBody type: Athletic\nTone: Raw and authentic",
  "top": "Black heavyweight tee",
  "bottom": "Cargo trousers, olive",
  "shoes": "Chunky white trainers",
  "accessories": "Silver ring"
}
```

Write characteristics as a single string — one `Key: Value` entry per line. Only include fields that were filled in.

**When a reference photo was used**, add these fields:
```json
  "reference_image": "reference.webp",
  "reference_mode": "inspired"
```

**Face-lock only** — `reference_mode` is `"face_lock"` and a consent block is required:
```json
  "reference_mode": "face_lock",
  "consent": {
    "likeness": "real person — face-locked to reference.webp",
    "status": "verbal — confirmed by user 2026-09-12, written release pending",
    "release_file": null,
    "scope": null,
    "expires": null,
    "photo_rights": "unconfirmed — reference is a social-media selfie; get a direct photo from the talent"
  }
```
`status` must say what kind of consent and on what date. The script refuses to run when it's empty.

**characteristics.md** — a readable reference version of the same data:
```markdown
# [Character Name] — Characteristics

## Demographics
Age:
Sex:
Ethnicity:

## Physical features
Skin tone:
Face shape:
...

## Hair
Colour:
Style:

## Build
Height:
Body type:

## Aesthetic
Tone:
```

---

## Step 6 — Generate

Run from the project root:

```bash
python3 scripts/generate-character.py brands/[brand-name]/characters/[character-name]
```

This runs three Higgsfield CLI calls (model: `nano_banana_2`):
1. Headshot — text-to-image, 2K, 3:4 (image-reference when face-locked)
2. Full body — image-reference edit, 2K, 3:4, using the headshot's job UUID as the face reference
3. Angle sheet — image-reference edit, 2K, 9:16, six angles in one grid

Cost: ~$0.36 total.

Flags:
- `--no-multiangle` — headshot + full body only (~$0.24)
- `--multiangle-only` — just the angle sheet, from an existing `headshot.png`. Use this to add a sheet to a character made before angle sheets existed (~$0.12)

---

## Step 7 — Present results

Once generation completes, confirm the save paths:
- `brands/[brand-name]/characters/[character-name]/headshot.png`
- `brands/[brand-name]/characters/[character-name]/fullbody.png`
- `brands/[brand-name]/characters/[character-name]/multiangle.png`

Check the angle sheet before handing it on: all six panels must be the same person, with the same hair and top, on the same background. Profile and ¾ panels are where a face drifts — if one panel is off, regenerate the sheet with `--multiangle-only` rather than redoing the whole character.

Ask: "Happy with this character? Or would you like to regenerate or adjust the characteristics?"

Once confirmed, ask:

> "What would you like to do next?"

---

## Iteration

**Regenerate with same characteristics:**
Run the script again — overwrites headshot.png and fullbody.png, and adds a new `multiangle_v2.png`.

**Adjust characteristics and regenerate:**
1. Ask which characteristics to change
2. Update character-spec.json and characteristics.md
3. Re-run the script

**Angle sheet only:** `--multiangle-only`. Each run adds the next version (`multiangle_v2.png`, `_v3.png`, …) and never overwrites. Downstream skills read the highest version.

**Note:** Full body always regenerates together with the headshot — the full body uses the headshot as face reference, so both need to match.

---

## Notes

- Characters are brand-specific — each brand has its own `characters/` subfolder
- Multiple characters per brand are fine: `characters/jade/`, `characters/marcus/`
- Characters are reused across all downstream skills — outfit-changer, location-changer, product shots, `/ugc-clone`, `/ugc-content`
- The angle sheet is a grid of 2 columns × 3 rows: front at eye level, ¾ turned each way, a tighter front from slightly below, a full side profile, and a front with a slight head turn. Video models that accept several references (Kling 3.0 Omni, Seedance) hold a face far better when the sheet's panels go in alongside the headshot
- Auth issues from the generation script almost always mean Higgsfield CLI auth has expired — run `higgsfield auth login` before anything else

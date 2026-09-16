---
name: ugc-studio
description: Run when the user wants the whole pipeline in one go — "bikin UGC dari nol", "set up brand and make a video", "clone this video for my brand" — instead of running /brand-dna-builder, /product-dna, /character-creator and a video skill one by one. Chains the existing skills in order, reusing whatever is already set up, and finishes on either /ugc-clone (prompts from a reference video) or /ugc-content (Higgsfield generation).
---

# UGC Studio

One run, start to finish: brand → product → character → video. Each step is an existing skill; this one drives them in order and skips what's already done.

**How this skill works:** at each step, read that skill's own `SKILL.md` and follow it exactly. The one thing to override is its ending — a sub-skill that says "Next: run `/product-dna`" has done its job here, so continue to the next step instead of stopping. Never re-ask for something an earlier step already established.

---

## Step 1 — What are we making?

Ask first, because it changes the order of everything else:

```
What are we making?

  1. Clone a reference video   — you have a video you want remade with your brand.
                                 Ends with prompts to paste. Nothing is generated.
  2. UGC video (Higgsfield)    — brief-driven video, generated via Marketing Studio.
```

Note for path 1: the reference is analyzed after the character exists, so mention it — if the user wants the character cast to match the video's creator, they can say so at Step 4 and describe the type by hand.

---

## Step 2 — Brand

Check `./brands/` for subfolders with a `brand-dna.md`.

- **None** → run `/brand-dna-builder` (follow `skills/brand-dna-builder/SKILL.md`). It ends by writing `products.json`; continue to Step 3 rather than stopping.
- **One or more** → list them and ask:
  ```
  Brands set up:
    1. skin1004
    2. saturdays
  Use one of these, update it, or add a new brand?
  ```
  Update or add → run `/brand-dna-builder`. Otherwise read `brand-dna.md` and move on.

---

## Step 3 — Product

Read `brands/[brand]/products.json` and list the products, marking which already have `product-dna/<slug>.md`:

```
Which product is this video for?

  1. Poremizing Light Gel Cream     ← DNA ready
  2. Centella Ampoule               ← no DNA yet
  3. + Add a new product
```

- **DNA exists** → read it and continue.
- **No DNA, or a new product** → run `/product-dna` for that one product (follow `skills/product-dna/SKILL.md`). Auto-fills from `page_url` when there is one. Then continue — don't stop at its "Next:" block.
- **User wants to skip the DNA** → ask three questions (category, two main benefits, call to action), save a minimal DNA file marked ⚠️, and say that the copy will be thinner for it.

One product per run. Others can be set up later with `/product-dna`.

---

## Step 4 — Character

Look in `brands/[brand]/characters/`:

```
Character for this video?

  1. kirana        (existing)
  2. + Create a new character
  3. Skip — hands-only or product-only video
```

- **Existing** → read `character-spec.json`. If there's no `multiangle*.png`, offer the angle sheet:
  > "No angle sheet for this character. Video models hold a face much better with one. Generate it? ~$0.12"
  > `python3 scripts/generate-character.py brands/[brand]/characters/[name] --multiangle-only`
- **New** → run `/character-creator` (follow `skills/character-creator/SKILL.md`). All three of its Step-2 paths apply — Auto from brand DNA, from a reference photo, or manual. For path 1 of Step 1, a character that matches the reference video's creator type can be described by hand here.
- **Skip** → fine for unboxing and product demos. `/ugc-clone` will ask for a character later if the reference turns out to have a face.

---

## Step 5 — Run the chosen path

**Path 1 — Clone a reference video:** follow `skills/ugc-clone/SKILL.md` from its **Step 4** (brand, product and character are already resolved). It runs its own two gates and ends with prompt files. **Nothing is generated.**

**Path 2 — UGC video (Higgsfield):** follow `skills/ugc-content/SKILL.md` from its **Step 4** (the mode picker). It generates an MP4 through Marketing Studio.

---

## Step 6 — Offer the other path

Once the chosen path finishes:

> "Done. Want to also [clone a reference video / make a Higgsfield UGC video] with the same brand, product and character?"

Yes → run the other path from Step 5, reusing everything. No → stop, listing what was produced and where it is.

---

## Notes

- **Reuse is the point.** Never rebuild brand DNA, product DNA or a character that already exists — offer to use, update, or add.
- **Sub-skills stay the source of truth.** Read their `SKILL.md` at run time; never copy their steps into this file. A fix to `/character-creator` reaches this skill automatically.
- **Only the handoff lines are overridden** — the "Next: run /x" endings. Every other instruction in a sub-skill is followed exactly, including its approval gates and preview blocks.
- **kie.ai is not a path here.** `/ugc-content-kie` is run on its own when Higgsfield is out of credits.
- Each step's outputs land in the usual places: `brands/[brand]/brand-dna.md`, `product-dna/`, `characters/`, `ugc-clone/`, `ugc-content/`.

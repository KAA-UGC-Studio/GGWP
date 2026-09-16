---
name: ad-generator
description: Run when the user wants to generate static ads. Shows 40 ad format templates (headline, offer, testimonial, us-vs-them, UGC, pull-quote, faux-press, stat radial, manifesto, and more). User picks which templates to run, Claude fills each with brand-specific details from brand-dna.md, generates one ad per template via GPT Image 2 or Banana 2. Run after studio-shot-generator or product-shot-generator to use the best product image as input.
---

# Ad Generator

Pick from 40 battle-tested ad templates. Claude fills each with your brand DNA and generates one image per template.

Input: product image + brand-dna.md
Output: one ad per selected template, saved to `brands/[brand]/advertisements/[product-slug]_[timestamp]/`

---

## Step 1 — Detect brand

Run:
```bash
find ./brands -maxdepth 2 -name "brand-dna.md" | sort
```

Extract brand name from folder path only. If one brand found, use it automatically. If multiple, ask which one.

Read `brands/[brand]/brand-dna.md` in full. Extract and store:
- **Color system** — primary, support, accent, background colors with hex values and roles
- **Typography rules** — weight, case, scale, treatment for ads
- **Brand voice** — "Sounds like" and "Never" lines for writing headlines

---

## Step 2 — Select product image

Run:
```bash
find brands/[brand]/studio-shots -maxdepth 2 \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) | sort
```

If studio shots found, display a numbered list using the folder name as the product name:
```
Studio shots available:

  1. [folder name]
  2. [folder name]
  ...

Which product? Pick a number — or say "product images" to browse product-images/ instead.
```

If none found, check product images:
```bash
find brands/[brand]/product-images -maxdepth 1 \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) | sort
```

If product images found, display a numbered list using the filename (without extension) as the name:
```
Product images available:

  1. [filename without extension]
  2. [filename without extension]
  ...

Which product? Pick a number.
```

Store the full path internally — only show names to the user.

Always ask and wait — even if only one image is found. Never auto-select.

Wait for the user to select one before proceeding.

**Load product-dna alongside brand-dna:**

Once the product is selected, derive its slug from the product image filename (no extension). Read `brands/[brand]/product-dna/<slug>.md` if it exists. Hold both `brand-dna.md` (loaded in Step 1) and `product-dna.md` as live context for Steps 3.5 and 4. If `product-dna.md` doesn't exist for this product, proceed with brand-dna only.

---

## Step 3 — Show template menu

Read `skills/ad-generator/templates.md`. For each template, extract the aspect ratio from the end of its template text. Display the full numbered list with name, ratio, and one-line description:

```
40 ad templates available:

  1.  Headline                         3:4   — Tests text rendering. Clean model output check.
  2.  Offer/Promotion                  9:16  — The money-maker. Test your core offer.
  3.  Testimonials                     9:16  — Real environments + text overlays.
  4.  Features/Benefits Point-Out      3:4   — Educational diagram-style layout.
  5.  Bullet-Points                    3:4   — Split composition. Product left, benefits right.
  6.  Social Proof                     3:4   — Member count + review card + press logos.
  7.  Us vs Them                       3:4   — Side-by-side comparison.
  8.  Before & After (UGC Native)      9:16  — Mirror selfie transformation.
  9.  Negative Marketing (Bait&Switch) 3:4   — Fake bad review that's actually a rave.
  10. Press/Editorial                  3:4   — Authority play. Vogue back-page energy.
  11. Pull-Quote Review Card           3:4   — Emotional quote over a review card.
  12. Lifestyle Action + Colorway      1:1   — Action hero shot + product lineup.
  13. Stat Surround / Callout Radial   1:1   — Product as hero, stats as planets.
  14. Bundle Showcase + Benefit Bar    1:1   — Product feature with benefit bar.
  15. Social Comment Screenshot        1:1   — Screenshotted comment = instant credibility.
  16. Curiosity Gap / Hook Quote       1:1   — Provocative headline forces the double-take.
  17. Verified Review Card             1:1   — Mimics real review platform UI.
  18. Stat Radial (Lifestyle Flatlay)  1:1   — Same as #13 but lifestyle background.
  19. Highlighted Testimonial          1:1   — Long-form review with highlighted phrases.
  20. Advertorial / Editorial Card     3:4   — Looks like a news post, not an ad.
  21. Bold Statement / Reaction        1:1   — Pure brand energy. Copy IS the ad.
  22. Flavor Story / "Tastes Like"     3:4   — Full-bleed food scene + product.
  23. Long-Form Manifesto              3:4   — Copy-dominant. The writing is the creative.
  24. Product + Comment Callout        3:4   — Product above a faux Facebook comment.
  25. Us vs Them Color Split           3:4   — Vivid split with checkmarks vs X marks.
  26. Stat Callout (Data-Driven)       3:4   — Statistic-led with lifestyle background.
  27. Benefit Checklist Showcase       3:4   — Product shot + benefit rows + CTA.
  28. Feature Arrow Callout            3:4   — Hand holding product with outward callouts.
  29. UGC + Viral Post Overlay         9:16  — Selfie with a Reddit/X post screenshotted.
  30. Hero Statement + Icon Bar        3:4   — Power statement + three icon benefits.
  31. Comparison Grid / Table          1:1   — Meme-style head-to-head comparison grid.
  32. UGC Story Callout                9:16  — iPhone Story with text bubble annotations.
  33. Faux Press / News Screenshot     3:4   — Looks like a real online article.
  34. Faux iPhone Notes                3:4   — iOS Notes app screenshot aesthetic.
  35. Hero Product + Stat Bar          3:4   — Superlative headline + product + stat strip.
  36. Whiteboard Before/After          3:4   — Real person photo + whiteboard drawing.
  37. Hero Statement + Offer Burst     3:4   — Promo variant with discount starburst.
  38. UGC Lifestyle + Review (Split)   3:4   — Casual photo left, product + review right.
  39. Curiosity Gap Scroll-Stopper     1:1   — Hook headline + problem photo. No product.
  40. Native Post-It Note Style        3:4   — Lifestyle photo with handwritten post-it.

Aspect ratios are locked — layouts are built for their format and changing them breaks the composition.

Which templates do you want to run? Enter numbers separated by commas — e.g. "1, 7, 11"
```

Wait for selection.

---

## Step 3.5 — Campaign Brief

For each selected template, generate an auto-suggestion for the copy that will appear on the ad — the text a viewer would read (headline, offer, benefits list, quote, stats). Show all selected templates at once in one message, with the auto-suggestion and one question per template.

**Source-of-truth principle for auto-suggestions:**

Fill each slot from the right source based on what the slot wants:
- **Brand-level slots** (voice, tone, identity, colors) draw from `brand-dna.md` — especially the Voice in Practice section for headlines, subheads, and offer copy
- **Product-level slots** (claims, benefits, ingredients, stats, taglines, positioning, comparisons) draw from `product-dna.md`

Read the template's prompt text to understand the slot's length and format hints (e.g. `"under 10 words"`, `"[BENEFIT 1-N]"`, `"4-6 lines"`, `"2-3 SENTENCE REVIEW"`), and fit the chosen DNA content to those hints. Don't force product-dna data into slots where it doesn't fit (e.g. descriptive ingredients into numeric stat slots — invent + ⚠️ instead).

Only invent + ⚠️ when **neither** DNA has the answer (real review counts, customer names, real press coverage, specific stats not in product-dna).

**Display format — show ALL text elements that will appear on the ad:**

Open with this intro line, replacing `[brand]` and `[product]` with the actual names:
> "Here's the campaign brief — filled from `[brand]` brand-dna and `[product]` product-dna. Items marked ⚠️ are invented because neither DNA had the info. Say 'go' to generate, or change anything."

Then show each template's slots:

```
[4] Features/Benefits  ·  3:4
    Headline:  "WHAT MAKES [BRAND] DIFFERENT"
    Claims:    "ZERO CRASH · CLEAN ENERGY · BOLD PACKAGING · ELECTRIC TASTE"
    → ⚠️ Real product facts? (numbers, ingredients, specs from your product)

[6] Social Proof  ·  3:4
    Headline:  "JOIN 500,000+ WHO [BENEFIT]."
    Rating:    "Rated 4.9 out of 5"
    Review:    "[2–3 sentence quote]"
    → ⚠️ Real member count + rating? Real quote?

[13] Stat Radial  ·  1:1
    Headline:  "[Brand benefit headline]"
    Stats:     "97% · #1 BESTSELLER · 500K+ REVIEWS · [KEY INGREDIENT]"
    → ⚠️ Real stats? (I'll use non-specific language if not)

[7] Us vs Them  ·  3:4
    Headline:    "PYNK VS THE REST"
    Weaknesses:  "CHEMICAL AFTERTASTE · BRUTAL SUGAR CRASH · FORGETTABLE PACKAGING"
    Strengths:   "ELECTRIC CLEAN TASTE · ZERO CRASH · IMPOSSIBLE TO IGNORE"
    → Who's your competitor? What do you actually beat them on?

[1] Headline  ·  3:4
    Headline:  "YOUR ENERGY, LOUDER."
    Subline:   "The can that refuses to blend in."
    → Different angle?
```

Rules:
- Show ALL text elements per template — every piece of text a viewer will read
- Use the correct label for each element: `Headline:`, `Subline:`, `Claims:`, `Stats:`, `Rating:`, `Review:`, `Quote:`, `Attribution:`, `Offer:`, `CTA:`, `Weaknesses:`, `Strengths:`, `Publications:`, `Copy:`
- Every element must be filled with a complete suggestion — never leave `[BRACKETED PLACEHOLDERS]` in the brief. If you don't have real data, invent a plausible value and flag it ⚠️ (e.g. `"180MG CAFFEINE ⚠️"`, `"4.8 out of 5 ⚠️"`, `"20% OFF ⚠️"`)
- Use ⚠️ for any element that contains invented numbers, stats, claims, names, or quotes that need to be real
- No ⚠️ for pure brand voice copy (headlines from "Sounds like", lifestyle descriptions)
- Never remove a template element because you don't have real data — always suggest and flag ⚠️ instead
- If user says "go" without correcting a ⚠️ item, use the suggested value in the spec as-is
- One-word answers work: "Red Bull" fills Us vs Them; "yes" approves everything
- User says "go" to accept all and proceed

Wait for one response covering all templates, then proceed to Step 4.

**Question per template — all 40:**

| # | Template | ⚠️ | Question |
|---|----------|----|----------|
| 1 | Headline | — | Different angle? |
| 2 | Offer/Promotion | ⚠️ | Real offer? Discount code? Deadline? |
| 3 | Testimonials | — | Real quote or specific customer type? |
| 4 | Features/Benefits | ⚠️ | Real product facts? (numbers, ingredients, specs) |
| 5 | Bullet-Points | — | Top 5 benefits to list? |
| 6 | Social Proof | ⚠️ | Real member count + rating? (falls back to non-specific if not) |
| 7 | Us vs Them | — | Who's your competitor? What do you beat them on? |
| 8 | Before & After (UGC) | — | What transformation does your product deliver? |
| 9 | Negative Marketing | — | What criticism do you want to flip? |
| 10 | Press/Editorial | ⚠️ | Real press coverage? Only use publication names where you have actual coverage. |
| 11 | Pull-Quote Review Card | — | Real review language to draw from? |
| 12 | Lifestyle Action + Colorway | — | Specific colorways or SKUs in the lineup? |
| 13 | Stat Surround / Callout Radial | ⚠️ | Real stats to use? |
| 14 | Bundle Showcase + Benefit Bar | ⚠️ | Real bundle? Which products? |
| 15 | Social Comment Screenshot | — | Specific sentiment or real comment? |
| 16 | Curiosity Gap / Hook Quote | ⚠️ | Specific hook? Real review/star count to include — or skip social proof? |
| 17 | Verified Review Card | — | Real review or approved language? |
| 18 | Stat Radial (Lifestyle Flatlay) | ⚠️ | Real stats? |
| 19 | Highlighted Testimonial | — | Real review or approved sentiment to highlight? |
| 20 | Advertorial / Editorial Card | — | Editorial angle — what story do you want told? |
| 21 | Bold Statement / Reaction | — | Any specific line you want to land? |
| 22 | Flavor Story / "Tastes Like" | ⚠️ | Real stats for the bottom bar (calories, caffeine, sugar)? Suggest plausible values if not — user confirms. |
| 23 | Long-Form Manifesto | — | What does your brand believe that others don't? |
| 24 | Product + Comment Callout | — | What does the comment say? |
| 25 | Us vs Them Color Split | — | Competitor + what you beat them on? |
| 26 | Stat Callout (Data-Driven) | ⚠️ | Real number to lead with? |
| 27 | Benefit Checklist Showcase | ⚠️ | Real rating + review count? Suggest plausible values if not — user confirms. |
| 28 | Feature Arrow Callout | ⚠️ | Real product features to point to? |
| 29 | UGC + Viral Post Overlay | — | What does the Reddit/X post say? |
| 30 | Hero Statement + Icon Bar | — | Statement + 3 benefits to feature as icons? |
| 31 | Comparison Grid / Table | — | Which brands in the grid? Your wins vs. theirs? |
| 32 | UGC Story Callout | — | What's the person experiencing/saying? |
| 33 | Faux Press / News Screenshot | — | Faux publication names and headlines are part of the format — no real coverage needed. Different headline angle? |
| 34 | Faux iPhone Notes | — | What's written in the Notes screenshot? |
| 35 | Hero Product + Stat Bar | ⚠️ | Real superlative claim + stats? |
| 36 | Whiteboard Before/After | — | What's on the whiteboard? Before/after labels? |
| 37 | Hero Statement + Offer Burst | ⚠️ | Real promo? Discount + deadline? |
| 38 | UGC Lifestyle + Review (Split) | — | Real or approved review copy? |
| 39 | Curiosity Gap Scroll-Stopper | — | Hook + what problem/question to show? |
| 40 | Native Post-It Note Style | — | What does the post-it say? |

---

## Step 4 — Fill selected templates

For each selected template, read its full text from `skills/ad-generator/templates.md` and replace every `[BRACKETED PLACEHOLDER]` with brand-specific details:

**From brand-dna.md:**
- `[BRAND]` → brand name
- `[PRIMARY BRAND COLOR]` → primary color name + hex
- `[CONTRAST COLOR]` → choose a color from brand palette that contrasts the primary
- `[BACKGROUND]` → background color from brand color system
- `[TEXT COLOR]` / `[CONTRAST TEXT]` → apply contrast rule below
- `[BRAND COLOR]` references throughout → use appropriate brand palette color per context
- Ignore the Generation Modifier section — it applies to studio shots only

**Contrast rule — always enforce:**
- Light or pale background → text must be dark (black or deep brand color). Never white on light.
- Dark background → text must be white or light. Never dark on dark.
- State the chosen text color explicitly in every prompt.

**From product selection:**
- `[YOUR PRODUCT]` → product name only

**From campaign brief (Step 3.5):**
- Use any input the user provided in Step 3.5 to fill the corresponding slots
- If the user gave a voice dump, extract the key phrase and fit it to the template's constraints (e.g. distill a 3-sentence answer into a 6-word headline)
- If the user said "go" or left a template blank, auto-fill from brand voice

**Written by Claude (sourced from the right DNA — used when no brief input given):**

- **For product-claim slots** (`[BENEFIT 1-N]`, `[STRENGTH 1-N]`, `[CALLOUT 1-N]`, `[STAT N]` + numeric value placeholders, `[INGREDIENT]`, `[CLEAN LABEL CLAIM]`, `[VARIETY 1-N]`, `[PRODUCT DESCRIPTOR]`, `[VALUE PROP]`, `[YOUR ADVANTAGE]`, `[SUPERLATIVE CLAIM]`, `[QUOTE]` / `[REVIEW TEXT]` testimonial content) → source-of-truth is `product-dna.md` (loaded in Step 2). Pull the relevant section (Key benefits, Ingredients, Notable absences, Positioning, Tagline) and fit it to the slot's length and format hints in the template prompt.
- **For brand-voice slots** (`[YOUR HEADLINE]`, `[YOUR SUBHEAD]`, `[YOUR OFFER]` / `[OFFER DETAILS]`, brand-tone manifesto copy) → source-of-truth is `brand-dna.md` Voice in Practice section. Pull the brand's "Sounds like" tone and fit to the slot's length hint.
- **Invent + ⚠️ only when neither DNA has the answer** (real review counts, customer names, specific stats not in product-dna, real press coverage).
- **Never force product-dna content into a slot where it doesn't fit** (e.g. descriptive ingredients like "leather" into a numeric stat slot — invent + ⚠️ instead).

**Product facts rule:**
- When filling `[STAT]`, `[VALUE]`, `[CALORIES]`, `[CAFFEINE]`, or any number/spec: use the value the user confirmed in Step 3.5 — whether they gave a real number or approved your suggestion by saying "go"
- Never introduce new invented values at spec time that were not already shown and approved in the brief
- Never assume category-typical numbers at spec time without brief approval (e.g. "200mg caffeine", "10 calories")

**Product anchor — apply to every template without exception:**
When constructing the final prompt, find the first occurrence of `Create:` in the filled template text. Replace everything before it with this fixed opening:

```
The provided reference image shows the exact product that must appear in this ad. Do not invent, modify, or substitute this product — it must look identical to the reference image: shape, label, colors, and packaging.

Create: [rest of filled template text]
```

This replaces all "Use the attached images as brand reference" and "Match the exact product..." variations. Templates.md is not changed.

**Template 14 — single product only:**
When filling template 14 (Bundle Showcase + Benefit Bar), ignore the "two products / gift box / bundle" structure. Fill it as: the reference product displayed prominently with the benefit bar below. Do not reference or describe a second product. One product only.

**Aspect ratio:** extract the ratio stated at the end of each template text (e.g. "3:4 aspect ratio", "9:16 aspect ratio", "1:1 aspect ratio"). Store for the spec.

---

## Step 5 — Confirmation summary

```
Ready to generate [N] ads:

  Brand:     [brand]
  Product:   [selected image path]
  Templates: [list of selected template names]
  Output:    brands/[brand]/advertisements/[product-slug]_[YYYYMMDD_HHMMSS]/

Confirm to generate.
```

Derive `[product-slug]` from the product image filename — lowercase, hyphens, no extension.

---

## Step 6 — Write specs and generate

Create the parent output folder:
```bash
mkdir -p "brands/[brand]/advertisements/[product-slug]_[YYYYMMDD_HHMMSS]"
```

For each selected template, create a subfolder named `[NN]-[template-slug]` (zero-padded number + lowercase-hyphenated template name, e.g. `01-headline`, `07-us-vs-them`, `11-pull-quote-review-card`).

Write `ad-spec.json` in each subfolder:
```json
{
  "output_name": "[product-slug]",
  "brand": "[brand]",
  "product": "[product name]",
  "product_image": "brands/[brand]/studio-shots/[selected]/[file]",
  "template_number": [N],
  "template_name": "[template name]",
  "aspect_ratio": "[ratio extracted from template]",
  "headline": "[headline]",
  "prompt": "[fully filled template text]"
}
```

Then run the scripts **in parallel batches of 5** (not sequentially). Each `generate-ad.py` invocation is independent — reads its own spec.json, writes its own output, exits — so they can safely run concurrently.

**How to batch:**
- If N ≤ 5: kick off ALL N scripts at once via bash backgrounding (`&`), then `wait` for them all to complete.
- If N > 5: do batches of 5. Submit batch 1, wait for it to finish, submit batch 2, wait, etc. (a 40-template "all" run becomes 8 batches of 5.)

**Bash pattern (single batch of 5 example):**
```bash
python3 scripts/generate-ad.py brands/[brand]/advertisements/[timestamp]/01-headline &
python3 scripts/generate-ad.py brands/[brand]/advertisements/[timestamp]/07-us-vs-them &
python3 scripts/generate-ad.py brands/[brand]/advertisements/[timestamp]/11-pull-quote &
python3 scripts/generate-ad.py brands/[brand]/advertisements/[timestamp]/13-stat-radial &
python3 scripts/generate-ad.py brands/[brand]/advertisements/[timestamp]/27-checklist &
wait
```

**Progress reporting:**
- Before each batch: announce "Submitting batch [B] of [TOTAL_BATCHES]: [N] ads in parallel..."
- After each batch completes: announce "Batch [B] done. [N] ads written."
- After all batches: proceed to Step 7.

**Why batches of 5:** Higgsfield's gateway is flaky under heavy concurrent load (502/504 errors). 5 is a safe, validated batch size that won't trigger rate limits or cascading gateway errors. If batches of 5 prove stable in practice, the cap can be raised later — but never lower than 1 (sequential) without a different reason.

---

## Step 7 — Report back

```
Done. [N] ads generated.

brands/[brand]/advertisements/[product-slug]_[timestamp]/
  01-headline/        → "[headline]"
  07-us-vs-them/      → "[headline]"
  ...

What next:
- Regenerate one ad: python3 scripts/generate-ad.py brands/.../[folder]
- Run more templates: tell me the numbers
- Adjust a headline or detail: say which template and what to change
```

---

## Notes

- Studio shots give cleaner product placement — the model has a clear product to work with
- Templates already include "Use the attached images as brand reference" — the product image is the brand anchor
- Runs never overwrite — each generation adds _v1 → _v2 → _v3
- One generation per template per run — re-run the script directly for additional variations

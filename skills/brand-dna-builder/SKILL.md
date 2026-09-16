---
name: brand-dna-builder
description: Run when the user wants to set up their brand or provides a website URL. Researches the brand's visual identity, typography, ad creative style, and builds a brand profile with Color System. Downloads product images. Run this once per brand before using any other skill.
---

# Brand DNA Builder

Sets up your brand inside the AI Ad Studio. Run this once per brand before using any other skill.

Two outputs:
1. `brands/[brand-name]/brand-dna.md` — brand identity, color system, typography, ad creative style
2. `brands/[brand-name]/products.json` + `product-images/` — product index and downloaded images

---

## Step 1 — Select or create brand

Check if any brands already exist in `./brands/`. If brands are found, ask:
- "Would you like to add a new brand, or update an existing one?"

If no brands exist, proceed directly to Step 2.

---

## Step 2 — Choose your setup path

Ask in one message:

> "How would you like to set up your brand?
>
> **Option 1 — Automatic (via URL)**
> Give me your brand's website and I'll research it myself — reading the site, product pages, and about copy to build your brand profile. Faster, and works well for brands with a strong online presence.
>
> **Option 2 — Manual (interview)**
> I'll ask you a few questions about your brand. Best for your own brand, client work, or brands without a strong web presence.
>
> Note: automatic research doesn't always work on every website — if it fails, we'll switch to manual automatically.
>
> Which would you prefer? (1 for automatic, 2 for manual)"

---

## Step 3 — Build brand profile

### Auto path

Fetch the homepage first using WebFetch. Read it fully before searching anywhere else. Work through all three stages before writing anything.

#### Stage 1 — Site audit

Read the homepage, one product page, and the About page. Extract:

- **Voice:** Read 3–4 product descriptions and the hero headline. What tone does the brand use? Write 5 adjectives that capture it precisely — avoid generic category descriptors, be specific to this brand.
- **Photography:** Lighting quality (hard/soft, studio/natural). Color grade (warm/cool/neutral, contrast, matte or punchy). What surfaces and environments appear. What's in frame.
- **Colors:** Dominant color, accent, background tones. What is clearly off-limits.
- **Typography:** What font weight and style are used for headlines? How is body copy treated — tight, loose, all-caps? Note any distinctive typographic choices visible on the site.
- **Packaging:** Physical form — shape, material, finish (matte/gloss), label text and typography.
- **Target audience:** Who is this brand for? Age range, lifestyle, mindset — one sentence.

#### Stage 2 — Deeper search

```
WebSearch: [brand] color palette hex codes
WebSearch: [brand] typography
WebSearch: [brand] photography style campaign
```

Use anything specific (hex codes, exact font names, art direction notes). If nothing useful on a search, move on.

#### Stage 3 — Meta Ad Library

Search the brand in Meta's Ad Library (facebook.com/ads/library). Note:
- What formats are they currently running (feed square, Stories, carousel, video)?
- How is text used in their ads — headline-only, minimal, heavy copy?
- What is the visual treatment — lifestyle, product-only, mixed?

One paragraph is enough. This informs the Ad Creative Style section.

---

### Manual path

Ask all questions in one grouped message:

```
Let's build your brand profile. Answer what you know — skip anything that doesn't apply:

IDENTITY
Brand name:
Website (if any):
Positioning (who it's for, what it does):
Brand voice (5 adjectives):
Target audience (age, lifestyle, mindset):

COLORS
Primary brand color:
Secondary / accent color:
Background color:
Any colors that never appear:

TYPOGRAPHY
Headline font style (e.g. bold sans-serif, elegant serif, all-caps):
Any distinctive typographic choices:
How text sits in your ads (minimal, headline only, heavy copy):

PHOTOGRAPHY
Lighting style:
Color grade / mood:
Typical backgrounds and surfaces:
What appears in frame (subjects, props, styling):

PRODUCT
Physical form (shape, size, material, finish):
Label (text, typography, placement):
Most recognisable visual element:

ADS
What formats do you run (feed, Stories, video):
How do you use text in your ads:
```

**After the user provides their answers, write `brand-dna.md` (next section), then continue through Step 4 and Step 5. The Manual brand-setup path always lands on the Step 5 Manual sub-path (no URL exists to scrape from). Do not stop, do not suggest next-skill handoffs, until `products.json` is written.**

---

### Write brand-dna.md (both paths)

Create the brand folder:

```
brands/[brand-name]/
```

Save as `./brands/[brand-name]/brand-dna.md` using exactly this structure:

```
# [Brand Name] — Brand DNA

## Identity
**Name:** [Exactly as the brand writes it — styling, capitalisation, any symbols]
**Positioning:** [One sentence — who it's made for, what it does for them, and how it comes across]
**Voice:** [Five adjectives — specific to this brand]
**Target audience:** [Who buys it — age, lifestyle, mindset in one sentence]

## Color System
Lead:        [color name] — [hex]
Support:     [color name] — [hex]
Accent:      [color name] — [hex]
Background:  [color name] — [hex]
Off-limits:  [what never appears]

## Typography
Headline:    [typeface name and weight — e.g. "Neue Haas Grotesk, bold condensed"]
Body:        [typeface name — e.g. "Garamond, regular"]
Treatment:   [non-standard typographic choices — capitalisation style, tracking, leading, scale, weight contrast]
In ads:      [how type typically sits in their ads — placement, scale, color on image]

## Photography Style
- **Lighting:** [diffused or direct, available or studio — quality, direction, and effect on the subject]
- **What's in frame:** [subjects, hands, props, styling choices — everything that appears in the shot]
- **Color grade:** [warm or cool, flat or contrasty, clean or filmic — describe what you actually see]
- **Setting:** [surface material, background, indoor or outdoor]
- **Composition:** [camera angle, where the subject sits, how much negative space]
- **Mood:** [three to five adjectives — the feeling the imagery gives]

## The Product
Form:       [form factor and material only — e.g. "slim glass jar", "tall aluminium can"]
Label:      [label text, typography, placement]

## Ad Creative Style
Formats:      [what they run — feed square, Stories, carousel, video, etc.]
Text on image: [how copy sits in ads — sparingly, headline only, heavy, placement]
Visual style:  [photo-led, product-only, lifestyle, mixed — what dominates]
Current ads:   [one sentence on what they're actively running in Meta Ad Library]

## Voice in Practice
Sounds like: "[example sentence in brand voice]"
Never:       "[example of wrong tone]"

## Hard Rules
Always: [non-negotiable visual rule]
Always: [non-negotiable visual rule]
Never:  [visual rule]
Never:  [visual rule]

```

For Typography — if exact font names aren't provided, describe the style (e.g. "bold condensed sans-serif").

---

## Step 4 — Report back

Immediately after brand-dna.md is saved, confirm with the operator using the block below. **After showing the confirmation, IMMEDIATELY enter Step 5 — do NOT end the skill, do NOT suggest `/product-dna` or any other next-skill handoff until Step 5 has written `products.json`. Step 5 is mandatory for both Auto and Manual brand-setup paths.**

```
Brand DNA saved for [Brand Name].

Voice:       [5 adjectives]
Colors:      [lead] / [support] / [accent]
Typography:  [headline font]
Ad style:    [one line summary]

Next: let's set up your product images.
```

---

## Step 5 — Product images

**This step is mandatory. Never offer to skip it. Never suggest moving to the next skill until products.json is written.**

**Routing — pick the sub-path based on how the brand was set up in Step 3:**
- **Brand set up via Auto (URL) path →** use the **Auto path** sub-section below first. If the scrape fails, fall back to the Manual path sub-section.
- **Brand set up via Manual (interview) path →** skip the Auto path sub-section entirely and go directly to the **Manual path** sub-section. There's no URL to scrape from.

Whichever sub-path runs, the final result must be `products.json` written to the brand folder. Do not end the skill or suggest `/product-dna` until that file exists.

### Auto path — preview available products

Fetch the product list. For Shopify brands try:
```
[brand-url]/products.json?sort_by=best-selling&limit=20
```

Or use WebFetch on the shop/collections page to extract product names.

Present the list to the user. **STOP HERE. Do not download anything. Do not run the script. Wait for the user to reply before taking any action.**

```
Now let's get your product images set up.

Found [N] products on [brand]. Here are the top results:

  1. [Product Name]
  2. [Product Name]
  ...

Which would you like to download?
- Say "manual" to add your own images instead
- Pick numbers to download specific ones (e.g. "1, 3")
- Say "all" for everything
```

**Do not proceed until the user replies.**

If the user wants to download, run from the project root:

```bash
python3 scripts/scrape-brand-products.py --url [brand-url] --out brands/[brand-name] --limit [N]
```

This saves:
- Images → `brands/[brand-name]/product-images/`
- Index → `brands/[brand-name]/products.json`

**If the script fails** (non-Shopify, heavy JS rendering): tell the user and fall back to manual.

### Manual path — add images yourself

Tell the user:

```
Your product-images folder is ready at brands/[brand-name]/product-images/

Drop your product images in there. Use lowercase filenames, hyphens between words, no spaces — like pynk-can-pink.jpg. Tell me when they're in and I'll build your products.json.
```

Wait for the user to confirm before doing anything else.

### Write products.json (both paths)

Once images are confirmed in the folder:

1. Scan `brands/[brand-name]/product-images/` for all image files
2. For any file with uppercase letters or underscores — rename it to lowercase with hyphens before proceeding. Example: `PYNK_Can_Pink.png` → `pynk-can-pink.png`. Use your file tools to rename, not bash.
3. Write `products.json` using EXACTLY this structure — no extra fields, no variations:

```json
{
  "products": [
    {
      "name": "Product Name As Written",
      "filename": "product-name-as-written.jpg",
      "page_url": ""
    }
  ]
}
```

- `name` — human-readable product name
- `filename` — the actual filename in product-images/ (after renaming)
- `page_url` — leave empty string `""` for manually added products

**If multiple images exist for the same product:** ask "which of these is the hero shot for [product]?" before writing products.json. Only one entry per product.

**Optional richer fields** (only present when auto-path scraped from Shopify) — `description_html`, `product_type`, `tags`, `vendor`. The scraper writes these automatically. Manual entries leave them out. The downstream `/product-dna` skill reads them for auto-fill of product DNA sheets.

Once `products.json` is written, reply in plain chat (NOT in a fenced code block) with this exact shape — including the blank line between the two paragraphs:

> Brand [Brand Name] is set up and ready.
>
> Next — run `/product-dna` to capture product details for the [product name] (real claims, ingredients, positioning).
>
> Downstream skills like `/ad-generator` and `/ugc-content` read those facts to write authentic copy instead of inventing it.


## Notes

- If exact font names can't be found, describe the style precisely rather than guessing a name.
- If the Meta Ad Library shows no active ads, note it and skip the Current ads field.
- Folder naming: slug the brand name — lowercase filenames, hyphens between words — `pynk`, `rhode`, `the-ordinary`
- If hex codes can't be confirmed exactly, search `[brand] color palette hex codes` — estimated values are better than no values
- To update brand DNA, run this skill again — it overwrites the existing file
- A single project supports many brands — each lives in its own `brands/[name]/` subfolder

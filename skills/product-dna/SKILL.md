---
name: product-dna
description: Run when the user wants to set up product details, add a new product to an existing brand, or capture product DNA. Iterates products in a brand, fills per-product DNA markdown (tagline, benefits, ingredients, positioning). Downstream skills read these to write authentic content. Auto-fills from a product URL or runs a short manual interview. Run after /brand-dna-builder.
---

# Product DNA

Captures detailed product information per product as a markdown sheet. Every downstream skill — UGC scripts, ad templates, product photoshoots, marketplace listings — reads these files to pull real product facts (real ingredients, real claims, real benefits) instead of inventing them.

One product per run. Run as many times as you have products to set up.

**Prerequisite:** the brand must exist (`/brand-dna-builder` run at least once).

---

## Step 1 — Select brand

Check `./brands/` for subfolders containing a `brand-dna.md`. One match — use it and confirm the brand name. Several matches — list and ask. None — point the user to `/brand-dna-builder` first.

---

## Step 2 — Pick what to set up

Read `brands/[brand]/products.json` to enumerate registered products. Check `brands/[brand]/product-dna/<slug>.md` for each (slug = product filename without extension) to determine DNA status.

Present a single unified picker:

```
What do you want to set up?

  Existing products without DNA yet:
    1. The Dewy Skin Cream            ← no DNA yet
    2. The Water Cream                ← no DNA yet
    
  Existing products with DNA:
    3. The Rice Wash                  ← DNA exists (option: update)
    
  Or:
    4. + Add a new product
```

User picks ONE number.

If the user picks an existing product **without** DNA → proceed to Step 3a (DNA capture flow).
If the user picks an existing product **with** DNA → ask "Update or skip?" → if update, proceed to Step 3a, if skip, end skill.
If the user picks "Add a new product" → proceed to Step 3b.

---

## Step 3a — Capture DNA for an existing product

The product already has an image at `brands/[brand]/product-images/<slug>.<ext>` and an entry in `products.json`.

### Auto path (product has `page_url`)

1. Read the product's `page_url` from `products.json`.
2. Read the optional rich fields if present: `description_html`, `product_type`, `tags`, `vendor` (the scraper writes these for Shopify-fetched products).
3. Use WebFetch on the product URL to read the live page. Extract: tagline / subhead, full description, key benefits, ingredients section (if skincare/food), claims, positioning hints.
4. Compose the template (see "Template" below) filled with what was found. Mark anything invented (e.g. assumed category) with a ⚠️.
5. Show the proposed template to the user:
   > "Here's what I'd put for [Product Name]. Review + edit anything, or say 'save' to keep as-is."
6. Apply the user's edits. Save to `brands/[brand]/product-dna/<slug>.md` (create the directory if it doesn't exist).
7. Confirm + end (see Step 4).

### Manual path (no `page_url`, OR auto-fetch fails, OR user prefers)

Ask all 6 sections in ONE grouped message. **Render the form below inside a fenced code block (triple backticks) in chat, copied verbatim — do not paraphrase, do not drop the examples in parentheses, do not compress section spacing.** The form has been designed so non-expert users know exactly what to fill in.

```
Quick product DNA for [Product Name]
Fill in what you know, skip anything that doesn't apply.

Category (e.g. energy drink, supplement, sneaker):

Sizes / flavors / scents (if applicable):

Tagline (one-line claim — e.g. "Zero-Sugar Energy Drink", "Premium Leather Jacket"):

Description (1-2 sentences — what it is, who it's for):

Key benefits (3-5 specific bullets — what the product actually delivers):

Ingredients / materials (skincare/food → ingredients; fashion/objects → materials):

Notable absences (e.g. no artificial sweeteners, no parabens):

Positioning (1-2 sentences — what makes it different vs alternatives):
```

Wait for the user to fill out. Compose the template from their answers (empty answers → empty fields in the file). Save to `brands/[brand]/product-dna/<slug>.md`. Confirm + end.

---

## Step 3b — Add a new product

Ask the user:

> "How do you want to add this product?
>
> **1 — URL:** paste a product webpage URL. I'll download the hero image and pre-fill the DNA from the page.
> **2 — Manual:** drop an image into the product-images folder and we'll fill the DNA together by hand."

### Path B1 — URL

1. Ask: "What's the product URL?"
2. Use `scripts/scrape-brand-products.py` logic OR run the scraper against just this URL. Pull: title, hero image, description_html, product_type, tags, vendor (Shopify) OR fall back to HTML OG tags (non-Shopify).
3. Derive `<slug>` from the product title (lowercase, hyphens — same convention as existing products).
4. Save the hero image to `brands/[brand]/product-images/<slug>.<ext>`.
5. Append the new entry to `products.json` with all fields (`name`, `filename`, `page_url`, + `description_html` / `product_type` / `tags` / `vendor` if present). If a `<slug>` already exists in products.json, ask the user for a different name.
6. Compose the template auto-filled from the scraped data. Mark invented values with ⚠️.
7. Present to user. Apply edits. Save `product-dna/<slug>.md`.
8. Confirm + end.

### Path B2 — Manual

1. Ask: "What do you want to call this product? (short name, will become the filename — e.g. `pink-energy-drink`)"
2. Slug the name (lowercase, hyphens).
3. Tell the user:
   > "Drop the product image into this folder:
   > `brands/[brand]/product-images/`
   >
   > Any filename is fine — I'll rename it for you. Reply 'done' when the file is there."
4. Wait for the user's "done" reply.
5. Detect and rename the new file:
   - List all image files in `brands/[brand]/product-images/`.
   - Cross-reference against `products.json` — any filename already listed there belongs to an existing product. Ignore those.
   - The remaining file(s) are new. If exactly one new file → rename it to `<slug>.<ext>` (preserving the original extension, lowercased). If multiple new files → ask the user which one is the product they just added.
   - If zero new files → tell the user the folder looks unchanged and ask them to recheck.
   - Use file tools to rename, not bash.
6. Append the new entry to `products.json` with `name`, `filename`, `page_url: ""`. No rich Shopify fields.
7. Ask the DNA questions in one grouped message (same form as Step 3a manual path).
8. Compose the template from answers. Save `product-dna/<slug>.md`.
9. Confirm + end.

---

## Step 4 — Confirm + suggest next

```
Product DNA saved: brands/[brand]/product-dna/<slug>.md

Next:
  /product-dna    — set up another product
  /character-creator — build a brand character
```

---

## Template — `brands/[brand]/product-dna/<slug>.md`

Use this exact structure (five sections, in this order). Empty values stay empty — downstream skills handle missing sections.

```markdown
# [Product Name] — Product DNA

## Identity
**Category:** [energy drink / supplement / sneaker / ...]
**Sizes / flavors / scents:** [if it comes in multiple options]

## What it does
**Tagline:** [one-liner]
**Description:** [1-2 sentences — what is it, who's it for]

## Key benefits
- [benefit 1 — specific, not generic]
- [benefit 2]
- [benefit 3]

## Ingredients / materials
- [key ingredient or material 1]
- [key ingredient or material 2]
- Notable absences: [free of X, Y, Z]

## Positioning
[1-2 sentence positioning vs alternatives]

## Copy — Bahasa Indonesia
**Tagline (ID):** [Indonesian tagline]
**Description (ID):** [Indonesian description]
**Key benefits (ID):**
- [benefit 1 in Bahasa]
- [benefit 2 in Bahasa]
- [benefit 3 in Bahasa]
```

The **Copy — Bahasa Indonesia** section is a localized mirror of the Tagline, Description, and Key benefits — natural, on-brand Bahasa Indonesia marketing copy (not a literal word-for-word translation). Downstream skills use it to write authentic Indonesian-market ads and UGC. Fill it for every product; if the brand is English-only and the user doesn't want localized copy, leave the section's fields empty.

---

## Notes

- Slug for the DNA file is always derived from the product image filename without extension (`the-rice-wash.jpg` → `the-rice-wash.md`).
- Skip option always available — at any point, the user can say "skip" or "later" and the skill ends without writing a file. Downstream skills handle missing DNA gracefully.
- The DNA file is the single source of truth for product context. `products.json` stays minimal (name, filename, page_url + optional Shopify rich fields). Downstream skills read the DNA file when they need product facts.
- The auto-fill is a STARTING POINT, never a final answer. Always wait for user review/edit before saving. Even ⚠️-marked items need user confirmation.
- If a user wants to update an existing DNA, this skill overwrites the file in place. There's no version history — encourage users to keep the DNA file in their own git or backup if they want history.

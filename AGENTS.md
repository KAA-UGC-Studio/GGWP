# AI Ad Studio

Build product photography, static ads, and UGC content using Codex and the Higgsfield CLI.

---

## Getting started

First session in a fresh clone? Check setup before generating anything — `README.md` lists
what must be installed (`pip install -r requirements.txt`, `.env` with `KIE_API_KEY`,
`higgsfield auth login`, ffmpeg for `/ugc-clone`). A missing key or an expired auth is the
usual cause of a run failing on its first API call.

In a hurry? `/ugc-studio` runs the whole chain below in one go — brand → product → character → video — reusing whatever is already set up.

Start here:

1. `/brand-dna-builder` — set up your brand (run once per brand before anything else)
2. `/product-dna`       — set up each product (run once per product, after brand is ready)
3. `/character-creator` — build a brand character (headshot + full body)

Then pick any generation skill:

4. `/studio-shot-generator`  — turn any product photo into a clean studio shot
5. `/product-shot-generator` — place your product into a reference composition
6. `/product-visual`         — generate brand-quality product imagery, 7 photo modes (lifestyle, closeup, moodboard, hero banner, virtual model tryout, conceptual, restyle)
7. `/ad-generator`           — pick from 40 ad templates, fill with brand DNA, generate
8. `/product-ugc-generator`  — generate a UGC selfie and talking-head video (Veo path)
9. `/ugc-content`            — branded UGC-style video, 5 modes via Higgsfield Marketing Studio
10. `/ugc-content-kie`       — same 5 UGC modes on the kie.ai backend (Nano Banana Pro still → Veo 3.1 / Kling 3.0 / Seedance 2.0)
11. `/product-video`         — cinematic (non-UGC) product video, 4 modes via Higgsfield Marketing Studio (product motion film, creative, brand spot, cinematic try-on)
12. `/ugc-clone`             — clone a reference video: watches it, then writes prompts (EN + ID) for your brand. Never generates

---

## Folder structure

```
brands/
  [brand-name]/
    brand-dna.md
    products.json
    product-images/
    studio-shots/
    product-shots/
    advertisements/
      [product-slug]_[timestamp]/
        [NN]-[template-name]/
          ad-spec.json
          [product-slug]_v1.png
    characters/
      [character-name]/
        character-spec.json
        characteristics.md
        headshot.png
        fullbody.png
        multiangle.png          (six-angle face sheet; re-runs add _v2, _v3)
        reference.[ext]         (only when built from a reference photo)
    ugc-clone/
      [character]-[product]-[ref-slug]/
        ugc-clone-spec.json
        prompt-en.md
        prompt-id.md
    product-ugc/
      [output-name]/
        product-ugc-spec.json
        [output-name]_v1.png
        [output-name]-run1.mp4
    product-visual/
      [output-name]/
        product-visual-spec.json
        [output-name]_v1.png
    product-video/
      [mode]/
        [output-name]/
          product-video-spec.json
          [output-name]_v1.mp4
    ugc-content-kie/
      [mode]/
        [output-name]/
          ugc-content-kie-spec.json
          [output-name]_still_v1.png
          [output-name]_v1.mp4
```

---

## Skills

| Skill | What it does |
|-------|-------------|
| `/ugc-studio` | The whole pipeline in one run — brand → product → character → video, reusing what exists. Ends on `/ugc-clone` or `/ugc-content` |
| `/ugc-clone` | Clone a reference video — watches it (scene cuts, movement, dialogue), recommends a model, writes prompts in EN + ID. Never generates |
| `/brand-dna-builder` | Set up your brand — scrapes product images, builds color system and generation modifier |
| `/product-dna` | Capture per-product details (tagline, benefits, ingredients, positioning) — read by every downstream skill |
| `/character-creator` | Generate a matched headshot + full-body casting digital + six-angle face sheet for a brand character, from brand DNA, a reference photo, or by hand |
| `/studio-shot-generator` | Turn any product photo into a clean studio shot |
| `/product-shot-generator` | Place your product into a reference composition |
| `/product-visual` | Generate brand-quality product imagery — 7 modes (Lifestyle / Closeup / Moodboard / Hero banner / Virtual model tryout / Conceptual / Restyle) via Higgsfield product-photoshoot |
| `/ad-generator` | Pick from 40 ad templates, fill with brand DNA, generate |
| `/product-ugc-generator` | Create a UGC selfie and talking-head video of a character holding your product (Veo path) |
| `/ugc-content` | Generate a branded UGC-style video — 5 modes (UGC / Tutorial / Unboxing / Review / Try-On) via Higgsfield Marketing Studio Video |
| `/ugc-content-kie` | kie.ai analogue of `/ugc-content` — same 5 modes, two-stage build (Nano Banana Pro still → routed video model), for when Higgsfield has no credits or the user asks for kie.ai |
| `/product-video` | Generate a cinematic (non-UGC) product video — 4 modes (Product Motion Film / Creative Video Mode / Cinematic Brand Spot / Editorial Try-On) via Higgsfield Marketing Studio Video |

---

## Reference

- `docs/ai-tools-knowledge.md` — which video model to use and how to prompt it: per-model cards (durations, references, dialogue languages, native syntax), a quick picker, and the operator's own notes. Read by `/ugc-clone`. Update it when a run teaches you something new.
- `docs/kie-pricing.md` — kie.ai model pricing (credits / USD / IDR) for every model used by the skills. Check before expensive runs; update it when a run's receipt differs.
- `docs/kie-pricing-refresh.md` — how to re-read kie.ai's price list (browser only — it 403s automated fetches) and which row variant matches what the code sends.

## Rules

- Always open the project root folder in Codex — not a subfolder
- Lowercase filenames, hyphens between words, no spaces — `pynk-can-pink.jpg`
- Every generation saves as a new file — outputs never overwrite each other
- Higgsfield auth is global — `higgsfield auth login` once per machine
- Characters are brand-specific — each brand has its own `characters/` subfolder
- A single project supports many brands — each lives in its own `brands/[name]/` subfolder
- When scanning folders (`characters/`, `product-images/`, `studio-shots/`, etc.), ignore dotfiles (`.DS_Store`, `.AppleDouble`, `Thumbs.db`, etc.) and the project-level `.gitignore` lists what's excluded. Generated outputs are real files (PNG / MP4) with sidecar `.uuid` siblings — sidecar files are NOT dotfiles, they're named `<file>.uuid` and are part of the system

# AI Ad Studio

Product photography, static ads, and UGC video — generated from a brand brief, inside Claude Code.

Thirteen skills that turn a product photo and a few facts about your brand into studio shots,
ad creatives, brand characters, and talking-head UGC video. You run them by typing a slash
command. Claude does the rest.

---

## What you need

| | | |
|---|---|---|
| **Claude Code** | required | The skills run inside it — [install guide](https://docs.claude.com/en/docs/claude-code) |
| **Python 3.10+** | required | Every generator is a Python script |
| **kie.ai API key** | for the `-kie` skills | [kie.ai/api-key](https://kie.ai/api-key) — pay-as-you-go, you own the account |
| **Higgsfield CLI** | for the Higgsfield skills | Auth once per machine with `higgsfield auth login` |
| **ffmpeg + ffprobe** | for `/ugc-clone` only | Must be on your `PATH` |

You bring your own API keys. Generation costs are billed by kie.ai / Higgsfield directly to
you — see `docs/kie-pricing.md` for what each run costs in credits, USD, and IDR.

---

## Install

```bash
git clone <your-repo-url> ai-ad-studio
cd ai-ad-studio
pip install -r requirements.txt
cp .env.example .env        # then paste your KIE_API_KEY into .env
higgsfield auth login       # only if you plan to use the Higgsfield skills
```

Then open **the `ai-ad-studio` folder itself** in Claude Code — not a subfolder, not a parent.
The skills resolve paths relative to the project root, so opening the wrong folder breaks them.

```bash
claude
```

Type `/` and you should see `/brand-dna-builder`, `/ugc-studio`, and the rest.

### Optional: the skills these build on

This repo's skills are self-contained — nothing here calls another skill by name. But the same
workflows get better with the Higgsfield skill pack installed alongside them. `skills-lock.json`
records which ones and at what version; install them from their own source
(`higgsfield-ai/skills`) rather than from this repo, so you get updates and the original license.

---

## Quickstart — first video in four commands

```
/brand-dna-builder      → set up the brand (once per brand)
/product-dna            → capture one product's details
/character-creator      → cast a brand character (headshot + full body)
/ugc-content-kie        → generate the UGC video
```

In a hurry, `/ugc-studio` runs that whole chain in one go and reuses whatever is already set up.

`CLAUDE.md` is the full map — every skill, what it does, and the folder each one writes to.
Claude reads it automatically, so you can also just ask: *"which skill makes a studio shot?"*

---

## What's in the box

```
skills/        13 skills — the product
scripts/       15 Python generators the skills call
docs/          model knowledge, kie.ai pricing, price-refresh procedure
.claude/       slash-command wrappers (/ugc-content, /ad-generator, …)
brands/        example brands — see brands/README.md
Referensi/     character templates + photography cheat sheets
CLAUDE.md      the project map Claude reads on every session
```

| Skill | What it does |
|-------|-------------|
| `/ugc-studio` | The whole pipeline in one run — brand → product → character → video |
| `/ugc-clone` | Watches a reference video and writes prompts (EN + ID) for your brand |
| `/brand-dna-builder` | Sets up a brand — scrapes product images, builds the color system |
| `/product-dna` | Per-product details every other skill reads |
| `/character-creator` | Headshot + full body + six-angle face sheet for a brand character |
| `/studio-shot-generator` | Any product photo → clean studio shot |
| `/product-shot-generator` | Places your product into a reference composition |
| `/product-visual` | Brand-quality product imagery, 7 photo modes |
| `/ad-generator` | 40 ad templates, filled with your brand DNA |
| `/product-ugc-generator` | UGC selfie + talking-head video (Veo path) |
| `/ugc-content` | Branded UGC video, 5 modes (Higgsfield) |
| `/ugc-content-kie` | The same 5 modes on kie.ai |
| `/product-video` | Cinematic product video, 4 modes |

---

## House rules

- Open the project root in Claude Code — never a subfolder
- Lowercase filenames, hyphens between words, no spaces — `pynk-can-pink.jpg`
- Every generation saves a new file; outputs never overwrite each other
- One project holds many brands — each lives in its own `brands/[name]/`
- Characters are brand-specific — each brand has its own `characters/`

---

## When something breaks

| Symptom | Fix |
|---|---|
| Slash commands don't appear | You opened the wrong folder. Open the repo root. |
| `higgsfield: command not found` | Higgsfield CLI isn't installed or isn't on `PATH` |
| Auth errors mid-generation | `higgsfield auth login` — the session expired |
| `KIE_API_KEY` errors | `.env` is missing or the key line is empty |
| `/ugc-clone` fails instantly | ffmpeg/ffprobe not on `PATH` |
| A run costs more than expected | Check `docs/kie-pricing.md` — resolution and duration drive the price |

---

## License

Licensed to one buyer for their own and their clients' commercial work. Not for resale or
redistribution. Full terms in `LICENSE.md`.

# brands/

One folder per brand. `/brand-dna-builder` creates them; every other skill reads from them.

## What ships here

**`anker-indonesia/`** is a complete working brand — `brand-dna.md`, `products.json`, and the
product images the generators use as input. Start here to see what a ready-to-run brand looks
like, or copy it as a starting shape for your own.

The other four (`cargloss-helmet`, `reseller`, `saturdays`, `skin1004`) ship as **specs only** —
the `.md` and `.json` files, without the generated media. They are real briefs from real runs,
kept as filled-in examples of what good input looks like: how a `brand-dna.md` reads when it is
specific enough, how a `characteristics.md` pins a character down, what a
`ugc-content-kie-spec.json` contains after a successful run. The images and videos those runs
produced are the clients' work and aren't distributed.

So: nothing is broken if a brand has no `.png` or `.mp4`. That's the point — you supply your own
product images and generate your own output.

## Your first brand

Don't hand-write these files. Run:

```
/brand-dna-builder
```

It asks for a brand name and a website or catalogue URL, scrapes the product images, builds the
color system and the generation modifier, and writes the folder for you. Then `/product-dna` for
each product you want to advertise.

## Shape of a brand folder

```
brands/[brand-name]/
  brand-dna.md              voice, colors, generation modifier — read by every skill
  products.json             the catalogue
  product-dna/              per-product briefs (/product-dna)
  product-images/           source photos you supply
  characters/[name]/        headshot, full body, face sheet (/character-creator)
  studio-shots/             (/studio-shot-generator)
  product-shots/            (/product-shot-generator)
  product-visual/           (/product-visual)
  advertisements/           (/ad-generator)
  product-ugc/              (/product-ugc-generator)
  ugc-content-kie/[mode]/   (/ugc-content-kie)
  product-video/[mode]/     (/product-video)
  ugc-clone/                (/ugc-clone) — prompts only, no generation
```

# Refreshing kie.ai prices

Prices are **vendored** in `docs/kie-pricing.md` — the reference every skill quotes before an
expensive run. kie.ai publishes no pricing API, so refreshing it is a manual pass.

## Why there is no scraper

- `api.kie.ai/api/v1/jobs/models` → **404**. kie.ai publishes no pricing API.
- `kie.ai/pricing`, `kie.ai/market` → **403** to any server-side fetch (Cloudflare).
  This includes `WebFetch`, `curl`, and a Next.js route handler.

The price list is only readable from a **signed-in browser session**. The one live number the
app can fetch server-side is the user's own credit balance, via
`GET https://api.kie.ai/api/v1/chat/credit` — that is what the `/pricing` balance strip uses.

## Procedure

1. Open <https://kie.ai/pricing> in a browser where you're signed in.
2. Use the **search box** (top right) — one word only. Multi-word queries like `"seedance 2"`
   or `"kling 3"` silently return nothing; `seedance` and `kling` work. If typing produces no
   filtering, click directly into the field first — focusing it by element reference alone
   does not always take.
   Useful queries: `banana` · `gemini` · `veo` · `kling` · `seedance` · `gpt image`
   (note: `gpt-image` with a hyphen returns nothing).
3. Alternatively filter by the **Video / Image** category tabs and set **50 rows per page**.
4. Read four things off each row: the **exact row heading**, **credits/generation**, the
   **unit** (`per image` / `per second` / `per video`), and **Harga Kami (USD)**.

## Reading the rows correctly

The heading encodes the billing dimensions, and picking the wrong variant is the easiest way
to publish a wrong number. Match the row to what the code actually sends:

- **Resolution** — the scripts render video at `1080p` and pin Nano Banana 2 to `1K`. Where
  they send no resolution (GPT Image 2, Kling, Seedance), kie's default applies — record that
  tier and note the assumption.
- **Audio** — we send `sound: true` to both Kling models and `generate_audio: true` to
  Seedance. Audio rows cost more; do not quote the silent rate.
- **`with video input` vs `no video input`** — these bill differently
  (`with` = unit price × *(input + output)* duration). We only ever send a still image, so
  **`no video input`** is always the right row.
- **Unit** — a `per second` model must be multiplied by duration; `per video` is flat.
  Gemini Omni is `per video` and priced per duration tier, so its effective per-second rate
  drops as clips get longer. Don't interpolate it linearly.

## Updating

1. Edit the affected rows in `docs/kie-pricing.md`.
2. Re-check the USD → IDR rate used by the table against the current rate.
3. Update the "Last updated" line so a stale number is visible as stale.

`kieLabel` on each entry is the exact row heading from the price list — use it to re-find the
row next time. If a heading has changed, kie has likely restructured that model's tiers; read
the whole group before editing.

## Promoting a price to `confidence: "receipt"`

`"listed"` means read off the price list. To upgrade a model to `"receipt"`:

1. Note the kie.ai balance before a run (`python scripts/kie-check.py` or the `/pricing` strip).
2. Run exactly one generation of that type.
3. Compare the delta to what `/pricing` estimated.

If they match, set `confidence: "receipt"` and record the date in the entry's `note`. If they
don't, the listed tier is wrong for how we call the model — fix the tier first, then re-check
which variant (resolution / audio / input mode) we're actually being billed for.

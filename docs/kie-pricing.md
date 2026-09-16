# kie.ai Model Pricing Reference

Quick cost lookup for every kie.ai model used in this project (skills).
Last updated: **2026-09-06** (Seedance rows re-read; other models last read 2026-08-23) · Check balance anytime: `python scripts/kie-check.py`


## Basis

- **1 kie.ai credit = $0.005** ($5 = 1,000 credits; 5–10% bonus on larger top-ups) — confirmed
  three independent ways on the price list (18.4 cr → $0.092 · 4 cr → $0.02 · 105 cr → $0.525)
- **IDR conversions below use Rp 16.300 / USD** — adjust when the rate moves
- 1 credit ≈ **Rp 82**
- Confidence tags: ✅ = observed on a real run in this project · 📄 = kie.ai's listed price ·
  ~ = third-party estimate, verify before relying on it

---

## Image models

| Model | kie slug | Used by | Price | USD | IDR | Tag |
|---|---|---|---|---|---|---|
| Nano Banana | `google/nano-banana` | fast drafts, fallback | 4 cr / image | $0.02 | Rp 330 | 📄 |
| Nano Banana 2 | `nano-banana-2` | primary for every image job; `/ugc-content-kie` Stage-1 still | **8 cr @ 1K** · 12 cr @ 2K · 18 cr @ 4K | **$0.04** / $0.06 / $0.09 | Rp 650 / 980 / 1.470 | 📄 |
| GPT Image 2 | `gpt-image-2-image-to-image` | text-heavy ad layouts | **6 cr @ 1k** · 10 cr @ 2k · 16 cr @ 4k | **$0.03** / $0.05 / $0.08 | Rp 490 / 820 / 1.300 | 📄 |

The scripts pin `resolution: "1K"` on Nano Banana 2 and sends no resolution for GPT Image 2
(so kie's 1k default applies) — the bolded tiers are what we actually pay.

## Video models

Every video job renders at **1080p**.

| Model | kie slug | Dialogue? | Durations | Price | 8s USD | 8s IDR | Tag |
|---|---|---|---|---|---|---|---|
| Gemini Omni Flash | `gemini-omni-video` | ✅ speaks (incl. Bahasa Indonesia) — supersedes Veo for talking-head | 4 / 6 / 8 / 10s · 720p/1080p/4k | **flat per clip @1080p:** 4s 63 cr · 6s 84 cr · 8s 105 cr · 10s 126 cr | **$0.525** | Rp 8.560 | 📄 |
| Veo 3.1 Fast | `veo3_fast` | ✅ speaks (legacy talking-head, fallback only) | 4 / 6 / 8s | **65 cr flat @1080p** (60 @720p, 180 @4K) | $0.325 | Rp 5.300 | 📄 |
| Veo 3.1 Quality | `veo3` | ✅ speaks | 4 / 6 / 8s | 255 cr flat @1080p | $1.275 | Rp 20.800 | 📄 |
| Kling 2.6 | `kling-2.6/image-to-video` | ❌ ambient audio only | 5 / 10s | **with audio:** 5s 110 cr · 10s 220 cr (55/110 without) | 10s $1.10 | 10s Rp 17.900 | 📄 |
| Kling 3.0 (std) | `kling-3.0/video` | ❌ ambient audio only | 5 / 10s | **27 cr/s @1080p with audio** (18 without · 20 @720p · 67 @4K) | 10s $1.35 | 10s Rp 22.000 | 📄 |
| Seedance 2.0 Fast | `bytedance/seedance-2-fast` | ❌ ambient audio only | 4–15s · 480p/720p only | **24.8 cr/s @720p** (11.7 @480p) | $0.99 | Rp 16.200 | 📄 |
| Seedance 2.5 | `bytedance/seedance-2-5` | ❌ ambient audio only | 4–30s · 480p/720p/1080p | **63 cr/s @720p** (28 @480p · 114 @1080p) | $2.52 | Rp 41.100 | 📄 |

**Gemini Omni is priced per clip, not per second.** The per-second rate *falls* as the clip
grows (15.75 cr/s at 4s → 12.6 cr/s at 10s), so halving the duration does **not** halve cost.
Kling 3.0 and Seedance *are* per-second, so for those it roughly does.

**Seedance 2.5 is pinned to 720p** in `model-catalog.ts` — 1080p costs 114 cr/s ($4.56 for 8s).
Two things only it can do: it reads a closing frame (`last_frame_url`), so segmented product
stories chain scene-to-scene on it the way they do on Kling 3.0; and it renders **up to 30s in
one generate** where every other model here tops out at 10s, so product video and UGC video
offer 15/20/25/30s on it. Story Mode is unaffected — it still renders 10s segments and stitches
them, on this model like any other.

We send `sound: true` to both Kling models — audio is a real surcharge (+50% on Kling 3.0,
+100% on Kling 2.6). Seedance gets `generate_audio: true` and a first frame, so the cheaper
"with video input" rate never applies.

---

## Full-run cost — UGC run (still + video, two charges per run)

Nano Banana 2 @1K still (8 cr) + one video:

| Video model | Total credits | USD | IDR |
|---|---|---|---|
| Gemini Omni Flash, 8s (**default — the only one that speaks Indonesian**) | 113 | **$0.57** | Rp 9.200 |
| Gemini Omni Flash, 4s | 71 | $0.36 | Rp 5.800 |
| Veo 3.1 Fast, 8s (legacy fallback) | 73 | $0.37 | Rp 6.000 |
| Kling 2.6, 5s | 118 | $0.59 | Rp 9.600 |
| Kling 3.0 std, 10s | 278 | $1.39 | Rp 22.700 |
| Seedance 2.0 Fast, 10s 720p | 256 | $1.28 | Rp 20.900 |
| Seedance 2.5, 10s 720p | 638 | $3.19 | Rp 52.000 |
| Seedance 2.5, 30s 720p (one clip — no other model goes past 10s) | 1.898 | $9.49 | Rp 154.700 |

## Full-run cost — Story Mode

`n = duration / 10` scenes, each = 1 keyframe still (8 cr) + one 10s segment:

| Story | Scenes | Kling 3.0 | Seedance 2.0 Fast | Seedance 2.5 |
|---|---|---|---|---|
| 20s | 2 | 556 cr · $2.78 | 512 cr · $2.56 | 1,276 cr · $6.38 |
| 30s | 3 | 834 cr · $4.17 | 768 cr · $3.84 | 1,914 cr · $9.57 |
| 40s | 4 | 1,112 cr · $5.56 | 1,024 cr · $5.12 | 2,552 cr · $12.76 |

**Rules of thumb**
- Regenerating (`_v2`) re-runs BOTH stages — every retry costs a still + a video charge.
- Want the character talking → **Gemini Omni Flash** (default) or Veo as the legacy
  fallback; Kling/Seedance are dialogue-free by design.
- Long clips get expensive fast: a 40s Kling story ≈ 10× an 8s Omni UGC run.

## Cheaper tiers we are not using

Listed on kie.ai for models we already run, but not wired into `CANDIDATES` — quality is
untested here, so treat a switch as a change that needs its own evaluation.

| Alternative | Replaces | Price | Saving |
|---|---|---|---|
| Veo 3.1 Lite @1080p | Veo 3.1 Fast (65 cr) | 35 cr · $0.175 | −46% |
| Nano Banana 2 Lite @1K | Nano Banana 2 (8 cr) | 4 cr · $0.02 | −50% |
| Kling 3.0 Turbo @1080P | Kling 3.0 (27 cr/s) | 22.5 cr/s · $0.1125/s | −17% |
| Seedance 2.0 Mini @720P | Seedance 2.0 Fast (24.8 cr/s) | 8.2 cr/s · $0.041/s | −67% |

## Other backends

- **Higgsfield** (`/ugc-content`, `/product-video`, `/product-visual`, studio/product shots via
  `gpt_image_2` / `nano_banana_2` / `veo3_1`) bills its own credits on your Higgsfield plan —
  not kie.ai credits. Check with the Higgsfield balance tool / `higgsfield auth` account page.

## Updating this file

See **[kie-pricing-refresh.md](kie-pricing-refresh.md)** for the procedure. In short: kie.ai's
pricing pages return 403 to automated fetches, so numbers come from a signed-in browser pass
over [kie.ai/pricing](https://kie.ai/pricing) (📄), real run receipts (✅), or third-party
writeups (~). When a run's credit usage differs noticeably from this table, update the row and
the date and re-tag it ✅.

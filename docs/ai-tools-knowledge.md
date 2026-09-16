# AI Tools Knowledge — video & start-frame models

What `/ugc-clone` reads to **recommend a video model** and to **write the prompt in that model's native syntax**. Merges three sources:

1. The operator's field notes — copied verbatim below. **These win on quality judgments.**
2. Repo facts — `docs/kie-pricing.md` and the model routing in `scripts/generate-ugc-content-kie.py`.
3. Web research (2026-09-16) — vendor guides and reviews, listed under Sources.

Last updated: **2026-09-16**. When a real run contradicts this file, update the model card and the date.

---

## Personal notes (verbatim — "Dari apa yang saya rasakan")

> **VEO 3.1 :** Mode voicenya sudah support bahasa indonesia sehingga bisa talking head, tidak serealistis kling, harga menengah
>
> **VEO OMNI FLASH :** Versi upgrade dari VEO 3.1, talking head lebih bagus, realistis untuk mode close up, kurang realistis kalau shot agak jauh, harga menengah
> *Opini Personal : jangan gunakan lagi VEO 3.1, Omni Flash jauh lebih baik dengan harga yang hanya sedikit lebih mahal*
>
> **Kling 2.5 :** Realistis, harga murah, sound effect jelek
>
> **Kling 2.6 :** Realistis, harga menengah, ada sound effect
>
> **Kling Motion Control :** Untuk kebutuhan video joget-joget (meniru gerakan dari video referensi)
>
> **Kling 3.0 :** Realistis, canggih, bisa multi shot, bisa talking head (hanya bahasa inggris dan china) harga menengah
>
> **Kling 3.0 Omni :** Sama seperti Kling 3.0 tapi bisa Omni Reference (Mengupload banyak referensi)
>
> **Seedance 2.0 :** Sangat realistis, sangat canggih, paling mahal, kekurangannya adalah talking head bahasa indonesia yang sering salah ucap

---

## ⚠️ Open conflicts — for the operator to decide

These are places where the personal notes, the repo and vendor claims disagree. `/ugc-clone` follows the rule in **bold** until the operator settles each one.

| # | Topic | Personal notes | Repo / vendor | Rule until settled |
|---|---|---|---|---|
| 1 | Seedance + Bahasa dialogue | Often mispronounces Indonesian | Vendor pages list Indonesian as a lip-sync language; the Seedance audio guide ranks Mandarin > English > JP/KR | **Notes win.** Never the top pick for Bahasa talking-head; name the risk when offered as an alternative. |
| 2 | Kling 3.0 dialogue languages | English + Chinese only | Official guide: zh, en, ja, ko, es | **Either way, no Indonesian.** Kling 3.0 dialogue only for English (or the other four) scripts. |
| 3 | "Veo Omni Flash" | Upgrade of Veo 3.1 | Google ships it as **Gemini Omni Flash** (a separate Gemini Omni family, the de-facto Veo successor); kie slug `gemini-omni-video` | **Same model.** Show it as "Veo/Gemini Omni Flash". |
| 4 | Seedance 2.5 | Not in notes | Repo wires it (kie, 30s, 720p). Higgsfield calls it "a different tool from 2.0, not a newer one" (reference/edit/extension modes, 720p cap) | **Offer only when a single take > 15s is needed.** Untested by the operator — say so. |
| 5 | Kling 3.0 duration | — | Native 3–15s (Kling app, Higgsfield). The repo caps kie runs at 5/10s as a cost guardrail | **Platform-dependent.** 15s on Kling app / Higgsfield; 10s if the operator will paste into the repo's kie flow. |
| 6 | Kling 3.0 Omni, Kling Motion Control, Kling 2.5 | In notes | Not wired in the repo; not in `docs/kie-pricing.md` (kie does host `kling-o3` and Kling Motion Control) | **Recommend freely** (UGC-Clone never generates); cost shown as "check price on the platform". |

---

## Quick picker

Match the **reference video's traits** (from the Gate-1 analysis) to a top pick. Always show 1–2 alternatives with the trade-off.

| Reference trait | Top pick | Alternatives / trade-off |
|---|---|---|
| Talking head, **Bahasa Indonesia** dialogue, close/medium framing | **Veo/Gemini Omni Flash** | Kling 3.0 silent + voiceover added in post (more realistic body motion, no lip-sync) · Seedance 2.0 (most realistic, risk of mispronounced Bahasa) |
| Talking head, **English** dialogue | **Kling 3.0** (realistic, multi-shot, speaks EN) | Omni Flash (best close-up lip-sync) · Seedance 2.0 (top realism, priciest) |
| **No dialogue** (music / ASMR / VO in post), multi-cut routine, demo, b-roll | **Kling 3.0** multi-shot (≤ 6 shots, ≤ 15s) | Seedance 2.0 (more realistic physics, priciest) · Kling 2.6 (cheaper, single shot, good SFX) |
| Must keep **many references** (face angles + product + location) | **Kling 3.0 Omni** (≤ 7 refs, `@` binding) | Seedance 2.0 (`@Image` binding) · Omni Flash (≤ 7 image refs) |
| **Copy exact body motion** — dance, trend choreography, one continuous take | **Kling Motion Control** | — (no other model transfers motion from a video) |
| Wide / full-body shots with dialogue | Kling 3.0 (EN) or split: wide shots silent on Kling, close-ups on Omni Flash in separate clips | Omni Flash is weak on wide shots (notes) |
| Single continuous take **> 15s** | **Seedance 2.5** (≤ 30s, 720p) | Split into ≤ 15s clips on Kling 3.0 / Seedance 2.0 and chain with end/start frames |
| Cheapest acceptable realism, simple motion | **Kling 2.5** (bad SFX — replace audio in post) | Kling 2.6 (SFX included, mid price) |

**Never recommend Veo 3.1** (notes: Omni Flash is far better for slightly more).

---

## Model cards

Each card: **Notes** (operator) · **Strengths / weaknesses** · **Limits** · **References** · **Dialogue** · **Native prompt syntax** · **Where** · **Price**.

### Veo / Gemini Omni Flash
- **Notes:** best talking head, realistic in close-up, less realistic when the shot is further away; mid price.
- **Strengths:** lip-synced dialogue including Bahasa Indonesia; audio (dialogue, SFX, ambience) generated in the same pass; holds character and voice; conversational editing.
- **Weaknesses:** wide/full-body shots look less real; keep compositions simple.
- **Limits:** kie 4 / 6 / 8 / 10s at 720p / 1080p / 4k; Higgsfield/Runware document 9:16 or 16:9. Match duration to beats — one beat 5–6s, three beats ~8s.
- **References:** up to 7 images, or 1 video + up to 5 images (Higgsfield `gemini_omni`).
- **Dialogue:** quote lines **verbatim** in straight quotes and name the delivery. A paraphrase ("she talks about her skin") makes the model improvise an unrelated line.
- **Native prompt syntax:** 3–4 sentences using a five-element scaffold — **shot framing + camera move** (first sentence), style, lighting, location, action. Audio as a directing sentence. Say `no music` / `no dialogue` to switch defaults off.
  ```
  Handheld smartphone medium close-up, slight natural shake, a 8-second shot. Raw UGC look, real skin texture. Warm dim tungsten light in a walk-in closet. She taps the gel into her cheek and says in Bahasa Indonesia, casual and warm: "Ini gel cream-nya dingin banget, langsung seger." Soft room tone, no music.
  ```
- **Where:** kie `gemini-omni-video` · Higgsfield `gemini_omni` · Google Flow / Gemini app.
- **Price:** kie flat per clip — 8s @1080p 105 cr (~Rp 8.560). See `docs/kie-pricing.md`.

### Veo 3.1 — legacy, do not recommend
- **Notes:** speaks Bahasa, less realistic than Kling; "jangan gunakan lagi".
- Kept only as the repo's automatic fallback (`veo3_fast`, 4/6/8s). Never a recommendation.

### Kling 2.5
- **Notes:** realistic, cheap, bad sound effects.
- **Use:** budget single shots; plan to replace the audio in post. 5 / 10s.
- **Where:** Kling app, kie (Kling 2.5 Turbo). **Price:** not in `docs/kie-pricing.md` — check the platform.

### Kling 2.6
- **Notes:** realistic, mid price, has sound effects.
- **Strengths:** realistic motion with SFX; single start image.
- **Limits:** 5 / 10s; no aspect-ratio parameter on kie (the start frame sets the shape); no dialogue.
- **Syntax:** one flowing paragraph describing the motion, not the static frame.
- **Where:** kie `kling-2.6/image-to-video` · Higgsfield `kling_2_6` · Kling app. **Price:** kie 5s 110 cr / 10s 220 cr with audio.

### Kling 3.0
- **Notes:** realistic, advanced, multi-shot, talking head in English and Chinese only; mid price.
- **Strengths:** native multi-shot (up to 6 shots in one output); native ambient audio; start + end frame; strong motion realism.
- **Limits:** 3–15s (Kling app / Higgsfield; the repo's kie flow caps 10s); 16:9, 9:16, 1:1 only; 720p / 1080p; `std` / `pro` modes.
- **References:** start image + end image.
- **Dialogue:** zh / en / ja / ko / es (per the official guide) — **not Indonesian**. Format: `Name (tone): line`.
- **Native prompt syntax:** header line (aspect, duration, look, continuity rules), then numbered shots, then audio and an avoid line. The skin1004 precedent `brands/skin1004/product-ugc/kirana-skin100-remake/kling-prompt-en.txt` is the house format:
  ```
  9:16 vertical, 15s, raw UGC skincare routine filmed on a phone front camera, handheld micro-shake, quick jump cuts. Start exactly on the start frame. Keep the same woman, face, hair, outfit, location and light throughout.

  Shot 1 (0-4.5s): ...
  Shot 2 (4.5-6.8s): Jump cut, same framing. ...

  Audio: ... No voiceover, no dialogue.
  Avoid: face changing between shots, extra fingers, warped or misspelled label, text overlays, subtitles.
  ```
- **Where:** kie `kling-3.0/video` · Higgsfield `kling_3_0` · Kling app (Custom Multi-Shot panel). **Price:** kie 27 cr/s @1080p with audio.

### Kling 3.0 Omni
- **Notes:** like Kling 3.0 plus Omni Reference (upload many references).
- **Strengths:** binds characters, products and locations to `@` references; "Elements" built from ~4 angles (front, ¾ left, ¾ right, back) give the model a 3D sense of identity; element voice binding.
- **Limits:** up to 15s; multi-shot; up to 7 images/elements without a video, 4 with a video; character video element 3–8s.
- **Tip for this repo:** crop the character's `multiangle.png` panels into separate images and upload them as one Element.
- **Native prompt syntax:** refer to uploads with `@` names inside the shot text — `@Kirana picks up @Product and ...`.
- **Where:** Kling app · kie `kling-o3`. **Price:** not in `docs/kie-pricing.md`.

### Kling Motion Control
- **Notes:** for dance videos — copies the movement from a reference video.
- **How it works:** character image + motion reference video → the character performs that motion.
- **Limits:** reference video 3–30s, **one continuous shot**, no cuts, minimal camera movement, moderate speed. Output up to 30s when orientation follows the video, 10s when it follows the image. Optional prompt ≤ 2,500 characters for background, clothing and lighting.
- **Fit for UGC-Clone:** only when the reference is a single continuous performance take. A multi-cut UGC reference has to be trimmed to one continuous segment first.
- **Where:** Kling app · kie (Kling 2.6 / 3.0 Motion Control). **Price:** check the platform.

### Seedance 2.0 (and 2.0 Fast)
- **Notes:** very realistic, very advanced, most expensive; Bahasa talking head often mispronounced.
- **Strengths:** state-of-the-art realism and physics; consistent identity; multi-shot; takes image, start/end image, video and audio references (Higgsfield).
- **Limits:** 4–15s. Higgsfield `seedance_2_0` up to 4K. kie `bytedance/seedance-2-fast` is 480p / 720p only and the repo sends a first frame only.
- **Dialogue:** `Character speaks in <language>: "..."` — 5–10 words per line; keep the camera locked, face medium close-up, front or ¾; don't give head-movement instructions during speech. Mix line: `Dialogue clean and prominent, music low, ambient subtle.`
- **Native prompt syntax:** state **number of shots, total duration and aspect ratio at the top**. Bind each reference to one job — `@Image1 is the character's face only; @Image2 is the product only`. Number shots (`Shot 1`, `Shot 2`) — Seedance 2.0 reads shot numbers better than timestamps. Add `no 3D, no cartoon, no VFX` if skin goes plastic. For locked POV: `no cuts, no zoom, natural head movement`.
- **Where:** Higgsfield `seedance_2_0` (default serious video there) · kie `bytedance/seedance-2-fast` · Dreamina / CapCut. **Price:** kie Fast 24.8 cr/s @720p; Higgsfield bills its own credits.

### Seedance 2.5
- **Strengths:** up to 30s in one generation; up to 50 references (30 image + 10 video + 10 audio); strong continuity; reads a closing frame.
- **Weaknesses:** 720p native (upscale after); morphing in fast action; infers a voice from the character's look (can pick an unwanted accent — correct it with a plain word such as "American", not "American English").
- **Syntax:** longer, deliberately paced prompts with timestamped beats of ~8–10s each (`0–8s`, `8–20s`, `20–30s`). **2.0 prompts can break on 2.5** — write for the model you pick.
- **Where:** kie `bytedance/seedance-2-5` (repo pins 720p) · Higgsfield `seedance_2_5` · Dreamina. **Price:** kie 63 cr/s @720p — the priciest option here.

### Start-frame image models

| Model | Use for the start frame when… | Where |
|---|---|---|
| **Nano Banana Pro** (default) | Face + product must both stay exact; hard briefs | kie `nano-banana-pro` · Higgsfield `nano_banana_pro` |
| Nano Banana 2 | Same job, cheaper; up to 14 references | kie `nano-banana-2` · Higgsfield `nano_banana_2` |
| GPT Image 2 | The frame must contain rendered text (rare — text belongs in post) | kie `gpt-image-2-image-to-image` · Higgsfield `gpt_image_2` |
| Seedream 4.5 | Face-anchored edit into a complex new scene | Higgsfield `seedream_4_5` |

Start-frame prompt rules: pass the **headshot first, product second** (then `multiangle.png` / `fullbody.png` if the model takes more); write an explicit identity lock ("the exact same woman as reference 1 — same face, skin tone, hair"); quote the label text; describe the first frame of the scene, not the whole action.

---

## Universal prompt craft

From the operator's cheat sheets (`Referensi/Other Insight/`) and the research above.

**The reference image drives motion more than the prompt.** A well-chosen start frame (and end frame, where supported) does most of the work; the prompt directs what the frame cannot.

**Models over-cinematize.** The director's two jobs: create realistic movement, and prevent strange movement. For UGC, prefer the small natural moves below over sweeping camera work.

| Camera movement | Keyword |
|---|---|
| Static | `static camera`, `locked-off shot`, `no camera movement` |
| Forward / back | `push in` / `dolly in` · `pull out` / `dolly out` |
| Handheld | `subtle handheld camera, very slight natural shake` |
| Pan / tilt | `pan left` / `pan right` · `tilt up` / `tilt down` |
| Follow | `soft follow camera`, `gentle tracking` |

| Subject micro-movement | Keyword |
|---|---|
| Breathing | `breathing motion`, `natural breathe` |
| Head | `micro head movement`, `subtle head movement` · `slight head turn and return` |
| Weight | `slight weight shift` |
| Hands | `natural hand adjustment movement` (add the specific action) |

| Angle | Keyword | Note |
|---|---|---|
| Front | `front view`, `symmetrical composition` | |
| ¾ | `three quarter view` | AI often confuses left and right — expect retries |
| Profile | `side profile` | Face drifts at this angle — needs a master face (`multiangle.png`) |
| Back | `back view` | |
| Vertical | `eye level` · `slightly high angle` · `slightly low angle` · `extreme high angle` · `extreme low angle` · `dutch angle` | Use "slightly" when the result feels exaggerated |
| Special | `over-the-shoulder shot` · `peek angle` · `frame within a frame` · `reflection shot` · `shot through foreground object` | |

| Framing | Keyword | Covers |
|---|---|---|
| Full body | `full body shot` | feet to head |
| Medium | `medium shot` | thighs to head |
| Medium close-up | `medium close up shot` | waist to head |
| Close-up | `close up shot to [area]` | a named area |
| Extreme close-up | `extreme close up to [area]` | |
| Wide | `wide shot` · `extreme wide shot` | environment dominates |

**Dialogue.** Quote the exact line, name the language and delivery, keep 5–10 words per line, and plan roughly 2.5 words per second of screen time. Lip-sync is best in medium close-up, front or ¾, locked or barely moving camera.

**Text.** Never ask a video model for text overlays, captions or subtitles — they garble. Say `no text overlays, no subtitles` and put all on-screen text in the post-production notes. For the product label, quote its exact text and add `stays sharp and legible, never warped`.

**Length.** Single-shot prompts stay under ~200 tokens. Multi-shot prompts (Kling 3.0, Seedance) can run longer because each shot is short.

**Phrasing.** Most models have no negative prompt. Phrase positively in the body ("tack sharp", "real skin texture"), and keep one closing `Avoid:` line for the failures that matter (face changing between shots, extra fingers, warped label).

---

## Where the prompt gets pasted

| Platform | How references attach |
|---|---|
| **Higgsfield web** | Seedance 2.0: image / start / end / video / audio slots. Kling 3.0: start + end image. Omni Flash: up to 7 image references (+1 video). |
| **kie.ai** (playground or the repo's scripts) | Omni Flash `image_urls` ≤ 7; Kling 3.0 `image_urls` (start/end); Seedance 2.0 Fast first frame only; Seedance 2.5 first + last frame. |
| **Official apps** | Kling app: Custom Multi-Shot panel; Element Library for Kling 3.0 Omni (`@Element`). Dreamina / CapCut: Seedance `@Image1`-style binding. Google Flow / Gemini app: Omni Flash. |

## Prices

Credits, USD and IDR for every kie model the repo runs live in **`docs/kie-pricing.md`**. Models not listed there (Kling 2.5, Kling 3.0 Omni, Kling Motion Control, Higgsfield-billed runs) are shown as "check price on the platform" — never invented.

---

## Sources

- Operator field notes (kept outside this repo); cheat sheets in `Referensi/Other Insight/`
- [Kling VIDEO 3.0 Model Guide](https://kling.ai/quickstart/klingai-video-3-model-user-guide) · [Kling VIDEO 3.0 Omni Guide](https://kling.ai/quickstart/klingai-video-3-omni-model-user-guide) · [Kling Motion Control User Guide](https://kling.ai/quickstart/motion-control-user-guide) · [Kling Element Library](https://kling.ai/quickstart/klingai-element-library-3-user-guide)
- [Higgsfield — Seedance 2.0 Prompting Guide](https://higgsfield.ai/blog/seedance-prompting-guide) · [Prompt Architects — How to prompt Seedance 2.5 and 2.0](https://prompt-architects.com/blog/216-how-to-prompt-seedance-2-0) · [Cutout.pro — Seedance 2.0 Audio Guide](https://www.cutout.pro/learn/blog-seedance-2-0-audio-guide/)
- [MindStudio — Seedance 2.5 Review](https://www.mindstudio.ai/blog/seedance-2-5-review-guide) · [Dreamina — Seedance 2.5 vs 2.0](https://dreamina.capcut.com/seedance/seedance-2-5-vs-seedance-2-0) · [Seedance 2.5 supported languages](https://www.seedance.tv/blog/seedance-2-5-supported-languages)
- [Runware — Cinematic prompting for Gemini Omni Flash](https://runware.ai/docs/models/google-gemini-omni-flash/guides/cinematic-prompting) · [Gemini Omni Flash review](https://www.buildfastwithai.com/blogs/gemini-omni-flash-review-google-ai-video-model-2026)

---
name: lao-voice
description: Free Lao neural voiceover (TTS) skill using Microsoft Edge Neural TTS (lo-LA-ChanthavongNeural and lo-LA-KeomanyNeural) plus FFmpeg character voice shaping (16 distinct Lao character profiles), loudness normalization, Telegram/WhatsApp .ogg voice notes, 30fps lip-sync envelopes, and direct integration with motion-muse / Remotion video projects (including Noto Sans Lao font setup). Use whenever the user asks for Lao voiceover, Lao narration, Lao dubbing, multi-character Lao cartoon voices, or Lao speech replies (ພາກສຽງລາວ, ອ່ານອອກສຽງພາສາລາວ, ສຽງພາກລາວ) without paid API keys.
---

# Lao Voice (`lao-voice`)

Generate natural, free **Lao (ພາສາລາວ)** voiceovers and multi-character cartoon voices locally using **Microsoft Edge Neural TTS (`edge-tts`) + `FFmpeg`** — zero API keys, zero paid subscriptions. Designed to work standalone (chat bots, Telegram/WhatsApp voice notes, standalone narrations) and as a drop-in Lao voice + font companion for **`motion-muse` / `toon-story` / Remotion**.

`SKILL_DIR` below is the folder containing this `SKILL.md`. If unknown:
```bash
SKILL_DIR=$(dirname "$(find ~/.openbot ~/.openclaw ~/.claude ~/.agents ~ -path '*/lao-voice/scripts/lao_voice.py' 2>/dev/null | head -1)")/..
```

## 0. Setup check (first run)

```bash
bash "$SKILL_DIR/scripts/setup.sh"
```
Checks `python3`, `ffmpeg`, `curl`, and `edge-tts` (supports `edge-tts` CLI, `python3 -m edge_tts`, or `uvx edge-tts`). Stop and report if it prints `MISSING:` instead of `READY: lao-voice`.

## 1. Quick single-line voiceover (`speak`)

Use for standalone Lao narration, bot voice replies, or single dialogue lines:

```bash
# Standard MP3 (for video, web, general playback)
python3 "$SKILL_DIR/scripts/lao_voice.py" speak \
  --profile narrator \
  --text "ສະບາຍດີ! ຍິນດີຕ້ອນຮັບສູ່ຊ່ອງຂອງພວກເຮົາ!" \
  --out ./out/hello.mp3

# Telegram / WhatsApp voice note (.ogg Opus 48kHz)
python3 "$SKILL_DIR/scripts/lao_voice.py" speak \
  --profile female \
  --text "ມື້ນີ້ອາກາດດີຫຼາຍເດີ້!" \
  --out ./out/reply.ogg

# With 30fps lip-sync envelope JSON
python3 "$SKILL_DIR/scripts/lao_voice.py" speak \
  --profile xieng \
  --text "ອໍ້! ຄິດອອກແລ້ວ!" \
  --out ./out/idea.mp3 \
  --envelope ./out/idea.env.json
```

Useful flags:
- `--profile <name>` — character timbre preset (run `python3 "$SKILL_DIR/scripts/lao_voice.py" profiles` to inspect all presets)
- `--voice`, `--rate`, `--pitch`, `--af` — override base Edge voice, speed (`+8%`, `-6%`), pitch (`+10Hz`, `-8Hz`), or FFmpeg filter chain
- `--text-file <path>` — read Lao text from a UTF-8 file instead of `--text`
- `--lufs -16` — loudness target (default `-16` LUFS)
- `--raw` — skip FFmpeg character EQ/pitch shaping
- `--json` — print machine-readable JSON metadata (`file`, `duration`, `frames`)

## 2. Built-in Lao character voice profiles

Edge TTS has two native Lao neural voices (`lo-LA-ChanthavongNeural` male and `lo-LA-KeomanyNeural` female). `lao_voice.py` shapes pitch, speed, formant (`asetrate` + `atempo`), EQ, and reverb with FFmpeg so multiple characters sound clearly distinct:

| Profile | Base Voice | Character / Mood |
|---|---|---|
| `narrator` / `host` | Male (`Chanthavong`) | Crisp presenter / TikTok & YouTube host |
| `female` / `mother` | Female (`Keomany`) | Natural warm adult woman |
| `female_bright` | Female (`Keomany`) | Cheerful, lively young woman |
| `female_dream` | Female (`Keomany`) | Soft dreamy voice with subtle echo |
| `male` / `father` | Male (`Chanthavong`) | Warm adult man / father |
| `youth` / `xieng` | Male (`Chanthavong`) | Bright, quick-witted youth / boy / novice |
| `youth_excited` | Male (`Chanthavong`) | Energetic / smug / excited youth |
| `king` | Male (`Chanthavong`) | Deep, commanding older royal baritone |
| `merchant` | Male (`Chanthavong`) | Booming, boastful adult male |
| `elder` | Male (`Chanthavong`) | Calm, warm, unhurried elder / abbot |
| `oracle` | Male (`Chanthavong`) | Deep mystical sage with hall echo |
| `shock` | Male (`Chanthavong`) | Exasperated / shocked comic male reaction |

## 3. Pairing with `motion-muse` / `toon-story` (Remotion videos)

When the user asks for a **Lao-language video or 3D cartoon episode** using `motion-muse`, **use `lao-voice` automatically instead of ElevenLabs** (do not ask to pay for ElevenLabs unless the user explicitly asks for ElevenLabs).

### Step A — Fetch the Lao font (`Noto Sans Lao`)
`motion-muse` installs Thai fonts by default. Always add `Noto Sans Lao` for Lao titles and subtitles:
```bash
bash "$SKILL_DIR/scripts/fetch-lao-font.sh" <project>/public/fonts
```
Load `fonts/NotoSansLao[wdth,wght].ttf` with `FontFace` (`weight: '100 900'`) + Remotion `delayRender`/`continueRender`, and set `lineHeight >= 1.45` so Lao upper vowels and tone marks never clip. For per-word/character kinetic animation, segment with `Intl.Segmenter('lo', { granularity: 'grapheme' })`.

### Step B — Batch-build voiced episodes (`build`)
Write `src/<slug>/script.json` (see `$SKILL_DIR/examples/demo-script.json` for schema), then run:
```bash
python3 "$SKILL_DIR/scripts/lao_voice.py" build <project> <project>/src/<slug>/script.json
```
What `build` generates automatically:
1. All character voice MP3 files under `<project>/public/<voDir>/<line-id>.mp3` (with SHA-256 caching so unchanged lines aren't regenerated)
2. `timeline.json` — frame-accurate `scenes`, `lines` (with `file` and 30fps RMS lip-sync `env` compatible with `motion-muse`'s `StoryAudio` and `mouthOf()`), `sfx`, `music`, `cues`, and `total`
3. `storyboard.json` — ready for `motion-muse`'s `director.py render`
4. `<Comp>.vtt` — captions synced to exact voiced timestamps

Per-line fields supported in `script.json`:
- `who`: speaker ID (matched against `cast[who].profile`, then built-in profile name, else `narrator`)
- `profile`: optional per-line emotion/profile override (e.g. `"youth_excited"`, `"shock"`, `"female_dream"`)
- `text`: on-screen subtitle text (may include `\n` and `«»`)
- `speak`: optional spoken Lao override if pronunciation differs from display text (e.g. spelling out numbers or English brand names phonetically in Lao)
- `hold` / `gap`: pause in seconds after the line (default `0.25`)
- `cue`: optional cue name recorded in `timeline.cues` at the exact scene-local start frame of the line
- `voices`: optional top-level map in `script.json` to define custom character profiles (`{ "voice", "rate", "pitch", "af" }`)

## 4. Lao TTS quality rules

- **Clean spoken text:** `lao_voice.py` automatically turns `\n` into `, `, strips `«»`, and removes the silent cancellation mark `໌` (`U+0ECC`) for cleaner Edge TTS pronunciation (pass `--no-clean` to disable).
- **Numbers & English terms:** For crisp Lao narration, write numbers and English names in Lao words inside `speak` (e.g. `ຕອນທີສາມ` instead of `ຕອນທີ 3`, `ເອໄອ` instead of `AI`) while keeping clean formatting in `text`.
- **BGM mixing:** Duck background music to ~`0.15–0.22` volume while voice lines play (`<StoryAudio tl={T} voice={1.0} duck={0.36} />`).
- **Network required:** `edge-tts` connects to Microsoft Edge's online neural TTS service; `lao_voice.py` retries automatically up to 4 times on transient network glitches.

---
name: lao-voice
description: 100% free Lao multi-voice TTS skill using Microsoft Edge Neural TTS (lo-LA-ChanthavongNeural and lo-LA-KeomanyNeural), 31 verified FFmpeg character & effect voice profiles (male, female, kids, elders, giant, ghost, robot, radio, whisper, underwater), optional free local zero-shot voice cloning via Seed-VC (--clone any 5s voice clip for unlimited realistic Lao voices), Telegram/WhatsApp .ogg voice notes, 30fps lip-sync envelopes, and direct motion-muse / Remotion integration with Noto Sans Lao font setup. Use whenever the user asks for Lao voiceover, Lao narration, Lao dubbing, multi-character Lao cartoon voices, or Lao speech replies (ພາກສຽງລາວ, ສຽງພາກລາວ, ສຽງຫຼາຍແບບ) without paid API keys.
---

# Lao Voice (`lao-voice`)

Generate natural, **100% free Lao (ພາສາລາວ)** voiceovers with **31 verified character & effect profiles (28 distinct voices)** — plus **unlimited custom realistic voices for free** via local zero-shot voice cloning (`Seed-VC`) — zero API keys, zero paid subscriptions. Works standalone (OpenBot, OpenClaw, Telegram/WhatsApp voice notes, CLI) and as a drop-in Lao voice + font companion for **`motion-muse` / `toon-story` / Remotion**.

`SKILL_DIR` below is the folder containing this `SKILL.md`. If unknown:
```bash
SKILL_DIR=$(dirname "$(find ~/.openbot ~/.openclaw ~/.claude ~/.agents ~ -path '*/lao-voice/scripts/lao_voice.py' 2>/dev/null | head -1)")/..
```

## 0. Setup check (first run)

```bash
bash "$SKILL_DIR/scripts/setup.sh"
```
Checks `python3`, `ffmpeg`, `curl`, and `edge-tts` (supports `edge-tts` CLI, `python3 -m edge_tts`, or `uvx edge-tts`). Stop and report if it prints `MISSING:` instead of `READY: lao-voice`.

## 1. Quick single-line voiceover (`speak`) & voice audition (`preview`)

```bash
# Standard MP3 (for video, web, general playback)
python3 "$SKILL_DIR/scripts/lao_voice.py" speak \
  --profile narrator \
  --text "ສະບາຍດີ! ຍິນດີຕ້ອນຮັບສູ່ຊ່ອງຂອງພວກເຮົາ!" \
  --out ./out/hello.mp3

# Telegram / WhatsApp voice note (.ogg Opus 48kHz)
python3 "$SKILL_DIR/scripts/lao_voice.py" speak \
  --profile female_bright \
  --text "ມື້ນີ້ອາກາດດີຫຼາຍເດີ້!" \
  --out ./out/reply.ogg

# Generate sample MP3 clips to listen & compare multiple voices
python3 "$SKILL_DIR/scripts/lao_voice.py" preview \
  --profiles narrator,female,grandma,xieng,boy,girl,king,giant,ghost,robot \
  --out ./previews
```

Useful flags for `speak`:
- `--profile <name>` — pick from 31 free built-in character/effect presets (`python3 "$SKILL_DIR/scripts/lao_voice.py" profiles`)
- `--voice`, `--rate`, `--pitch`, `--af` — override base voice (`lo-LA-ChanthavongNeural` / `lo-LA-KeomanyNeural`), speed (`+8%`, `-6%`), pitch (`+10Hz`, `-8Hz`), or FFmpeg filter chain
- `--clone <ref.wav>` — free local zero-shot voice cloning via Seed-VC (see Section 3)
- `--envelope <out.json>` — export 30fps RMS lip-sync envelope JSON
- `--text-file <path>`, `--lufs -16`, `--raw`, `--no-clean`, `--json`

## 2. 31 Built-in free Lao character & effect profiles

Run `python3 "$SKILL_DIR/scripts/lao_voice.py" profiles` (or `--category male|female|youth|fx`) to inspect all presets:

| Category | Profiles |
|---|---|
| **Male (`male`)** | `narrator`, `host`, `news`, `storyteller`, `male`, `father`, `king`, `merchant`, `elder`, `oracle`, `shock` |
| **Female (`female`)** | `female`, `mother`, `female_bright`, `female_soft`, `female_dream`, `female_shock`, `grandma` |
| **Youth & Kids (`youth`)** | `youth`, `xieng`, `youth_excited`, `boy`, `girl` |
| **Cartoon & FX (`fx`)** | `giant`, `chipmunk`, `ghost`, `robot`, `radio`, `megaphone`, `whisper`, `underwater` |

## 3. Unlimited realistic free voices via local Seed-VC (`--clone`)

To turn Lao Edge TTS speech into **any human or character voice for free** (while keeping 100% accurate native Lao pronunciation):
1. One-time install (runs locally on Mac Apple Silicon MPS or CPU, zero training required):
   ```bash
   bash "$SKILL_DIR/scripts/setup-seed-vc.sh"
   ```
2. Pass any 5–15 second clean voice sample (`.wav`/`.mp3`, even in another language) to `--clone`:
   ```bash
   python3 "$SKILL_DIR/scripts/lao_voice.py" speak \
     --profile narrator \
     --clone ./voices/grandpa_sample.wav \
     --text "ນິທານເລື່ອງນີ້ເກີດຂຶ້ນດົນມາແລ້ວ..." \
     --out ./out/grandpa_lao.mp3
   ```
3. In `build` mode (`script.json`), set `"clone": "voices/grandpa_sample.wav"` inside `cast.<id>` or on individual lines.

## 4. Pairing with `motion-muse` / `toon-story` (Remotion videos)

When the user asks for a **Lao-language video or 3D cartoon episode** using `motion-muse`, **use `lao-voice` automatically instead of ElevenLabs** (do not ask to pay for ElevenLabs unless the user explicitly asks for ElevenLabs).

### Step A — Fetch the Lao font (`Noto Sans Lao`)
```bash
bash "$SKILL_DIR/scripts/fetch-lao-font.sh" <project>/public/fonts
```
Load `fonts/NotoSansLao[wdth,wght].ttf` with `FontFace` (`weight: '100 900'`) + Remotion `delayRender`/`continueRender`, set `lineHeight >= 1.45`, and segment kinetic text with `Intl.Segmenter('lo', { granularity: 'grapheme' })`.

### Step B — Batch-build voiced episodes (`build`)
Write `src/<slug>/script.json` (see `$SKILL_DIR/examples/demo-script.json`), then run:
```bash
python3 "$SKILL_DIR/scripts/lao_voice.py" build <project> <project>/src/<slug>/script.json
```
Generates:
1. All character voice MP3s under `<project>/public/<voDir>/<line-id>.mp3` (with SHA-256 caching)
2. `timeline.json` — frame-accurate `scenes`, `lines` (with `file` + 30fps lip-sync `env` compatible with `motion-muse`'s `StoryAudio` and `mouthOf()`), `sfx`, `music`, `cues`, `total`
3. `storyboard.json` — ready for `motion-muse`'s `director.py render`
4. `<Comp>.vtt` — captions synced to exact voiced timestamps

Per-line / cast fields supported in `script.json`: `who`, `profile`, `clone`, `text`, `speak`, `hold`/`gap`, `cue`, and top-level custom `voices` map.

## 5. Lao TTS quality rules

- **Clean spoken text:** `lao_voice.py` turns `\n` into `, `, strips `«»`, and removes the silent mark `໌` (`U+0ECC`) automatically (`--no-clean` to disable).
- **Numbers & English terms:** Write numbers and English names phonetically in Lao inside `speak` (e.g. `ຕອນທີສາມ`, `ເອໄອ`) while keeping clean display formatting in `text`.
- **BGM mixing:** Duck background music to ~`0.15–0.22` volume while voice lines play (`<StoryAudio tl={T} voice={1.0} duck={0.36} />`).

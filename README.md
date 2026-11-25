# lao-voice

Agent skill for **free Lao neural voiceover (ພາກສຽງພາສາລາວຟຣີ)** using **Microsoft Edge Neural TTS (`edge-tts`) + `FFmpeg`** — zero API keys, 16 distinct Lao character voice profiles, Telegram/WhatsApp `.ogg` voice notes, 30fps lip-sync envelopes, and direct integration with **[peichh/motion-muse](https://github.com/peichh/motion-muse)** (including automatic `Noto Sans Lao` font setup).

## Features / ຄວາມສາມາດຫຼັກ

- **ຟຣີ 100% ບໍ່ຕ້ອງໃຊ້ API Key:** ໃຊ້ສຽງພາສາລາວຂອງ Microsoft Edge Neural TTS (`lo-LA-ChanthavongNeural` ຊາຍ & `lo-LA-KeomanyNeural` ຍິງ)
- **16 ໂປຣໄຟລ໌ສຽງຕົວລະຄອນ:** ປັບ pitch, speed, formant, EQ ແລະ echo ດ້ວຍ FFmpeg (`narrator`, `female`, `female_bright`, `female_dream`, `male`, `youth`/`xieng`, `youth_excited`, `king`, `merchant`, `elder`, `oracle`, `shock` ຯລຯ)
- **ພ້ອມສຳລັບບອທແຊັດ & ວິດີໂອ:** ສົ່ງອອກໄດ້ທັງ `.mp3`, `.ogg` (Opus 48kHz ສຳລັບ Voice Note ໃນ Telegram/WhatsApp), ແລະ `.wav` ພ້ອມປັບຄວາມດັງ `-16 LUFS`
- **ໃຊ້ຄູ່ກັບ `motion-muse` / Remotion ໄດ້ທັນທີ:** ຄຳສັ່ງ `build` ສ້າງໄຟລ໌ສຽງທັງຕອນ + `timeline.json` (ພ້ອມຄ່າຂະຫຍັບປາກ 30fps `env`) + `storyboard.json` + ຊັບໄຕເຕິລ `.vtt` ພ້ອມສະຄຣິບໂຫຼດຟອນ `Noto Sans Lao`

---

## Install / ການຕິດຕັ້ງ

- **Any agent supporting `npx skills` (OpenBot, OpenClaw, Cursor, Claude Code, etc.):**
  ```bash
  npx skills add songfreedom/lao-voice
  ```
- **Claude Code / OpenBot / OpenClaw (manual):**
  ```bash
  git clone https://github.com/songfreedom/lao-voice
  cp -r lao-voice/skills/lao-voice ~/.claude/skills/lao-voice
  # ຫຼື copy ເຂົ້າໂຟນເດີ skills/ ຂອງ OpenBot / OpenClaw
  ```
- **First-run dependency check:**
  ```bash
  bash skills/lao-voice/scripts/setup.sh
  ```
  Requires `python3`, `ffmpeg`, `curl`, and `edge-tts` (`pip install edge-tts` or `uvx edge-tts`).

---

## Usage / ຕົວຢ່າງການໃຊ້

### 1. Ask your AI Agent directly
- *"ໃຊ້ lao-voice ພາກສຽງລາວປະໂຫຍກນີ້ເປັນສຽງຜູ້ຍິງ: ສະບາຍດີ ຕ້ອນຮັບສູ່ຊ່ອງຂອງພວກເຮົາ"*
- *"ໃຊ້ motion-muse ຄູ່ກັບ lao-voice ສ້າງກາຕູນ 3D 9:16 ພາສາລາວ ພາກສຽງຫຼາຍຕົວລະຄອນ"*

### 2. Run via CLI directly
```bash
# List all 16 character voice profiles
python3 skills/lao-voice/scripts/lao_voice.py profiles

# Synthesize a single Lao voice clip (.mp3 or .ogg for Telegram/WhatsApp)
python3 skills/lao-voice/scripts/lao_voice.py speak \
  --profile xieng \
  --text "ອໍ້! ຄິດອອກແລ້ວ!" \
  --out ./idea.mp3

python3 skills/lao-voice/scripts/lao_voice.py speak \
  --profile female \
  --text "ສະບາຍດີ ມີຫຍັງໃຫ້ຊ່ວຍບໍ່?" \
  --out ./reply.ogg

# Batch-build a voiced motion-muse / Remotion episode (VO + timeline.json + storyboard.json + .vtt)
python3 skills/lao-voice/scripts/lao_voice.py build <project_dir> <project_dir>/src/<slug>/script.json

# Fetch Noto Sans Lao font (SIL OFL) for Remotion projects
bash skills/lao-voice/scripts/fetch-lao-font.sh <project_dir>/public/fonts
```

## License

MIT

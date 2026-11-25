# lao-voice

Agent skill for **100% free Lao multi-voice TTS (ພາກສຽງພາສາລາວຟຣີຫຼາຍແບບ)** — zero API keys, zero subscriptions. Combines **Microsoft Edge Neural TTS (`edge-tts`)**, **Google Translate Lao TTS (`gTTS`)**, **33 FFmpeg character & FX voice profiles**, optional **free local zero-shot voice cloning (`Seed-VC`)**, Telegram/WhatsApp `.ogg` voice notes, 30fps lip-sync envelopes, and direct integration with **[peichh/motion-muse](https://github.com/peichh/motion-muse)** + `Noto Sans Lao` font setup.

## 3 ຊັ້ນຄວາມຫຼາກຫຼາຍຂອງສຽງ (ຟຣີ 100% ທັງໝົດ!)

1. **3 ສຽງພາສາລາວຕົ້ນສະບັບຟຣີ:** Microsoft Edge ຊາຍ (`lo-LA-ChanthavongNeural`), ຍິງ (`lo-LA-KeomanyNeural`) + Google Lao (`gTTS`)
2. **33 ໂປຣໄຟລ໌ສຽງຕົວລະຄອນ & ເອັບເຟັກ (ພ້ອມໃຊ້ທັນທີ):**
   - **ຜູ້ຊາຍ:** `narrator`, `host`, `news`, `storyteller`, `male`, `father`, `king`, `merchant`, `elder`, `oracle`, `shock`
   - **ຜູ້ຍິງ:** `female`, `mother`, `female_bright`, `female_soft`, `female_dream`, `female_shock`, `grandma`
   - **ເດັກນ້ອຍ & ໄວລຸ້ນ:** `youth`, `xieng`, `youth_excited`, `boy`, `girl`
   - **ສຽງ Google Lao:** `google`, `google_kid`
   - **ກາຕູນ & ເອັບເຟັກ:** `giant` (ຍັກ), `chipmunk` (ສຽງໜູ/ກະຮອກ), `ghost` (ຜີ), `robot` (ຫຸ່ນຍົນ), `radio` (ວິທະຍຸ/ໂທລະສັບ), `megaphone` (ໂທລະໂຂ່ງ), `whisper` (ກະຊິບ), `underwater` (ໃຕ້ນ້ຳ)
3. **ໂຄລນສຽງຄົນຈິງບໍ່ຈຳກັດຟຣີ (`--clone` ຜ່ານ `Seed-VC` Local):** ເອົາສຽງພາສາລາວຈາກ `edge-tts` ໄປປ່ຽນເປັນສຽງໃຜກໍໄດ້ຈາກຄລິບສຽງຕົວຢ່າງ 5–15 ວິນາທີ (ຮັນເທິງ Mac Apple Silicon / CPU ຟຣີ ບໍ່ຕ້ອງເທຣນ)

---

## Install / ການຕິດຕັ້ງ

- **OpenBot / OpenClaw / Cursor / Claude Code (`npx skills`):**
  ```bash
  npx skills add songfreedom/lao-voice
  ```
- **Manual:**
  ```bash
  git clone https://github.com/songfreedom/lao-voice
  cp -r lao-voice/skills/lao-voice ~/.claude/skills/lao-voice
  ```
- **First-run check:**
  ```bash
  bash skills/lao-voice/scripts/setup.sh
  ```
- *(Optional)* ຕິດຕັ້ງ **Seed-VC** ຖ້າຕ້ອງການໂຄລນສຽງບໍ່ຈຳກັດຟຣີ (`--clone`):
  ```bash
  bash skills/lao-voice/scripts/setup-seed-vc.sh
  ```

---

## Usage / ຕົວຢ່າງການໃຊ້

```bash
# 1. ເບິ່ງທັງ 33 ໂປຣໄຟລ໌ສຽງ
python3 skills/lao-voice/scripts/lao_voice.py profiles

# 2. ສ້າງໄຟລ໌ທົດລອງຟັງຫຼາຍໆສຽງພ້ອມກັນ
python3 skills/lao-voice/scripts/lao_voice.py preview \
  --profiles narrator,female_bright,grandma,xieng,boy,girl,king,giant,ghost,robot \
  --out ./previews

# 3. ພາກສຽງ 1 ປະໂຫຍກ (mp3 ຫຼື .ogg ສຳລັບ Telegram/WhatsApp Voice Note)
python3 skills/lao-voice/scripts/lao_voice.py speak --profile xieng --text "ອໍ້! ຄິດອອກແລ້ວ!" --out ./idea.mp3
python3 skills/lao-voice/scripts/lao_voice.py speak --profile grandma --text "ຫຼານເອີຍ ມາກິນເຂົ້າເດີ້!" --out ./grandma.ogg
python3 skills/lao-voice/scripts/lao_voice.py speak --profile google --text "ສະບາຍດີ ນີ້ແມ່ນສຽງລາວອີກແບບ!" --out ./google.mp3

# 4. ໂຄລນສຽງຟຣີຈາກຄລິບຕົວຢ່າງ 5-15 ວິນາທີ (ຕ້ອງຮັນ setup-seed-vc.sh ກ່ອນ)
python3 skills/lao-voice/scripts/lao_voice.py speak \
  --profile narrator --clone ./my_actor.wav \
  --text "ນິທານເລື່ອງນີ້ເກີດຂຶ້ນດົນມາແລ້ວ!" --out ./cloned.mp3

# 5. ສ້າງສຽງທັງຕອນ + timeline.json (lip-sync 30fps) + storyboard.json + .vtt ສຳລັບ motion-muse
python3 skills/lao-voice/scripts/lao_voice.py build <project_dir> <project_dir>/src/<slug>/script.json

# 6. ໂຫຼດຟອນ Noto Sans Lao ເຂົ້າໂປຣເຈັກ Remotion
bash skills/lao-voice/scripts/fetch-lao-font.sh <project_dir>/public/fonts
```

## License

MIT

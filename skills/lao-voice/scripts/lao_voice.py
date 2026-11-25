#!/usr/bin/env python3
"""
lao_voice.py — 100% Free Lao Multi-Voice TTS + FFmpeg Character Shaping + Optional Local Voice Cloning (Seed-VC) + 30fps Lip-Sync.
Works standalone (OpenBot / OpenClaw / Telegram / CLI) and directly with motion-muse / Remotion.

Subcommands:
  profiles                              List all 30 built-in free Lao character & effect voice profiles
  speak    --text "..." --out out.mp3   Synthesize a single Lao voice line (mp3/ogg/wav)
  preview  --out ./previews             Generate sample MP3 clips to audition multiple voice profiles
  build    <project> <script.json>      Batch-build VO MP3s + timeline.json + storyboard.json + .vtt
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import wave
from typing import Any

# Free Lao base voices:
#   - edge-tts: lo-LA-ChanthavongNeural (Male), lo-LA-KeomanyNeural (Female)
#   - gtts:     Google Translate Lao ('lo') — a 3rd distinct native Lao base voice
# Plus FFmpeg formant/EQ/FX shaping for 30 distinct voices, and optional local Seed-VC (--clone ref.wav)
# for unlimited zero-shot realistic human voices in native Lao!
PROFILES: dict[str, dict[str, str]] = {
    # --- Male realistic / story personas (Edge Male base) ---
    "narrator": {
        "cat": "male",
        "engine": "edge",
        "desc": "Crisp, clear male presenter / channel host",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+6%",
        "pitch": "+2Hz",
        "af": "highpass=f=85,equalizer=f=3200:width_type=o:width=1.4:g=2.0",
    },
    "host": {
        "cat": "male",
        "engine": "edge",
        "desc": "Alias of narrator (TikTok / YouTube host)",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+6%",
        "pitch": "+2Hz",
        "af": "highpass=f=85,equalizer=f=3200:width_type=o:width=1.4:g=2.0",
    },
    "news": {
        "cat": "male",
        "engine": "edge",
        "desc": "Punchy broadcast / documentary announcer",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+4%",
        "pitch": "-2Hz",
        "af": "aresample=24000,asetrate=24000*0.97,atempo=1.0309,aresample=44100,highpass=f=80,equalizer=f=200:width_type=o:width=1.3:g=2.2,equalizer=f=3800:width_type=o:width=1.4:g=2.4,acompressor=threshold=-18dB:ratio=3:attack=8:release=80",
    },
    "storyteller": {
        "cat": "male",
        "engine": "edge",
        "desc": "Warm, gentle, unhurried folklore narrator",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "-5%",
        "pitch": "-4Hz",
        "af": "aresample=24000,asetrate=24000*0.95,atempo=1.0526,aresample=44100,highpass=f=75,equalizer=f=240:width_type=o:width=1.4:g=2.5,equalizer=f=2800:width_type=o:width=1.5:g=1.2",
    },
    "male": {
        "cat": "male",
        "engine": "edge",
        "desc": "Warm adult male / father",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+2%",
        "pitch": "-3Hz",
        "af": "aresample=24000,asetrate=24000*0.94,atempo=1.0638,aresample=44100,highpass=f=75,equalizer=f=220:width_type=o:width=1.4:g=2.5",
    },
    "father": {
        "cat": "male",
        "engine": "edge",
        "desc": "Alias of male (warm adult father)",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+2%",
        "pitch": "-3Hz",
        "af": "aresample=24000,asetrate=24000*0.94,atempo=1.0638,aresample=44100,highpass=f=75,equalizer=f=220:width_type=o:width=1.4:g=2.5",
    },
    "king": {
        "cat": "male",
        "engine": "edge",
        "desc": "Deep, proud, commanding older royal baritone",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "-2%",
        "pitch": "-10Hz",
        "af": "aresample=24000,asetrate=24000*0.92,atempo=1.0870,aresample=44100,equalizer=f=170:t=q:w=1.1:g=4.0,equalizer=f=3200:t=q:w=1.5:g=1.2",
    },
    "merchant": {
        "cat": "male",
        "engine": "edge",
        "desc": "Booming, boastful adult male merchant",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+5%",
        "pitch": "-6Hz",
        "af": "aresample=24000,asetrate=24000*0.90,atempo=1.1111,aresample=44100,highpass=f=70,equalizer=f=200:width_type=o:width=1.4:g=3.0",
    },
    "elder": {
        "cat": "male",
        "engine": "edge",
        "desc": "Calm, warm, wise elder / abbot / grandpa",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "-6%",
        "pitch": "-5Hz",
        "af": "aresample=24000,asetrate=24000*0.89,atempo=1.1236,aresample=44100,highpass=f=70,equalizer=f=200:width_type=o:width=1.4:g=2.6",
    },
    "oracle": {
        "cat": "male",
        "engine": "edge",
        "desc": "Deep mystical sage / astrologer with subtle hall echo",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "-10%",
        "pitch": "-6Hz",
        "af": "aresample=24000,asetrate=24000*0.86,atempo=1.1628,aresample=44100,highpass=f=65,equalizer=f=180:width_type=o:width=1.4:g=3.0,aecho=0.8:0.88:55:0.14",
    },
    "shock": {
        "cat": "male",
        "engine": "edge",
        "desc": "Exasperated / panicked comic male reaction",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+4%",
        "pitch": "+1Hz",
        "af": "aresample=24000,asetrate=24000*0.93,atempo=1.0753,aresample=44100,highpass=f=80,equalizer=f=2400:width_type=o:width=1.4:g=2.6",
    },

    # --- Youth & Kids ---
    "youth": {
        "cat": "youth",
        "engine": "edge",
        "desc": "Bright, agile young boy / clever trickster / novice",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+5%",
        "pitch": "+8Hz",
        "af": "aresample=24000,asetrate=24000*1.13,atempo=0.8850,aresample=44100,highpass=f=125,treble=g=2.0",
    },
    "xieng": {
        "cat": "youth",
        "engine": "edge",
        "desc": "Playful clever trickster (Xieng Mieng)",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+7%",
        "pitch": "+10Hz",
        "af": "aresample=24000,asetrate=24000*1.15,atempo=0.8696,aresample=44100,highpass=f=130,treble=g=2.4",
    },
    "youth_excited": {
        "cat": "youth",
        "engine": "edge",
        "desc": "Fast, excited or smug youth delivery",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+10%",
        "pitch": "+12Hz",
        "af": "aresample=24000,asetrate=24000*1.16,atempo=0.8621,aresample=44100,highpass=f=130,treble=g=2.5",
    },
    "boy": {
        "cat": "youth",
        "engine": "edge",
        "desc": "Cute young child (boy)",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+6%",
        "pitch": "+14Hz",
        "af": "aresample=24000,asetrate=24000*1.22,atempo=0.8197,aresample=44100,highpass=f=150,treble=g=2.5",
    },
    "girl": {
        "cat": "youth",
        "engine": "edge",
        "desc": "Cute lively little girl",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "+7%",
        "pitch": "+10Hz",
        "af": "aresample=24000,asetrate=24000*1.16,atempo=0.8621,aresample=44100,highpass=f=160,treble=g=2.2",
    },

    # --- Female personas (Edge Female base) ---
    "female": {
        "cat": "female",
        "engine": "edge",
        "desc": "Natural warm adult female voice",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "+0%",
        "pitch": "+2Hz",
        "af": "highpass=f=110,equalizer=f=2800:width_type=o:width=1.5:g=1.5",
    },
    "mother": {
        "cat": "female",
        "engine": "edge",
        "desc": "Alias of female (gentle mother)",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "+0%",
        "pitch": "+2Hz",
        "af": "highpass=f=110,equalizer=f=2800:width_type=o:width=1.5:g=1.5",
    },
    "female_bright": {
        "cat": "female",
        "engine": "edge",
        "desc": "Cheerful, energetic young woman / TikTok presenter",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "+8%",
        "pitch": "+6Hz",
        "af": "aresample=24000,asetrate=24000*1.05,atempo=0.9524,aresample=44100,highpass=f=120,treble=g=2.0",
    },
    "female_soft": {
        "cat": "female",
        "engine": "edge",
        "desc": "Calm, gentle, soothing female narrator",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "-7%",
        "pitch": "-2Hz",
        "af": "highpass=f=100,lowpass=f=7500,equalizer=f=260:width_type=o:width=1.4:g=1.8",
    },
    "female_dream": {
        "cat": "female",
        "engine": "edge",
        "desc": "Soft dreamy female voice with echo/reverb",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "-4%",
        "pitch": "+2Hz",
        "af": "highpass=f=110,aecho=0.8:0.86:95|185:0.24|0.12",
    },
    "female_shock": {
        "cat": "female",
        "engine": "edge",
        "desc": "Surprised / scolding / dramatic female reaction",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "+10%",
        "pitch": "+8Hz",
        "af": "aresample=24000,asetrate=24000*1.06,atempo=0.9434,aresample=44100,highpass=f=130,equalizer=f=3000:width_type=o:width=1.4:g=2.8",
    },
    "grandma": {
        "cat": "female",
        "engine": "edge",
        "desc": "Warm, slower older grandmother / aunty",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "-9%",
        "pitch": "-8Hz",
        "af": "aresample=24000,asetrate=24000*0.89,atempo=1.1236,aresample=44100,highpass=f=90,equalizer=f=240:width_type=o:width=1.3:g=2.6,lowpass=f=6500",
    },

    # --- 3rd Native Free Base Voice (Google Translate TTS 'lo') ---
    "google": {
        "cat": "gtts",
        "engine": "gtts",
        "desc": "Google Translate Lao voice (3rd distinct native Lao base voice!)",
        "voice": "lo",
        "rate": "+0%",
        "pitch": "+0Hz",
        "af": "highpass=f=95,equalizer=f=3000:width_type=o:width=1.5:g=1.8",
    },
    "google_kid": {
        "cat": "gtts",
        "engine": "gtts",
        "desc": "Playful child variant using Google Lao base voice",
        "voice": "lo",
        "rate": "+0%",
        "pitch": "+0Hz",
        "af": "aresample=24000,asetrate=24000*1.18,atempo=0.8475,aresample=44100,highpass=f=140,treble=g=2.0",
    },

    # --- Cartoon, Fantasy & Sound-FX Voices (Edge + FFmpeg FX) ---
    "giant": {
        "cat": "fx",
        "engine": "edge",
        "desc": "Huge booming giant / ogre / monster voice",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "-14%",
        "pitch": "-16Hz",
        "af": "aresample=24000,asetrate=24000*0.76,atempo=1.3158,aresample=44100,equalizer=f=120:width_type=o:width=1.2:g=5.0,aecho=0.8:0.85:45:0.22",
    },
    "chipmunk": {
        "cat": "fx",
        "engine": "edge",
        "desc": "Hyper-cute high-pitched cartoon critter / squirrel",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "+12%",
        "pitch": "+18Hz",
        "af": "aresample=24000,asetrate=24000*1.36,atempo=0.7353,aresample=44100,highpass=f=220,treble=g=3.0",
    },
    "ghost": {
        "cat": "fx",
        "engine": "edge",
        "desc": "Eerie trembling spirit / ghost voice with haunt echo",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "-12%",
        "pitch": "-4Hz",
        "af": "aresample=24000,asetrate=24000*0.92,atempo=1.0870,aresample=44100,vibrato=f=5.5:d=0.35,aecho=0.8:0.88:110|220:0.35|0.22",
    },
    "robot": {
        "cat": "fx",
        "engine": "edge",
        "desc": "Metallic sci-fi AI / robot voice",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+4%",
        "pitch": "-2Hz",
        "af": "highpass=f=240,lowpass=f=3600,flanger=delay=4:depth=2:regen=45:speed=2.5,aphaser=in_gain=0.8:out_gain=0.9:delay=3:decay=0.5:speed=1.8,acompressor=threshold=-16dB:ratio=4",
    },
    "radio": {
        "cat": "fx",
        "engine": "edge",
        "desc": "Vintage radio / telephone call voice",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+4%",
        "pitch": "+0Hz",
        "af": "highpass=f=340,lowpass=f=2700,equalizer=f=1400:width_type=o:width=1.2:g=4.0,acompressor=threshold=-20dB:ratio=6:attack=5:release=60",
    },
    "megaphone": {
        "cat": "fx",
        "engine": "edge",
        "desc": "Village loudspeaker / temple PA megaphone",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+3%",
        "pitch": "+2Hz",
        "af": "highpass=f=420,lowpass=f=3200,equalizer=f=1800:width_type=o:width=1.0:g=6.0,acompressor=threshold=-22dB:ratio=8,aecho=0.8:0.85:70|150:0.25|0.12",
    },
    "whisper": {
        "cat": "fx",
        "engine": "edge",
        "desc": "Soft secret whisper / ASMR-style hush",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "-10%",
        "pitch": "-3Hz",
        "af": "highpass=f=240,equalizer=f=320:width_type=o:width=1.5:g=-6.0,equalizer=f=4500:width_type=o:width=1.5:g=4.5,acompressor=threshold=-24dB:ratio=3",
    },
    "underwater": {
        "cat": "fx",
        "engine": "edge",
        "desc": "Muffled voice talking from inside a pond / underwater",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "-4%",
        "pitch": "-6Hz",
        "af": "lowpass=f=680,vibrato=f=3.2:d=0.25,aecho=0.85:0.88:35:0.2",
    },
}


def find_edge_tts_cmd() -> list[str]:
    """Return the command prefix to run edge-tts on this machine."""
    if shutil.which("edge-tts"):
        return ["edge-tts"]
    probe = subprocess.run(
        [sys.executable, "-c", "import edge_tts"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if probe.returncode == 0:
        return [sys.executable, "-m", "edge_tts"]
    if shutil.which("uvx"):
        return ["uvx", "--quiet", "edge-tts"]
    raise RuntimeError(
        "edge-tts not found. Install it with either:\n"
        "  pip install edge-tts\n"
        "or install uv (https://docs.astral.sh/uv/) so `uvx edge-tts` works."
    )


def find_gtts_cmd() -> list[str]:
    """Return the command prefix to run gtts-cli on this machine."""
    if shutil.which("gtts-cli"):
        return ["gtts-cli"]
    probe = subprocess.run(
        [sys.executable, "-c", "import gtts"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if probe.returncode == 0:
        return [sys.executable, "-m", "gtts.cli"]
    if shutil.which("uvx"):
        return ["uvx", "--quiet", "--from", "gTTS", "gtts-cli"]
    raise RuntimeError(
        "gTTS not found. Install it with:\n"
        "  pip install gTTS\n"
        "or install uv so `uvx --from gTTS gtts-cli` works."
    )


def find_seed_vc_dir(explicit: str | None = None) -> pathlib.Path:
    """Locate a local Plachtaa/seed-vc checkout for free zero-shot voice cloning."""
    candidates: list[pathlib.Path] = []
    if explicit:
        candidates.append(pathlib.Path(explicit).expanduser())
    if os.environ.get("SEED_VC_DIR"):
        candidates.append(pathlib.Path(os.environ["SEED_VC_DIR"]).expanduser())
    candidates.extend([
        pathlib.Path.home() / "seed-vc",
        pathlib.Path.home() / "skills" / "seed-vc",
        pathlib.Path(__file__).resolve().parent.parent / "seed-vc",
    ])
    for c in candidates:
        if (c / "inference.py").is_file():
            return c.resolve()
    raise RuntimeError(
        "Seed-VC not found for --clone. Install it once (100% free, local) with:\n"
        "  bash scripts/setup-seed-vc.sh\n"
        "or set SEED_VC_DIR=/path/to/seed-vc (https://github.com/Plachtaa/seed-vc)."
    )


def require_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg not found. Install it with:\n"
            "  macOS:   brew install ffmpeg\n"
            "  Ubuntu:  sudo apt-get install -y ffmpeg\n"
            "  Windows: winget install ffmpeg"
        )


def clean_lao_tts(text: str) -> str:
    """Clean subtitle/display Lao text for natural TTS pronunciation."""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\s*\n+\s*", ", ", t)
    # Remove display quotation brackets and Lao cancellation mark (໌) that can trip TTS
    t = t.replace("«", " ").replace("»", " ").replace("“", " ").replace("”", " ")
    t = t.replace("\u0ecc", "")
    # Collapse repeated exclamation/question marks & tidy spacing around punctuation
    t = re.sub(r"!{2,}", "!", t)
    t = re.sub(r"\?{2,}", "?", t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,!?])", r"\1", t).strip()
    return t


def resolve_profile(
    profile_name: str,
    custom_profiles: dict[str, dict[str, str]] | None = None,
    *,
    engine: str | None = None,
    voice: str | None = None,
    rate: str | None = None,
    pitch: str | None = None,
    af: str | None = None,
) -> dict[str, str]:
    merged = dict(PROFILES)
    if custom_profiles:
        merged.update(custom_profiles)
    if profile_name not in merged:
        avail = ", ".join(sorted(merged.keys()))
        raise ValueError(f"Unknown voice profile '{profile_name}'. Available: {avail}")
    p = dict(merged[profile_name])
    p.setdefault("engine", "edge")
    if engine:
        p["engine"] = engine
        if engine == "gtts" and not voice:
            p["voice"] = "lo"
    if voice:
        p["voice"] = voice
    if rate:
        p["rate"] = rate
    if pitch:
        p["pitch"] = pitch
    if af is not None:
        p["af"] = af
    return p


def extract_envelope(audio_path: pathlib.Path, fps: int = 30) -> tuple[float, list[float]]:
    """Return (duration_seconds, list_of_fps_mouth_amplitudes_0_to_1)."""
    with tempfile.TemporaryDirectory(prefix="lao_env_") as td:
        wav_path = pathlib.Path(td) / "probe.wav"
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error", "-i", str(audio_path),
                "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le",
                str(wav_path),
            ],
            check=True,
        )
        with wave.open(str(wav_path), "rb") as w:
            sr = w.getframerate()
            n = w.getnframes()
            raw = w.readframes(n)
    samples = struct.unpack(f"<{n}h", raw) if n else ()
    dur_s = n / sr if sr else 0.0
    n_frames = max(1, math.ceil(dur_s * fps))
    spf = sr / fps

    rms: list[float] = []
    for f in range(n_frames):
        a = int(f * spf)
        b = min(n, int((f + 1) * spf))
        if b <= a:
            rms.append(0.0)
        else:
            acc = sum(s * s for s in samples[a:b]) / (b - a)
            rms.append(math.sqrt(acc) / 32768.0)

    peak = max(rms) if rms else 1.0
    if peak < 1e-5:
        peak = 1.0
    norm = [min(1.0, (v / peak) ** 0.72) for v in rms]
    env: list[float] = []
    prev = 0.0
    for v in norm:
        cur = 0.62 * v + 0.38 * prev
        env.append(round(0.0 if cur < 0.06 else cur, 3))
        prev = cur
    return dur_s, env


def run_seed_vc(
    src_audio: pathlib.Path,
    ref_audio: pathlib.Path,
    out_dir: pathlib.Path,
    seed_vc_dir: pathlib.Path,
    *,
    steps: int = 25,
    semi_tone_shift: int = 0,
) -> pathlib.Path:
    """Convert src_audio to the target timbre of ref_audio using local Seed-VC."""
    if not ref_audio.is_file():
        raise FileNotFoundError(f"Clone reference audio not found: {ref_audio}")
    out_dir.mkdir(parents=True, exist_ok=True)
    # Prefer Seed-VC's own venv python if setup-seed-vc.sh created one
    py_bin = seed_vc_dir / ".venv" / "bin" / "python"
    python_exe = str(py_bin) if py_bin.is_file() else sys.executable

    before = set(out_dir.glob("*.wav"))
    cmd = [
        python_exe,
        str(seed_vc_dir / "inference.py"),
        "--source", str(src_audio),
        "--target", str(ref_audio),
        "--output", str(out_dir),
        "--diffusion-steps", str(steps),
        "--length-adjust", "1.0",
        "--inference-cfg-rate", "0.7",
        "--f0-condition", "False",
        "--semi-tone-shift", str(semi_tone_shift),
    ]
    subprocess.run(cmd, cwd=str(seed_vc_dir), check=True)
    after = sorted(set(out_dir.glob("*.wav")) - before, key=lambda p: p.stat().st_mtime)
    if not after:
        after = sorted(out_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime)
    if not after:
        raise RuntimeError(f"Seed-VC produced no .wav output in {out_dir}")
    return after[-1]


def synthesize_line(
    text: str,
    out_path: pathlib.Path,
    prof: dict[str, str],
    *,
    fmt: str | None = None,
    lufs: float = -16.0,
    raw_passthrough: bool = False,
    retries: int = 4,
    channels: int = 1,
    clone_ref: pathlib.Path | None = None,
    seed_vc_dir: pathlib.Path | None = None,
    vc_steps: int = 25,
    vc_shift: int = 0,
) -> pathlib.Path:
    """Generate a single Lao voice audio file via Edge TTS / gTTS (+ optional Seed-VC) + FFmpeg."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ext = (fmt or out_path.suffix.lstrip(".") or "mp3").lower()
    if ext not in ("mp3", "ogg", "opus", "wav"):
        raise ValueError(f"Unsupported output format '{ext}'. Use mp3, ogg, or wav.")

    engine = prof.get("engine", "edge").lower()
    if engine == "edge":
        tts_cmd_prefix = find_edge_tts_cmd()
    elif engine == "gtts":
        tts_cmd_prefix = find_gtts_cmd()
    else:
        raise ValueError(f"Unsupported engine '{engine}'. Use 'edge' or 'gtts'.")

    with tempfile.TemporaryDirectory(prefix="lao_tts_") as td:
        td_path = pathlib.Path(td)
        raw_mp3 = td_path / "raw.mp3"
        last_err = ""
        for attempt in range(retries):
            try:
                if engine == "edge":
                    cmd = [
                        *tts_cmd_prefix,
                        "--voice", prof["voice"],
                        f"--rate={prof.get('rate', '+0%')}",
                        f"--pitch={prof.get('pitch', '+0Hz')}",
                        "--text", text,
                        "--write-media", str(raw_mp3),
                    ]
                else:
                    cmd = [
                        *tts_cmd_prefix,
                        "--lang", prof.get("voice", "lo") or "lo",
                        "--output", str(raw_mp3),
                        text,
                    ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                if raw_mp3.exists() and raw_mp3.stat().st_size > 500:
                    break
                last_err = f"empty audio returned by {engine}"
            except subprocess.CalledProcessError as e:
                last_err = e.stderr.decode(errors="ignore").strip()
            time.sleep(1.5 * (attempt + 1))
        else:
            raise RuntimeError(f"{engine} TTS failed after {retries} attempts: {last_err}")

        stage_in = raw_mp3
        if clone_ref is not None:
            # Convert TTS output to WAV for Seed-VC, then clone target speaker timbre
            src_wav = td_path / "src.wav"
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(raw_mp3), "-ar", "24000", "-ac", "1", str(src_wav)],
                check=True,
            )
            svc_dir = seed_vc_dir or find_seed_vc_dir()
            stage_in = run_seed_vc(
                src_wav,
                clone_ref,
                td_path / "vc_out",
                svc_dir,
                steps=vc_steps,
                semi_tone_shift=vc_shift,
            )

        if raw_passthrough and clone_ref is None and ext == "mp3":
            shutil.copy2(stage_in, out_path)
            return out_path

        filters: list[str] = []
        # When cloning via Seed-VC, skip formant-shifting profile AF unless user explicitly passed custom --af
        if not raw_passthrough and prof.get("af") and clone_ref is None:
            filters.append(prof["af"])
        filters.extend([
            "silenceremove=start_periods=1:start_silence=0.04:start_threshold=-46dB:"
            "stop_periods=-1:stop_duration=0.14:stop_threshold=-46dB",
            f"loudnorm=I={lufs}:TP=-1.5:LRA=9",
            "apad=pad_dur=0.06",
        ])
        af_chain = ",".join(filters)

        ff_cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(stage_in), "-af", af_chain]
        if ext == "mp3":
            ff_cmd += ["-ar", "44100", "-ac", str(channels), "-b:a", "192k", str(out_path)]
        elif ext in ("ogg", "opus"):
            ff_cmd += ["-ar", "48000", "-ac", "1", "-c:a", "libopus", "-b:a", "64k", "-vbr", "on", str(out_path)]
        elif ext == "wav":
            ff_cmd += ["-ar", "44100", "-ac", str(channels), "-c:a", "pcm_s16le", str(out_path)]
        subprocess.run(ff_cmd, check=True)

    return out_path


def fmt_vtt_ts(sec: float) -> str:
    ms = int(round(max(0.0, sec) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def cache_key(text: str, prof: dict[str, str], lufs: float, clone_ref: pathlib.Path | None = None) -> str:
    clone_sig = ""
    if clone_ref and clone_ref.is_file():
        st = clone_ref.stat()
        clone_sig = f"{clone_ref.resolve()}:{st.st_size}:{int(st.st_mtime)}"
    payload = json.dumps(
        {
            "text": text,
            "engine": prof.get("engine", "edge"),
            "voice": prof["voice"],
            "rate": prof.get("rate", "+0%"),
            "pitch": prof.get("pitch", "+0Hz"),
            "af": prof.get("af", ""),
            "lufs": lufs,
            "clone": clone_sig,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def cmd_profiles(args: argparse.Namespace) -> None:
    selected = {
        k: v for k, v in PROFILES.items()
        if not args.category or v.get("cat") == args.category
    }
    if args.json:
        print(json.dumps(selected, indent=2, ensure_ascii=False))
        return
    print(f"{'PROFILE':<15} {'CAT':<7} {'ENGINE':<6} {'BASE VOICE':<25} DESCRIPTION")
    print("-" * 100)
    for name, p in selected.items():
        print(f"{name:<15} {p.get('cat',''):<7} {p.get('engine','edge'):<6} {p['voice']:<25} {p['desc']}")
    print(f"\nTotal: {len(selected)} free Lao voice profiles (plus --clone <ref.wav> via Seed-VC for unlimited voices).")


def cmd_speak(args: argparse.Namespace) -> None:
    require_ffmpeg()

    text = args.text
    if args.text_file:
        text = pathlib.Path(args.text_file).read_text(encoding="utf-8")
    if not text or not text.strip():
        sys.exit("Error: provide --text or --text-file with non-empty Lao text.")

    spoken = text.strip() if args.no_clean else clean_lao_tts(text)
    prof = resolve_profile(
        args.profile,
        engine=args.engine,
        voice=args.voice,
        rate=args.rate,
        pitch=args.pitch,
        af=args.af,
    )
    clone_ref = pathlib.Path(args.clone).expanduser().resolve() if args.clone else None
    svc_dir = find_seed_vc_dir(args.seed_vc_dir) if clone_ref else None

    out_path = pathlib.Path(args.out).expanduser().resolve()
    synthesize_line(
        spoken,
        out_path,
        prof,
        fmt=args.format,
        lufs=args.lufs,
        raw_passthrough=args.raw,
        channels=2 if args.stereo else 1,
        clone_ref=clone_ref,
        seed_vc_dir=svc_dir,
        vc_steps=args.vc_steps,
        vc_shift=args.vc_shift,
    )
    dur_s, env = extract_envelope(out_path, fps=args.fps)

    if args.envelope:
        env_path = pathlib.Path(args.envelope).expanduser().resolve()
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.write_text(
            json.dumps(
                {
                    "file": str(out_path),
                    "profile": args.profile,
                    "engine": prof.get("engine", "edge"),
                    "voice": prof["voice"],
                    "clone": str(clone_ref) if clone_ref else None,
                    "fps": args.fps,
                    "duration": round(dur_s, 4),
                    "frames": len(env),
                    "env": env,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    result = {
        "ok": True,
        "file": str(out_path),
        "profile": args.profile,
        "engine": prof.get("engine", "edge"),
        "voice": prof["voice"],
        "clone": str(clone_ref) if clone_ref else None,
        "duration": round(dur_s, 3),
        "frames": len(env),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        tag = f" + clone:{clone_ref.name}" if clone_ref else ""
        print(f"OK {out_path} ({args.profile} / {prof.get('engine','edge')}:{prof['voice']}{tag}, {dur_s:.2f}s, {len(env)} fr @ {args.fps}fps)")


def cmd_preview(args: argparse.Namespace) -> None:
    """Generate sample audio files for multiple profiles so the user can audition voices."""
    require_ffmpeg()
    out_dir = pathlib.Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.profiles:
        names = [x.strip() for x in args.profiles.split(",") if x.strip()]
    elif args.category:
        names = [k for k, v in PROFILES.items() if v.get("cat") == args.category]
    else:
        names = ["narrator", "female", "female_bright", "grandma", "xieng", "boy", "girl", "king", "elder", "giant", "ghost", "robot", "radio"]

    spoken = clean_lao_tts(args.text)
    for name in names:
        prof = resolve_profile(name)
        dst = out_dir / f"{name}.mp3"
        try:
            synthesize_line(spoken, dst, prof, fmt="mp3", lufs=args.lufs)
            print(f"  [OK] {dst.name:<22} ({prof.get('engine','edge')}) — {prof['desc']}")
        except Exception as e:
            print(f"  [ERR] {name}: {e}", file=sys.stderr)
    print(f"\nDONE! Audition your clips in: {out_dir}")


def cmd_build(args: argparse.Namespace) -> None:
    require_ffmpeg()

    proj = pathlib.Path(args.project).expanduser().resolve()
    sp = pathlib.Path(args.script).expanduser().resolve()
    sc: dict[str, Any] = json.loads(sp.read_text(encoding="utf-8"))

    fps = int(sc.get("fps", 30))
    width = int(sc.get("width", 1080))
    height = int(sc.get("height", 1920))
    comp = sc.get("comp", sp.stem)
    vo_subdir = args.vo_dir or sc.get("voDir", "audio/vo")
    vo_abs = proj / "public" / vo_subdir
    vo_abs.mkdir(parents=True, exist_ok=True)

    cache_file = vo_abs / ".lao-voice-cache.json"
    cache: dict[str, str] = {}
    if cache_file.exists() and not args.force:
        try:
            cache = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    custom_voices: dict[str, dict[str, str]] = sc.get("voices", {})
    cast: dict[str, dict[str, Any]] = sc.get("cast", {})
    lufs = float(sc.get("lufs", args.lufs))
    svc_dir_cache: pathlib.Path | None = None

    F = lambda sec: int(round(float(sec) * fps))

    timeline_scenes: list[dict[str, Any]] = []
    timeline_lines: list[dict[str, Any]] = []
    timeline_sfx: list[dict[str, Any]] = []
    sb_scenes: list[dict[str, Any]] = []
    cues: dict[str, int] = {}
    cursor = 0

    for scene in sc.get("scenes", []):
        sid = scene["id"]
        sc_start = cursor
        lead_f = F(scene.get("lead", 0.4))
        pad_f = F(scene.get("pad", 0.45))
        min_f = F(scene.get("min", 0.0))

        for fx in scene.get("sfx", []):
            timeline_sfx.append({
                "file": fx["file"],
                "from": max(0, sc_start + F(fx.get("at", 0.0))),
                "volume": fx.get("volume", 0.6),
                "scene": sid,
            })

        cur = sc_start + lead_f
        for idx, ln in enumerate(scene.get("lines", []), 1):
            lid = ln.get("id", f"{sid}-{idx}")
            who = ln.get("who", "narrator")
            display_text = ln.get("text", "")
            raw_speak = ln.get("speak") or display_text
            if not raw_speak.strip():
                continue
            spoken = raw_speak.strip() if ln.get("noClean") else clean_lao_tts(raw_speak)

            cast_entry = cast.get(who, {}) if isinstance(cast.get(who), dict) else {}
            prof_name = (
                ln.get("profile")
                or cast_entry.get("profile")
                or (who if (who in PROFILES or who in custom_voices) else "narrator")
            )
            prof = resolve_profile(
                prof_name,
                custom_profiles=custom_voices,
                engine=ln.get("engine") or cast_entry.get("engine"),
                voice=ln.get("voice"),
                rate=ln.get("rate"),
                pitch=ln.get("pitch"),
                af=ln.get("af"),
            )

            # Optional free Seed-VC voice cloning per-line or per-character
            clone_spec = ln.get("clone") or cast_entry.get("clone")
            clone_ref: pathlib.Path | None = None
            if clone_spec:
                cp = pathlib.Path(clone_spec).expanduser()
                clone_ref = cp if cp.is_absolute() else (proj / cp).resolve()

            out_mp3 = vo_abs / f"{lid}.mp3"
            rel_file = f"{vo_subdir.rstrip('/')}/{lid}.mp3"
            key = cache_key(spoken, prof, lufs, clone_ref)

            if not args.force and out_mp3.exists() and cache.get(lid) == key:
                status = "CACHE"
            else:
                if clone_ref and svc_dir_cache is None:
                    svc_dir_cache = find_seed_vc_dir(args.seed_vc_dir)
                synthesize_line(
                    spoken,
                    out_mp3,
                    prof,
                    fmt="mp3",
                    lufs=lufs,
                    clone_ref=clone_ref,
                    seed_vc_dir=svc_dir_cache,
                    vc_steps=int(ln.get("vcSteps", 25)),
                    vc_shift=int(ln.get("vcShift", 0)),
                )
                cache[lid] = key
                status = "GEN  "

            dur_s, env = extract_envelope(out_mp3, fps=fps)
            dur_f = max(1, math.ceil(dur_s * fps))
            tag = f"+clone:{clone_ref.name}" if clone_ref else ""
            print(f"  [{status}] {lid:<16} ({who} -> {prof_name}{tag}) {dur_s:.2f}s ({dur_f} fr)", flush=True)

            if "cue" in ln:
                cues[ln["cue"]] = cur - sc_start

            timeline_lines.append({
                "id": lid,
                "scene": sid,
                "who": who,
                "text": display_text,
                "from": cur,
                "dur": dur_f,
                "file": rel_file,
                "env": env,
            })

            for fx in ln.get("sfx", []):
                timeline_sfx.append({
                    "file": fx["file"],
                    "from": max(0, cur + F(fx.get("at", 0.0))),
                    "volume": fx.get("volume", 0.6),
                    "scene": sid,
                })

            gap_sec = ln.get("hold", ln.get("gap", 0.25))
            cur += dur_f + F(gap_sec)

        sc_dur = max(min_f, (cur - sc_start) + pad_f)
        if sc_dur < 1:
            sc_dur = F(2.0)

        timeline_scenes.append({"id": sid, "from": sc_start, "dur": sc_dur})
        sb_scenes.append({
            "id": sid,
            "dur": sc_dur,
            "caps": scene.get("caps", sc.get("caps", ["3d", "toon", "thai-type", "atmosphere"])),
            "shot": scene.get("shot", ""),
            "text": " / ".join(
                ln.get("text", "").replace("\n", " ") for ln in scene.get("lines", []) if ln.get("text")
            ),
            "out": scene.get("out", "cut"),
        })
        cursor = sc_start + sc_dur

    timeline_music: list[dict[str, Any]] = []
    for m in sc.get("music", []):
        entry: dict[str, Any] = {
            "file": m["file"],
            "from": F(m.get("from", 0.0)),
            "volume": m.get("volume", 0.22),
            "trim": m.get("trim", 0),
        }
        if "dur" in m:
            entry["dur"] = F(m["dur"])
        timeline_music.append(entry)

    timeline_sfx.sort(key=lambda x: x["from"])

    tl = {
        "fps": fps,
        "width": width,
        "height": height,
        "scenes": timeline_scenes,
        "lines": timeline_lines,
        "sfx": timeline_sfx,
        "music": timeline_music,
        "cues": cues,
        "total": cursor,
    }

    out_dir = sp.parent
    (out_dir / "timeline.json").write_text(json.dumps(tl, indent=1, ensure_ascii=False), encoding="utf-8")

    sb = {
        "title": sc.get("title", comp),
        "comp": comp,
        "fps": fps,
        "width": width,
        "height": height,
        "brief": sc.get("brief", ""),
        "style": sc.get("style", {"laoFont": "Noto Sans Lao"}),
        "caps": sorted({c for s in sb_scenes for c in s["caps"]}),
        "props": {"subs": not args.no_subs},
        "scenes": sb_scenes,
    }
    (out_dir / "storyboard.json").write_text(json.dumps(sb, indent=1, ensure_ascii=False), encoding="utf-8")

    vtt_lines = ["WEBVTT", ""]
    vtt_idx = 0
    for ln in timeline_lines:
        if not ln["text"]:
            continue
        vtt_idx += 1
        a = fmt_vtt_ts(ln["from"] / fps)
        b = fmt_vtt_ts((ln["from"] + ln["dur"]) / fps)
        vtt_lines += [str(vtt_idx), f"{a} --> {b}", ln["text"], ""]
    (out_dir / f"{comp}.vtt").write_text("\n".join(vtt_lines), encoding="utf-8")

    cache_file.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"\nREADY! {len(timeline_scenes)} scenes, {len(timeline_lines)} voiced lines, "
        f"{len(timeline_sfx)} SFX, total {cursor / fps:.2f}s ({cursor} frames)"
    )
    print(f"  timeline:   {out_dir / 'timeline.json'}")
    print(f"  storyboard: {out_dir / 'storyboard.json'}")
    print(f"  captions:   {out_dir / f'{comp}.vtt'}")


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="lao_voice.py",
        description="100% Free Lao Multi-Voice TTS (Edge TTS + gTTS + FFmpeg FX + Optional Local Seed-VC Cloning).",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_prof = sub.add_parser("profiles", help="List built-in free Lao character & effect voice profiles")
    p_prof.add_argument("--category", "-c", choices=["male", "female", "youth", "gtts", "fx"], help="Filter by category")
    p_prof.add_argument("--json", action="store_true", help="Output as JSON")
    p_prof.set_defaults(func=cmd_profiles)

    p_spk = sub.add_parser("speak", help="Generate a single Lao audio clip (mp3/ogg/wav)")
    p_spk.add_argument("--text", "-t", help="Lao text to speak")
    p_spk.add_argument("--text-file", help="Read Lao text from a UTF-8 file")
    p_spk.add_argument("--out", "-o", required=True, help="Output file path (.mp3, .ogg, or .wav)")
    p_spk.add_argument("--profile", "-p", default="narrator", help="Voice profile name (default: narrator)")
    p_spk.add_argument("--engine", choices=["edge", "gtts"], help="Override base TTS engine (edge or gtts)")
    p_spk.add_argument("--voice", help="Override base voice (e.g. lo-LA-KeomanyNeural)")
    p_spk.add_argument("--rate", help="Override speed (Edge TTS, e.g. +5%%, -10%%)")
    p_spk.add_argument("--pitch", help="Override pitch (Edge TTS, e.g. +8Hz, -6Hz)")
    p_spk.add_argument("--af", help="Override FFmpeg audio filter chain")
    p_spk.add_argument("--clone", help="Reference audio clip (5-15s wav/mp3) for free local Seed-VC voice cloning")
    p_spk.add_argument("--seed-vc-dir", help="Path to local Plachtaa/seed-vc folder (or set SEED_VC_DIR)")
    p_spk.add_argument("--vc-steps", type=int, default=25, help="Seed-VC diffusion steps (10=fast, 25=balanced)")
    p_spk.add_argument("--vc-shift", type=int, default=0, help="Seed-VC semitone shift (default: 0)")
    p_spk.add_argument("--format", "-f", choices=["mp3", "ogg", "wav"], help="Force output format")
    p_spk.add_argument("--lufs", type=float, default=-16.0, help="Target loudness LUFS (default: -16)")
    p_spk.add_argument("--fps", type=int, default=30, help="Envelope FPS (default: 30)")
    p_spk.add_argument("--envelope", help="Optional JSON path to write 30fps RMS lip-sync envelope")
    p_spk.add_argument("--stereo", action="store_true", help="Output stereo instead of mono (mp3/wav)")
    p_spk.add_argument("--raw", action="store_true", help="Skip FFmpeg timbre shaping")
    p_spk.add_argument("--no-clean", action="store_true", help="Send text verbatim to TTS without cleaning")
    p_spk.add_argument("--json", action="store_true", help="Output result summary as JSON")
    p_spk.set_defaults(func=cmd_speak)

    p_prev = sub.add_parser("preview", help="Generate sample MP3s to audition multiple Lao voice profiles")
    p_prev.add_argument("--out", "-o", default="./lao-voice-previews", help="Output folder for preview MP3s")
    p_prev.add_argument("--text", "-t", default="ສະບາຍດີ! ນີ້ແມ່ນສຽງທົດສອບພາສາລາວ", help="Sample Lao phrase")
    p_prev.add_argument("--profiles", help="Comma-separated profile names (e.g. king,xieng,grandma,ghost,robot)")
    p_prev.add_argument("--category", "-c", choices=["male", "female", "youth", "gtts", "fx"], help="Preview all in a category")
    p_prev.add_argument("--lufs", type=float, default=-16.0, help="Target loudness LUFS (default: -16)")
    p_prev.set_defaults(func=cmd_preview)

    p_bld = sub.add_parser("build", help="Batch-build voiced motion-muse episode from script.json")
    p_bld.add_argument("project", help="Remotion project directory (contains public/)")
    p_bld.add_argument("script", help="Path to script.json")
    p_bld.add_argument("--vo-dir", help="Relative dir under public/ for VO MP3s (default: audio/vo)")
    p_bld.add_argument("--seed-vc-dir", help="Path to local Plachtaa/seed-vc folder if script uses 'clone'")
    p_bld.add_argument("--lufs", type=float, default=-16.0, help="Target loudness LUFS (default: -16)")
    p_bld.add_argument("--no-subs", action="store_true", help="Set props.subs=false in storyboard.json")
    p_bld.add_argument("--force", action="store_true", help="Regenerate all lines even if cached")
    p_bld.set_defaults(func=cmd_build)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

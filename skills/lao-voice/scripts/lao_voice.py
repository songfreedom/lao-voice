#!/usr/bin/env python3
"""
lao_voice.py — Free Lao Neural TTS + FFmpeg character voice shaping + 30fps lip-sync.
Works standalone (OpenBot / OpenClaw / Telegram / CLI) and directly with motion-muse / Remotion.

Subcommands:
  profiles                              List built-in Lao character voice profiles
  speak    --text "..." --out out.mp3   Synthesize a single Lao voice line (mp3/ogg/wav)
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

# Built-in Lao character voice profiles (Microsoft Edge Neural TTS + FFmpeg timbre shaping)
# Base voices available in Edge TTS for Lao:
#   - lo-LA-ChanthavongNeural (Male)
#   - lo-LA-KeomanyNeural     (Female)
PROFILES: dict[str, dict[str, str]] = {
    "narrator": {
        "desc": "Crisp, clear male presenter / channel host",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+6%",
        "pitch": "+2Hz",
        "af": "highpass=f=85,equalizer=f=3200:width_type=o:width=1.4:g=2.0",
    },
    "host": {
        "desc": "Alias of narrator (YouTube/TikTok host)",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+6%",
        "pitch": "+2Hz",
        "af": "highpass=f=85,equalizer=f=3200:width_type=o:width=1.4:g=2.0",
    },
    "female": {
        "desc": "Natural warm female voice",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "+0%",
        "pitch": "+2Hz",
        "af": "highpass=f=110,equalizer=f=2800:width_type=o:width=1.5:g=1.5",
    },
    "mother": {
        "desc": "Gentle mother / adult female",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "+0%",
        "pitch": "+2Hz",
        "af": "highpass=f=110,equalizer=f=2800:width_type=o:width=1.5:g=1.5",
    },
    "female_bright": {
        "desc": "Cheerful, energetic young female",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "+8%",
        "pitch": "+6Hz",
        "af": "asetrate=24000*1.05,atempo=0.9524,aresample=44100,highpass=f=120,treble=g=2.0",
    },
    "female_dream": {
        "desc": "Soft dreamy female voice with echo/reverb",
        "voice": "lo-LA-KeomanyNeural",
        "rate": "-4%",
        "pitch": "+2Hz",
        "af": "highpass=f=110,aecho=0.8:0.86:95|185:0.24|0.12",
    },
    "male": {
        "desc": "Warm adult male / father",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+2%",
        "pitch": "-3Hz",
        "af": "asetrate=24000*0.94,atempo=1.0638,aresample=44100,highpass=f=75,equalizer=f=220:width_type=o:width=1.4:g=2.5",
    },
    "father": {
        "desc": "Alias of male (warm adult father)",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+2%",
        "pitch": "-3Hz",
        "af": "asetrate=24000*0.94,atempo=1.0638,aresample=44100,highpass=f=75,equalizer=f=220:width_type=o:width=1.4:g=2.5",
    },
    "youth": {
        "desc": "Bright, agile young boy / clever trickster (Xieng Mieng / novice)",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+5%",
        "pitch": "+8Hz",
        "af": "asetrate=24000*1.13,atempo=0.8850,aresample=44100,highpass=f=125,treble=g=2.0",
    },
    "xieng": {
        "desc": "Alias of youth (clever young trickster)",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+7%",
        "pitch": "+10Hz",
        "af": "asetrate=24000*1.15,atempo=0.8696,aresample=44100,highpass=f=130,treble=g=2.4",
    },
    "youth_excited": {
        "desc": "Fast, excited or smug youth delivery",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+10%",
        "pitch": "+12Hz",
        "af": "asetrate=24000*1.16,atempo=0.8621,aresample=44100,highpass=f=130,treble=g=2.5",
    },
    "king": {
        "desc": "Deep, proud, commanding older royal baritone",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "-2%",
        "pitch": "-10Hz",
        "af": "asetrate=24000*0.92,atempo=1.0870,aresample=44100,equalizer=f=170:t=q:w=1.1:g=4.0,equalizer=f=3200:t=q:w=1.5:g=1.2",
    },
    "merchant": {
        "desc": "Booming, boastful adult male merchant",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+5%",
        "pitch": "-6Hz",
        "af": "asetrate=24000*0.90,atempo=1.1111,aresample=44100,highpass=f=70,equalizer=f=200:width_type=o:width=1.4:g=3.0",
    },
    "elder": {
        "desc": "Calm, warm, unhurried elder / abbot",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "-6%",
        "pitch": "-5Hz",
        "af": "asetrate=24000*0.89,atempo=1.1236,aresample=44100,highpass=f=70,equalizer=f=200:width_type=o:width=1.4:g=2.6",
    },
    "oracle": {
        "desc": "Deep mystical sage / astrologer with subtle hall echo",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "-10%",
        "pitch": "-6Hz",
        "af": "asetrate=24000*0.86,atempo=1.1628,aresample=44100,highpass=f=65,equalizer=f=180:width_type=o:width=1.4:g=3.0,aecho=0.8:0.88:55:0.14",
    },
    "shock": {
        "desc": "Exasperated / shocked comic reaction (adult male)",
        "voice": "lo-LA-ChanthavongNeural",
        "rate": "+3%",
        "pitch": "-1Hz",
        "af": "asetrate=24000*0.92,atempo=1.0870,aresample=44100,highpass=f=75,equalizer=f=230:width_type=o:width=1.4:g=2.4",
    },
}


def find_edge_tts_cmd() -> list[str]:
    """Return the command prefix to run edge-tts on this machine."""
    if shutil.which("edge-tts"):
        return ["edge-tts"]
    # Check if edge_tts is importable in the current Python environment
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


def require_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg not found. Install it with:\n"
            "  macOS:   brew install ffmpeg\n"
            "  Ubuntu:  sudo apt-get install -y ffmpeg\n"
            "  Windows: winget install ffmpeg"
        )


def clean_lao_tts(text: str) -> str:
    """Clean subtitle/display Lao text for natural Edge TTS pronunciation."""
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


def synthesize_line(
    text: str,
    out_path: pathlib.Path,
    prof: dict[str, str],
    *,
    edge_cmd: list[str],
    fmt: str | None = None,
    lufs: float = -16.0,
    raw_passthrough: bool = False,
    retries: int = 4,
    channels: int = 1,
) -> pathlib.Path:
    """Generate a single Lao voice audio file via Edge TTS + FFmpeg."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ext = (fmt or out_path.suffix.lstrip(".") or "mp3").lower()
    if ext not in ("mp3", "ogg", "opus", "wav"):
        raise ValueError(f"Unsupported output format '{ext}'. Use mp3, ogg, or wav.")

    with tempfile.TemporaryDirectory(prefix="lao_tts_") as td:
        raw_mp3 = pathlib.Path(td) / "raw.mp3"
        last_err = ""
        for attempt in range(retries):
            try:
                cmd = [
                    *edge_cmd,
                    "--voice", prof["voice"],
                    f"--rate={prof.get('rate', '+0%')}",
                    f"--pitch={prof.get('pitch', '+0Hz')}",
                    "--text", text,
                    "--write-media", str(raw_mp3),
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                if raw_mp3.exists() and raw_mp3.stat().st_size > 500:
                    break
                last_err = "empty audio returned by edge-tts"
            except subprocess.CalledProcessError as e:
                last_err = e.stderr.decode(errors="ignore").strip()
            time.sleep(1.5 * (attempt + 1))
        else:
            raise RuntimeError(f"edge-tts failed after {retries} attempts: {last_err}")

        if raw_passthrough and ext == "mp3":
            shutil.copy2(raw_mp3, out_path)
            return out_path

        filters: list[str] = []
        if not raw_passthrough and prof.get("af"):
            filters.append(prof["af"])
        filters.extend([
            "silenceremove=start_periods=1:start_silence=0.04:start_threshold=-46dB:"
            "stop_periods=-1:stop_duration=0.14:stop_threshold=-46dB",
            f"loudnorm=I={lufs}:TP=-1.5:LRA=9",
            "apad=pad_dur=0.06",
        ])
        af_chain = ",".join(filters)

        ff_cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(raw_mp3), "-af", af_chain]
        if ext == "mp3":
            ff_cmd += ["-ar", "44100", "-ac", str(channels), "-b:a", "192k", str(out_path)]
        elif ext in ("ogg", "opus"):
            # Telegram/WhatsApp voice-note ready Opus-in-OGG
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


def cache_key(text: str, prof: dict[str, str], lufs: float) -> str:
    payload = json.dumps(
        {
            "text": text,
            "voice": prof["voice"],
            "rate": prof.get("rate", "+0%"),
            "pitch": prof.get("pitch", "+0Hz"),
            "af": prof.get("af", ""),
            "lufs": lufs,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def cmd_profiles(args: argparse.Namespace) -> None:
    if args.json:
        print(json.dumps(PROFILES, indent=2, ensure_ascii=False))
        return
    print(f"{'PROFILE':<15} {'BASE VOICE':<25} {'RATE':<6} {'PITCH':<7} DESCRIPTION")
    print("-" * 92)
    for name, p in PROFILES.items():
        print(f"{name:<15} {p['voice']:<25} {p['rate']:<6} {p['pitch']:<7} {p['desc']}")


def cmd_speak(args: argparse.Namespace) -> None:
    require_ffmpeg()
    edge_cmd = find_edge_tts_cmd()

    text = args.text
    if args.text_file:
        text = pathlib.Path(args.text_file).read_text(encoding="utf-8")
    if not text or not text.strip():
        sys.exit("Error: provide --text or --text-file with non-empty Lao text.")

    spoken = text.strip() if args.no_clean else clean_lao_tts(text)
    prof = resolve_profile(
        args.profile,
        voice=args.voice,
        rate=args.rate,
        pitch=args.pitch,
        af=args.af,
    )
    out_path = pathlib.Path(args.out).expanduser().resolve()
    synthesize_line(
        spoken,
        out_path,
        prof,
        edge_cmd=edge_cmd,
        fmt=args.format,
        lufs=args.lufs,
        raw_passthrough=args.raw,
        channels=2 if args.stereo else 1,
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
                    "voice": prof["voice"],
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
        "voice": prof["voice"],
        "duration": round(dur_s, 3),
        "frames": len(env),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"OK {out_path} ({args.profile} / {prof['voice']}, {dur_s:.2f}s, {len(env)} frames @ {args.fps}fps)")


def cmd_build(args: argparse.Namespace) -> None:
    require_ffmpeg()
    edge_cmd = find_edge_tts_cmd()

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

            # Profile lookup order: line.profile -> cast[who].profile -> who -> "narrator"
            prof_name = (
                ln.get("profile")
                or (cast.get(who, {}).get("profile") if isinstance(cast.get(who), dict) else None)
                or (who if (who in PROFILES or who in custom_voices) else "narrator")
            )
            prof = resolve_profile(
                prof_name,
                custom_profiles=custom_voices,
                voice=ln.get("voice"),
                rate=ln.get("rate"),
                pitch=ln.get("pitch"),
                af=ln.get("af"),
            )

            out_mp3 = vo_abs / f"{lid}.mp3"
            rel_file = f"{vo_subdir.rstrip('/')}/{lid}.mp3"
            key = cache_key(spoken, prof, lufs)

            if not args.force and out_mp3.exists() and cache.get(lid) == key:
                status = "CACHE"
            else:
                synthesize_line(
                    spoken,
                    out_mp3,
                    prof,
                    edge_cmd=edge_cmd,
                    fmt="mp3",
                    lufs=lufs,
                )
                cache[lid] = key
                status = "GEN  "

            dur_s, env = extract_envelope(out_mp3, fps=fps)
            dur_f = max(1, math.ceil(dur_s * fps))
            print(f"  [{status}] {lid:<16} ({who} -> {prof_name}) {dur_s:.2f}s ({dur_f} fr)", flush=True)

            if "cue" in ln:
                cues[ln["cue"]] = cur - sc_start

            line_entry: dict[str, Any] = {
                "id": lid,
                "scene": sid,
                "who": who,
                "text": display_text,
                "from": cur,
                "dur": dur_f,
                "file": rel_file,
                "env": env,
            }
            timeline_lines.append(line_entry)

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
        description="Free Lao Neural TTS (Microsoft Edge TTS) + FFmpeg character voice shaping + lip-sync.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_prof = sub.add_parser("profiles", help="List built-in Lao character voice profiles")
    p_prof.add_argument("--json", action="store_true", help="Output as JSON")
    p_prof.set_defaults(func=cmd_profiles)

    p_spk = sub.add_parser("speak", help="Generate a single Lao audio clip (mp3/ogg/wav)")
    p_spk.add_argument("--text", "-t", help="Lao text to speak")
    p_spk.add_argument("--text-file", help="Read Lao text from a UTF-8 file")
    p_spk.add_argument("--out", "-o", required=True, help="Output file path (.mp3, .ogg, or .wav)")
    p_spk.add_argument("--profile", "-p", default="narrator", help="Voice profile name (default: narrator)")
    p_spk.add_argument("--voice", help="Override Edge TTS voice (e.g. lo-LA-KeomanyNeural)")
    p_spk.add_argument("--rate", help="Override speed (e.g. +5%%, -10%%)")
    p_spk.add_argument("--pitch", help="Override pitch (e.g. +8Hz, -6Hz)")
    p_spk.add_argument("--af", help="Override FFmpeg audio filter chain")
    p_spk.add_argument("--format", "-f", choices=["mp3", "ogg", "wav"], help="Force output format")
    p_spk.add_argument("--lufs", type=float, default=-16.0, help="Target loudness LUFS (default: -16)")
    p_spk.add_argument("--fps", type=int, default=30, help="Envelope FPS (default: 30)")
    p_spk.add_argument("--envelope", help="Optional JSON path to write 30fps RMS lip-sync envelope")
    p_spk.add_argument("--stereo", action="store_true", help="Output stereo instead of mono (mp3/wav)")
    p_spk.add_argument("--raw", action="store_true", help="Skip FFmpeg timbre shaping")
    p_spk.add_argument("--no-clean", action="store_true", help="Send text verbatim to Edge TTS without cleaning")
    p_spk.add_argument("--json", action="store_true", help="Output result summary as JSON")
    p_spk.set_defaults(func=cmd_speak)

    p_bld = sub.add_parser("build", help="Batch-build voiced motion-muse episode from script.json")
    p_bld.add_argument("project", help="Remotion project directory (contains public/)")
    p_bld.add_argument("script", help="Path to script.json")
    p_bld.add_argument("--vo-dir", help="Relative dir under public/ for VO MP3s (default: audio/vo)")
    p_bld.add_argument("--lufs", type=float, default=-16.0, help="Target loudness LUFS (default: -16)")
    p_bld.add_argument("--no-subs", action="store_true", help="Set props.subs=false in storyboard.json")
    p_bld.add_argument("--force", action="store_true", help="Regenerate all lines even if cached")
    p_bld.set_defaults(func=cmd_build)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

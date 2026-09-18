import math
from pathlib import Path
import numpy as np
import soundfile as sf

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music_library"
SFX_DIR = ASSETS_DIR / "sfx_library"
TEMP_DIR = ASSETS_DIR / "temp"
OUTPUTS_DIR = ASSETS_DIR / "outputs"


def generate_dramatic_cinematic_music(
    output_path: Path, duration_sec: int = 75, sample_rate: int = 44100
):
    """
    Generates a suspenseful, dramatic cinematic background music track:
    - Rhythmic suspense heartbeat sub-bass pulse (dramatic 'lub-dub' tempo).
    - Cinematic minor tension pads (Cm, Ab, Fm) with evolving harmonic textures.
    - Soft metallic ticking / clock-like tension pulse.
    - Cinematic swells and dynamic atmospheric breathing.
    """
    total_samples = int(sample_rate * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)

    # 1. Rhythmic Heartbeat / Dramatic Sub-Bass Pulse (BPM = 72, beat every ~0.833s)
    beat_interval = 0.833
    heartbeat = np.zeros(total_samples)

    # Create two pulses per beat (lub-dub)
    for beat_start in np.arange(0, duration_sec - 1.0, beat_interval):
        idx1 = int(beat_start * sample_rate)
        # First pulse (lub)
        pulse1_len = int(0.18 * sample_rate)
        if idx1 + pulse1_len < total_samples:
            tp1 = np.linspace(0, 0.18, pulse1_len)
            p1 = np.sin(2 * np.pi * 55.0 * np.exp(-3.0 * tp1) * tp1) * np.exp(-12.0 * tp1)
            heartbeat[idx1 : idx1 + pulse1_len] += p1 * 0.7

        # Second pulse (dub) ~0.24s later
        idx2 = int((beat_start + 0.24) * sample_rate)
        pulse2_len = int(0.22 * sample_rate)
        if idx2 + pulse2_len < total_samples:
            tp2 = np.linspace(0, 0.22, pulse2_len)
            p2 = np.sin(2 * np.pi * 48.0 * np.exp(-2.5 * tp2) * tp2) * np.exp(-10.0 * tp2)
            heartbeat[idx2 : idx2 + pulse2_len] += p2 * 0.55

    # 2. Cinematic Tension Pads (Minor key: C minor chord C3, Eb3, G3, Bb3)
    c3 = 130.81
    eb3 = 155.56
    g3 = 196.00
    ab3 = 207.65

    # Slow breathing LFO
    lfo_swell = 0.5 + 0.5 * np.sin(2 * np.pi * 0.12 * t)
    lfo_dark = 0.6 + 0.4 * np.cos(2 * np.pi * 0.08 * t)

    pad1 = np.sin(2 * np.pi * c3 * t) * 0.22
    pad2 = np.sin(2 * np.pi * eb3 * t) * 0.18
    pad3 = np.sin(2 * np.pi * g3 * t) * 0.16
    pad4 = np.sin(2 * np.pi * ab3 * t) * 0.14 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t))
    drone_bass = np.sin(2 * np.pi * (c3 / 2.0) * t) * 0.35

    pads = (pad1 + pad2 + pad3 + pad4 + drone_bass) * lfo_swell * lfo_dark

    # 3. Soft Clock-Like Tension Tick (every 0.416s, eighth notes)
    tick = np.zeros(total_samples)
    for tick_time in np.arange(0, duration_sec - 0.1, 0.416):
        t_idx = int(tick_time * sample_rate)
        t_len = int(0.02 * sample_rate)
        if t_idx + t_len < total_samples:
            tt = np.linspace(0, 0.02, t_len)
            tick[t_idx : t_idx + t_len] += np.sin(2 * np.pi * 1800.0 * tt) * np.exp(-150.0 * tt) * 0.08

    # 4. Mix Components
    music_mix = heartbeat * 0.45 + pads * 0.45 + tick * 0.15

    # Apply fade in & fade out
    fade_len = int(sample_rate * 2.5)
    fade_in = np.linspace(0, 1, fade_len)
    fade_out = np.linspace(1, 0, fade_len)
    music_mix[:fade_len] *= fade_in
    music_mix[-fade_len:] *= fade_out

    # Normalize to -2dB
    max_val = np.max(np.abs(music_mix))
    if max_val > 0:
        music_mix = (music_mix / max_val) * 0.75

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), music_mix.astype(np.float32), sample_rate)
    print(f"Generated Dramatic Cinematic Suspense BGM: {output_path}")


def generate_whoosh_sfx(output_path: Path, sample_rate: int = 44100):
    """Generates a dynamic whoosh sound effect."""
    duration = 0.6
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    noise = np.random.uniform(-1.0, 1.0, len(t))
    envelope = np.sin(np.pi * (t / duration)) ** 2
    mod = np.sin(2 * np.pi * (100 + 800 * (t / duration)) * t)
    audio = noise * envelope * 0.6 + mod * envelope * 0.4
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio.astype(np.float32), sample_rate)
    print(f"Generated Whoosh SFX: {output_path}")


def generate_dramatic_boom_sfx(output_path: Path, sample_rate: int = 44100):
    """Generates a deep cinematic bass boom / dramatic hit."""
    duration = 1.8
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    freq = 90.0 * np.exp(-3.5 * t)
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    audio = np.sin(phase) * np.exp(-2.2 * t)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio.astype(np.float32), sample_rate)
    print(f"Generated Dramatic Boom SFX: {output_path}")


def main():
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    bgm_path = MUSIC_DIR / "cinematic_suspense.wav"
    generate_dramatic_cinematic_music(bgm_path, duration_sec=90)

    whoosh_path = SFX_DIR / "whoosh.wav"
    generate_whoosh_sfx(whoosh_path)

    boom_path = SFX_DIR / "dramatic_boom.wav"
    generate_dramatic_boom_sfx(boom_path)


if __name__ == "__main__":
    main()

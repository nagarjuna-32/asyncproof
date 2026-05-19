import os
import subprocess
from pathlib import Path


def record_with_ffmpeg(output_dir: str, output_filename: str, duration_seconds: int = 60) -> Path:
    """Consent-based visible recording.

    Notes:
    - This uses ffmpeg's screen capture which depends on OS + installed codecs.
    - Bot must be visible; ensure the user/host consent in your UI/session flow.
    - duration_seconds is a safety limit so recording ends.
    """

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / output_filename

    # Basic ffmpeg checks
    subprocess.run(["ffmpeg", "-version"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Windows screen capture often needs -f gdigrab. We'll use a cross-platform
    # fallback: gdigrab (Windows) and x11 (Linux). If it fails, user can adjust.
    cmd = [
        "ffmpeg",
        "-y",
        "-t",
        str(int(duration_seconds)),
    ]

    if os.name == "nt":
        # Capture primary screen and microphone is OS-dependent; we capture desktop only.
        # If microphone capture isn't configured, transcription may be weak.
        cmd += [
            "-f",
            "gdigrab",
            "-framerate",
            "15",
            "-i",
            "desktop",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
        ]
    else:
        cmd += [
            "-f",
            "x11grab",
            "-framerate",
            "15",
            "-i",
            ":0.0",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
        ]

    # Audio: attempt default system audio capture. Many environments require extra configuration.
    cmd += ["-c:a", "aac", "-b:a", "128k", str(out_path)]

    proc = subprocess.run(cmd, check=False)

    if not out_path.exists():
        raise RuntimeError(f"FFmpeg did not create output file: {out_path}")

    size = out_path.stat().st_size
    if size <= 0:
        raise RuntimeError(f"FFmpeg created empty file: {out_path} ({size} bytes)")

    return out_path


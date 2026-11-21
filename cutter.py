import subprocess
from pathlib import Path
from functools import reduce
from settings import CONFIG, ROOT

BACKUP: Path = ROOT / CONFIG["paths"]["backup_dir"]
FFMPEG: str = CONFIG["ffmpeg"]["ffmpeg_bin"]
FFPROBE: str = CONFIG["ffmpeg"]["ffprobe_bin"]
AVOID_TS: str = CONFIG["ffmpeg"]["avoid_negative_ts"]
MAP: str = CONFIG["ffmpeg"]["map"]
LOG_LINES: int = CONFIG["ffmpeg"]["log_lines"]
LOG_ENCODING: str = CONFIG["ffmpeg"]["log_encoding"]
MIN_KEEP: float = CONFIG["cut"]["min_keep_sec"]


def probe_args(video: str, entries: str) -> list[str]:
    return [FFPROBE, "-v", "error", "-show_entries", entries, "-of", "csv=p=0", video]


def has_audio(video: str) -> bool:
    out = subprocess.run(probe_args(video, "stream=codec_type"), capture_output=True, text=True).stdout
    return "audio" in out.split()


def duration(video: str) -> float:
    return float(subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", video],
        capture_output=True, text=True).stdout)


def merge(cuts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return reduce(
        lambda acc, c: acc[:-1] + [(acc[-1][0], max(acc[-1][1], c[1]))]
        if acc and c[0] <= acc[-1][1] else acc + [c],
        sorted(cuts), [])


def keep(total: float, cuts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    bounds: list[float] = [0.0] + [x for c in merge(cuts) for x in c] + [total]
    return [(s, e) for s, e in zip(bounds[::2], bounds[1::2]) if e - s >= MIN_KEEP]


def run_logged(args: list[str], emit) -> None:
    emit("$ " + " ".join(args))
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            encoding=LOG_ENCODING, errors="replace")
    tail: list[str] = []
    for line in proc.stdout:
        text = line.rstrip()
        if text:
            tail.append(text)
            tail = tail[-LOG_LINES:]
    for text in tail:
        emit(text)
    proc.wait()


def export(video: str, out: Path, segments: list[tuple[float, float]], emit=lambda _: None) -> bool:
    BACKUP.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    for i, (s, e) in enumerate(segments):
        part: Path = BACKUP / f"part{i:03d}.mp4"
        run_logged(
            [FFMPEG, "-y", "-ss", f"{s:.3f}", "-i", video,
             "-t", f"{e - s:.3f}", "-c", "copy", "-map", MAP,
             "-avoid_negative_ts", AVOID_TS, str(part)], emit)
        parts.append(part)
    listing: Path = BACKUP / "list.txt"
    listing.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf-8")
    run_logged(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0",
         "-i", str(listing), "-c", "copy", "-map", MAP, str(out)], emit)
    return has_audio(video) == has_audio(str(out))

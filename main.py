import sys
import subprocess
import os
from urllib.parse import urlparse, parse_qs


# ----------------
# Bootstrap
# ----------------

def _ensure(package: str, import_as: str | None = None) -> None:
    # Install package if not already available
    name = import_as or package
    try:
        __import__(name)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])


_ensure("yt-dlp", "yt_dlp")
_ensure("imageio-ffmpeg", "imageio_ffmpeg")
_ensure("rich")
_ensure("questionary")

import yt_dlp
import imageio_ffmpeg
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TaskID,
)
from rich import box
from rich.text import Text
from rich.prompt import Prompt, IntPrompt
import questionary


# ----------------
# Config
# ----------------

DOWNLOAD_DIR: str = r"D:\Malik\Videos\Youtube Videos"
FFMPEG_PATH: str = imageio_ffmpeg.get_ffmpeg_exe()
console = Console()


# ----------------
# URL helpers
# ----------------

def clean_url(raw_url: str) -> str:
    # Normalize any YouTube URL to the canonical watch?v= form
    parsed = urlparse(raw_url.strip())

    if parsed.netloc in ("youtu.be", "www.youtu.be"):
        video_id = parsed.path.lstrip("/").split("/")[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

    if "youtube.com" in parsed.netloc:
        params = parse_qs(parsed.query)
        video_id = params.get("v", [None])[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

    return raw_url.strip()


# ----------------
# Video info
# ----------------

def fetch_qualities(url: str) -> tuple[list[tuple[str, str]], str]:
    # Return available (label, format_id) pairs and the video title
    ydl_opts = {"quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    best_by_height: dict[int, dict] = {}
    for fmt in info.get("formats", []):
        height = fmt.get("height")
        vcodec = fmt.get("vcodec", "none")
        tbr = fmt.get("tbr") or 0
        if not height or vcodec == "none":
            continue
        existing_tbr = (best_by_height[height].get("tbr") or 0) if height in best_by_height else -1
        if tbr > existing_tbr:
            best_by_height[height] = fmt

    qualities = sorted(best_by_height.items(), key=lambda x: x[0], reverse=True)
    return [(f"{h}p", fmt["format_id"]) for h, fmt in qualities], info["title"]


# ----------------
# Download
# ----------------

def _make_progress() -> Progress:
    # Build a rich progress bar with speed and ETA columns
    return Progress(
        "[progress.description]{task.description}",
        BarColumn(bar_width=40),
        "[progress.percentage]{task.percentage:>5.1f}%",
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )


def download_video(url: str, format_id: str, resolution: str) -> str:
    # Download video + best audio and merge to mp4
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    progress = _make_progress()
    task_id: TaskID | None = None

    def yt_dlp_hook(d: dict) -> None:
        nonlocal task_id
        status = d.get("status")

        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            filename = os.path.basename(d.get("filename", ""))

            if task_id is None:
                task_id = progress.add_task(
                    f"[cyan]{filename[:50]}",
                    total=total or None,
                )
            else:
                progress.update(task_id, completed=downloaded, total=total or None)

        elif status == "finished" and task_id is not None:
            progress.update(task_id, completed=progress.tasks[task_id].total or 0)

    ydl_opts = {
        "format": f"{format_id}+bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "ffmpeg_location": FFMPEG_PATH,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [yt_dlp_hook],
    }

    console.print()
    with progress:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

    base, _ = os.path.splitext(filename)
    return base + ".mp4"


def download_audio(url: str, bitrate: str) -> str:
    # Download audio and convert to mp3 at the chosen bitrate
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    progress = _make_progress()
    task_id: TaskID | None = None
    bitrate_value = bitrate.replace("kbps", "")

    def yt_dlp_hook(d: dict) -> None:
        nonlocal task_id
        status = d.get("status")

        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            filename = os.path.basename(d.get("filename", ""))

            if task_id is None:
                task_id = progress.add_task(
                    f"[cyan]{filename[:50]}",
                    total=total or None,
                )
            else:
                progress.update(task_id, completed=downloaded, total=total or None)

        elif status == "finished" and task_id is not None:
            progress.update(task_id, completed=progress.tasks[task_id].total or 0)

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": bitrate_value,
        }],
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        "ffmpeg_location": FFMPEG_PATH,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [yt_dlp_hook],
    }

    console.print()
    with progress:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

    base, _ = os.path.splitext(filename)
    return base + ".mp3"


# ----------------
# UI helpers
# ----------------

def print_banner() -> None:
    # Show the app title panel
    banner = Text("▶  YouTube Video Downloader", style="bold red")
    console.print(Panel(banner, box=box.DOUBLE, border_style="red", padding=(0, 4)))
    console.print()


def print_qualities_table(qualities: list[tuple[str, str]], title: str) -> None:
    # Render available resolutions in a numbered table
    table = Table(
        title=f"[bold white]{title}[/]",
        box=box.ROUNDED,
        border_style="bright_black",
        header_style="bold cyan",
        show_lines=False,
        padding=(0, 2),
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Resolution", style="bold green")

    for i, (resolution, _) in enumerate(qualities, 1):
        table.add_row(str(i), resolution)

    console.print(table)
    console.print()


def prompt_quality_choice(count: int) -> int:
    # Prompt user to pick a quality by number
    while True:
        choice = IntPrompt.ask(f"[bold yellow]Select quality[/] [dim](1-{count})[/]")
        if 1 <= choice <= count:
            return choice
        console.print(f"[red]Please enter a number between 1 and {count}.[/]")


# ----------------
# Entry point
# ----------------

def main() -> None:
    print_banner()

    raw_url = Prompt.ask("[bold yellow]Enter YouTube URL[/]").strip()
    if not raw_url:
        console.print("[red]Error:[/] No URL provided.")
        sys.exit(1)

    url = clean_url(raw_url)
    if url != raw_url:
        console.print(f"[dim]Cleaned URL:[/] [cyan]{url}[/]")

    console.print()
    media_format = questionary.select(
        "Choose format:",
        choices=["Video (MP4)", "Audio (MP3)"],
    ).ask()

    if media_format == "Video (MP4)":
        console.print("\n[dim]Fetching available qualities...[/]")

        try:
            qualities, title = fetch_qualities(url)
        except Exception as exc:
            console.print(f"[red]Error fetching video info:[/] {exc}")
            sys.exit(1)

        if not qualities:
            console.print("[red]No downloadable video qualities found.[/]")
            sys.exit(1)

        console.print()
        selected_res = questionary.select(
            "Select quality:",
            choices=[res for res, _ in qualities],
        ).ask()

        selected_fmt_id = next(fid for res, fid in qualities if res == selected_res)

        console.print(f"\n[bold green]Downloading[/] [cyan]{selected_res}[/]...")

        try:
            filepath = download_video(url, selected_fmt_id, selected_res)
        except Exception as exc:
            console.print(f"\n[red]Download failed:[/] {exc}")
            sys.exit(1)

    else:
        console.print()
        selected_bitrate = questionary.select(
            "Select audio quality:",
            choices=["320kbps", "192kbps", "128kbps"],
        ).ask()

        console.print(f"\n[bold green]Downloading[/] [cyan]{selected_bitrate} MP3[/]...")

        try:
            filepath = download_audio(url, selected_bitrate)
        except Exception as exc:
            console.print(f"\n[red]Download failed:[/] {exc}")
            sys.exit(1)

    console.print(
        Panel(
            f"[bold green]Download complete![/]\n[dim]Saved to:[/] [cyan]{filepath}[/]",
            box=box.ROUNDED,
            border_style="green",
            padding=(0, 2),
        )
    )


if __name__ == "__main__":
    main()

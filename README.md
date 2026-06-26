# YouTube Video Downloader

A command-line tool that downloads YouTube videos or audio with an interactive terminal UI. Paste a URL, pick a format and quality using arrow keys, and watch a live progress bar as the file saves.

---

## What It Does

1. Accepts any YouTube URL (standard `youtube.com/watch?v=` or short `youtu.be/` links)
2. Normalizes the URL to a clean canonical form
3. Asks whether you want Video (MP4) or Audio (MP3) — select with arrow keys
4. For MP4: fetches real available resolutions and lets you pick with arrow keys
5. For MP3: lets you choose audio quality (320kbps, 192kbps, 128kbps) with arrow keys
6. Downloads and saves to `D:\Malik\Videos\Youtube Videos` — no path prompt
7. For MP4: merges video + best available audio into a single `.mp4` using ffmpeg
8. For MP3: extracts and converts audio to `.mp3` at the chosen bitrate using ffmpeg
9. Shows a live progress bar with file size, transfer speed, and estimated time remaining
10. Prints a confirmation panel with the saved file path when done

---

## Features

| Feature                  | Description                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------------- |
| Format selection         | Choose between Video (MP4) or Audio (MP3) using arrow keys                                  |
| Arrow-key quality picker | Navigate quality options with ↑↓ keys — no typing required                                  |
| MP4 quality              | Real resolutions fetched from the video (e.g. 1080p, 720p, 480p, 360p)                      |
| MP3 quality              | Fixed bitrate options: 320kbps, 192kbps, 128kbps                                            |
| Fixed save path          | All files save to `D:\Malik\Videos\Youtube Videos` automatically                            |
| URL normalization        | Converts `youtu.be` and any `youtube.com` variant to a clean `watch?v=` URL                 |
| Format deduplication     | Keeps only the highest-bitrate stream per resolution                                        |
| Audio + video merge      | Downloads video and audio separately, merges into one MP4 via ffmpeg                        |
| Live progress bar        | Shows downloaded bytes, transfer speed, and ETA during download                             |
| Self-bootstrapping       | Installs missing packages (`yt-dlp`, `imageio-ffmpeg`, `rich`, `questionary`) automatically |
| Standalone executable    | Buildable with PyInstaller into a single `.exe` for Windows                                 |

---

## Technologies Used

| Library          | Role                                                                        |
| ---------------- | --------------------------------------------------------------------------- |
| `yt-dlp`         | Extracts video metadata and handles the download with progress hook support |
| `imageio-ffmpeg` | Ships a self-contained ffmpeg binary — no system ffmpeg required            |
| `rich`           | Terminal UI: panels, progress bar, styled prompts                           |
| `questionary`    | Arrow-key selection menus for format and quality choices                    |
| `PyInstaller`    | Packages the script into a standalone Windows executable                    |
| `urllib.parse`   | Parses and normalizes YouTube URLs                                          |

---

## Requirements

```
pip install questionary
```

All other dependencies (`yt-dlp`, `imageio-ffmpeg`, `rich`) are installed automatically on first run.

---

## How the Code Works

**Bootstrap (`_ensure`)** — Checks if each required package is importable and runs `pip install` for any that are missing. The script works on a bare Python installation.

**URL cleaning (`clean_url`)** — Parses the raw input URL. Handles both `youtu.be` short links and `youtube.com` URLs, extracting the video ID and returning a clean `watch?v=` URL.

**Format fetching (`fetch_qualities`)** — Calls yt-dlp in metadata-only mode to get all available formats. Keeps only the highest-bitrate stream per unique height, returning a sorted list of `(label, format_id)` pairs.

**Video download (`download_video`)** — Passes yt-dlp the format string `<format_id>+bestaudio/best` to fetch video and audio streams separately, then merges them into MP4. A progress hook updates the rich progress bar on every chunk.

**Audio download (`download_audio`)** — Downloads the best available audio stream and runs it through the FFmpegExtractAudio postprocessor at the chosen bitrate, saving as MP3.

**UI layer** — `questionary.select` handles all arrow-key menus. `rich` provides the banner panel, progress bar, and completion notice.

---

## Author

**Malik-712**
GitHub: [https://github.com/Malik-712](https://github.com/Malik-712)

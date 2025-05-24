# YouTubeDownloader

A cross-platform YouTube downloader with multi-language GUI, supporting playlist/video, quality selection, and FFmpeg auto-installation.

## Features
- Download YouTube videos and playlists.
- Quality and format selection (mp4, webm, mp3).
- Multi-language support (English/中文, easily extendable).
- Automatic FFmpeg download for Windows/Mac/Linux.
- Error logs saved to `logs/`.

## Quick Start

1. **Install dependencies**

``pip install -r requirements.txt``

2. **Download FFmpeg (auto)**
- When you run the main program, it will check `assets/` for FFmpeg.
- If not found, it will run `download_ffmpeg.py` automatically.

3. **Run the downloader**

``python main.py``

## Manual FFmpeg Installation
If auto download fails, please:
- Visit [FFmpeg official site](https://ffmpeg.org/download.html)
- Download the release for your platform, and put the `ffmpeg` (or `ffmpeg.exe`) in the `assets/` folder.

## How to Add Language?
- Add a new `xx.json` file in `langs/`, using the same key structure as `en.json`.

## Development
- No binary files are included in the repo.
- If you want to package, use pyinstaller or similar tools.

## License
- This project uses [pytubefix](https://github.com/nficano/pytube) and [FFmpeg](https://ffmpeg.org/) under their respective licenses.

---

**如要更多語言教學或遇到 ffmpeg 自動下載 bug，歡迎新增 issue !**
**For more language tutorials or if you encounter FFmpeg auto-download bugs, feel free to open an issue!**

# core/ffmpeg_helper.py

import os
import sys
import urllib.request
import zipfile
import platform
import tempfile
import shutil
import traceback

FFMPEG_URLS = {
    "Windows": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "Darwin": "https://evermeet.cx/ffmpeg/ffmpeg.zip",  # macOS
    "Linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
}

def download_and_extract_ffmpeg(target_dir: str) -> str:
    """
    從官方來源下載 FFMPEG 並解壓縮至指定資料夾。
    返回 ffmpeg 執行檔的完整路徑。
    """
    system = platform.system()
    url = FFMPEG_URLS.get(system)
    if not url:
        raise Exception(f"FFmpeg automatic download is not supported on {system}")

    print(f"Downloading FFmpeg from {url}")
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.basename(url))

    try:
        urllib.request.urlretrieve(url, tmp_file.name)

        if url.endswith(".zip"):
            with zipfile.ZipFile(tmp_file.name, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
        elif url.endswith(".tar.xz"):
            shutil.unpack_archive(tmp_file.name, target_dir)
        else:
            raise Exception("Unsupported archive format.")

        # 嘗試尋找 ffmpeg 可執行檔
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.lower() == "ffmpeg.exe" or file == "ffmpeg":
                    ffmpeg_path = os.path.join(root, file)
                    final_path = os.path.join(target_dir, os.path.basename(ffmpeg_path))
                    shutil.copy2(ffmpeg_path, final_path)
                    print(f"FFmpeg extracted to: {final_path}")
                    return final_path

        raise FileNotFoundError("FFmpeg executable not found in the archive.")

    except Exception as e:
        print("Failed to download or extract FFmpeg:", e)
        traceback.print_exc()
        raise

    finally:
        os.unlink(tmp_file.name)

def ensure_ffmpeg(user_data_dir: str) -> str:
    """
    確保 FFmpeg 可用，若不可用則自動下載。
    返回 FFmpeg 執行檔的路徑。
    """
    exe_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    ffmpeg_path = os.path.join(user_data_dir, exe_name)

    if not os.path.exists(ffmpeg_path):
        print("FFmpeg not found, attempting to download...")
        return download_and_extract_ffmpeg(user_data_dir)
    return ffmpeg_path
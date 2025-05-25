import os
import sys
import platform
import zipfile
import tarfile
import requests
import shutil

def download_file(url, dest):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def main(download_dir=None):
    if download_dir is None:
        # 如果沒指定，預設還是 assets（但建議 always 傳入 user_data_dir）
        download_dir = os.path.join(os.path.dirname(__file__), "assets")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    system = platform.system()
    ffmpeg_exe = os.path.join(download_dir, "ffmpeg.exe" if system == "Windows" else "ffmpeg")
    if os.path.exists(ffmpeg_exe):
        print("ffmpeg 已存在！")
        return

    print(f"正在為 {system} 下載 ffmpeg ...")
    if system == "Windows":
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        zip_path = os.path.join(download_dir, "ffmpeg_win.zip")
        download_file(url, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(download_dir)
        for root, dirs, files in os.walk(download_dir):
            if "ffmpeg.exe" in files:
                shutil.copy2(os.path.join(root, "ffmpeg.exe"), ffmpeg_exe)
                break
        os.remove(zip_path)
    elif system == "Darwin":
        url = "https://evermeet.cx/ffmpeg/ffmpeg-6.1.1.zip"
        zip_path = os.path.join(download_dir, "ffmpeg_mac.zip")
        download_file(url, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(download_dir)
        shutil.move(os.path.join(download_dir, "ffmpeg"), ffmpeg_exe)
        os.remove(zip_path)
        os.chmod(ffmpeg_exe, 0o755)
    elif system == "Linux":
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        tar_path = os.path.join(download_dir, "ffmpeg_linux.tar.xz")
        download_file(url, tar_path)
        with tarfile.open(tar_path, "r:xz") as tar:
            for member in tar.getmembers():
                if member.isfile() and member.name.endswith("/ffmpeg"):
                    member.name = os.path.basename(member.name)
                    tar.extract(member, download_dir)
                    shutil.move(os.path.join(download_dir, "ffmpeg"), ffmpeg_exe)
                    os.chmod(ffmpeg_exe, 0o755)
                    break
        os.remove(tar_path)
    else:
        print("不支援的平台，請自行安裝 ffmpeg。")
        sys.exit(1)
    print("ffmpeg 已下載並放到 user_data_dir 目錄！")

if __name__ == "__main__":
    main()
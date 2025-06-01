import os
import time

def log_error(message, log_dir="logs", log_name="YouTubeDownloader_errors.log"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_name)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
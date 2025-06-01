import os
import sys
import appdirs
import tkinter as tk

from app.constants import APP_NAME, APP_AUTHOR
from app.language import load_lang_texts
from core.ffmpeg_helper import ensure_ffmpeg
from app.gui import YouTubeDownloaderApp

base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
user_data_dir = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
if not os.path.exists(user_data_dir):
    os.makedirs(user_data_dir)

DEFAULT_LANG = 'zh'
LANG_TEXTS = load_lang_texts(base_path)

def main():
    ffmpeg_path = ensure_ffmpeg(user_data_dir)
    if not ffmpeg_path:
        import tkinter.messagebox as messagebox
        tk.Tk().withdraw()
        messagebox.showerror("FFmpeg Error", "自動下載 FFmpeg 失敗，請手動安裝到 assets 目錄。")
        sys.exit(1)
    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("600x650")
    app = YouTubeDownloaderApp(root, ffmpeg_path, LANG_TEXTS, DEFAULT_LANG, APP_NAME)
    root.mainloop()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        from core.logger import log_error
        log_error(f"Fatal error: {str(e)}\n{traceback.format_exc()}")
        tk.Tk().withdraw()
        import tkinter.messagebox as messagebox
        messagebox.showerror("Fatal Error", str(e))
        sys.exit(1)
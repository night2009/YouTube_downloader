import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pytubefix import YouTube, Playlist
from PIL import Image, ImageTk
import threading
import os
import requests
from io import BytesIO
import subprocess
import re
import sys
import time
import traceback
import json

APP_NAME = "YouTubeDownloader"

def ensure_ffmpeg():
    # 支援不同平台自動找 ffmpeg 執行檔
    exe_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    ffmpeg_path = os.path.join(base_path, "assets", exe_name)
    if not os.path.exists(ffmpeg_path):
        try:
            subprocess.check_call([sys.executable, os.path.join(base_path, "download_ffmpeg.py")])
        except Exception as e:
            messagebox.showerror("FFmpeg Missing", "下載 FFmpeg 失敗，請依 README.md 說明手動安裝。")
            sys.exit(1)
    return ffmpeg_path

FFMPEG_PATH = ensure_ffmpeg()


base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
LOGS_DIR = os.path.join(base_path, "logs")

# Create logs directory if it doesn't exist
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

ERROR_LOG_PATH = os.path.join(LOGS_DIR, "YouTubeDownloader_errors.log")

DEFAULT_LANG = 'en'

# 語言檔動態載入
# Dynamically load language files
def load_lang_texts(lang_folder='langs'):
    lang_texts = {}
    for fname in os.listdir(lang_folder):
        if fname.endswith('.json'):
            lang_code = fname.split('.')[0]
            with open(os.path.join(lang_folder, fname), 'r', encoding='utf-8') as f:
                lang_texts[lang_code] = json.load(f)
    return lang_texts

LANG_TEXTS = load_lang_texts()

def sanitize_filename(name):
    return re.sub(r'[\\/*?"<>|]', "", name)

def log_error(message):
    with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

# ...existing code...

class YouTubeDownloaderApp:
    ''' 
    A simple YouTube downloader application using Tkinter and pytubefix.
    This application allows users to download videos or playlists from YouTube,
    select the format and resolution, and save them to a specified folder.
    This application supports multiple languages and provides a user-friendly interface.
    '''
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("560x580")
        try:
            icon_path = os.path.join(base_path, "assets", "YouTubeDownloader.ico")
            self.root.iconbitmap(default=icon_path)
        except Exception as e:
            print(f"Icon load failed: {e}")

        self.lang = tk.StringVar(value='zh')
        self.lang.trace_add("write", lambda *args: self.update_language())
        self.save_path = tk.StringVar()
        self.url = tk.StringVar()
        self.format_var = tk.StringVar(value='mp4')
        self.res_var = tk.StringVar()
        self.thumbnail_photo = None

        self.create_widgets()
        self.update_language()  # 初始UI語言 # Initialize UI language

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)
        frm.columnconfigure(0, weight=1)
        frm.columnconfigure(1, weight=0)

        # URL 輸入        
        # URL input
        self.label_url = ttk.Label(frm)
        self.label_url.grid(row=0, column=0, sticky='w')
        url_entry = ttk.Entry(frm, textvariable=self.url, width=50)
        url_entry.grid(row=1, column=0, columnspan=2, sticky='we')
        frm.rowconfigure(1, weight=0)

        # 資料夾選擇
        # Folder selection
        self.label_folder = ttk.Label(frm)
        self.label_folder.grid(row=2, column=0, sticky='w')
        path_entry = ttk.Entry(frm, textvariable=self.save_path, width=50)
        path_entry.grid(row=3, column=0, sticky='we')
        self.btn_browse = ttk.Button(frm, command=self.browse_folder)
        self.btn_browse.grid(row=3, column=1, sticky='e')
        frm.rowconfigure(3, weight=0)

        # 影片資訊與操作
        # Video info and actions
        self.btn_load = ttk.Button(frm, command=self.load_playlist_or_video)
        self.btn_load.grid(row=4, column=0, columnspan=2, pady=5, sticky='we')

        # 格式下拉選單
        # Format dropdown
        ttk.Label(frm, text=self.lang_text('format')).grid(row=5, column=0, sticky='w')
        self.format_combo = ttk.Combobox(frm, textvariable=self.format_var, values=['mp4', 'webm', 'mp3'], state='readonly')
        self.format_combo.grid(row=5, column=1, sticky='we')

        # 解析度下拉選單
        # Resolution dropdown
        ttk.Label(frm, text=self.lang_text('resolution')).grid(row=6, column=0, sticky='w')
        self.res_combo = ttk.Combobox(frm, textvariable=self.res_var, values=[], state='readonly')
        self.res_combo.grid(row=6, column=1, sticky='we')
        self.format_combo.bind('<<ComboboxSelected>>', lambda e: self.populate_resolutions(self.url.get()))

        # 下載按鈕
        # Download button
        self.download_btn = ttk.Button(frm, command=self.download_by_url)
        self.download_btn.grid(row=7, column=0, columnspan=2, pady=5, sticky='we')

        # 狀態提示
        # Status message
        self.label_info = ttk.Label(frm, text="", foreground="gray")
        self.label_info.grid(row=8, column=0, columnspan=2, sticky='we')

        # 進度條
        # Progress bar
        self.progress = ttk.Progressbar(frm, orient='horizontal', length=400, mode='determinate')
        self.progress.grid(row=9, column=0, columnspan=2, pady=5, sticky='we')

        # 語言切換
        # Language switch
        self.label_lang = ttk.Label(frm)
        self.label_lang.grid(row=10, column=0, sticky='w')
        self.lang_combo = ttk.Combobox(frm, textvariable=self.lang, values=list(LANG_TEXTS.keys()), state='readonly')
        self.lang_combo.grid(row=10, column=1, sticky='e')

        # 預覽縮圖區
        # Thumbnail preview area
        self.thumbnail_label = ttk.Label(frm)
        self.thumbnail_label.grid(row=11, column=0, columnspan=2, pady=12)
        frm.rowconfigure(11, weight=1)

        for i in range(12):
            frm.rowconfigure(i, weight=1 if i in [1, 3, 9, 11] else 0)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def update_language(self):
        self.label_url.config(text=self.lang_text('enter_url'))
        self.label_folder.config(text=self.lang_text('select_folder'))
        self.btn_browse.config(text=self.lang_text('browse'))
        self.btn_load.config(text=self.lang_text('load_video'))
        self.download_btn.config(text=self.lang_text('download_video'))
        self.label_lang.config(text=self.lang_text('language_label'))
        self.label_info.config(text="")

    def lang_text(self, key):
        lang = self.lang.get()
        if key in LANG_TEXTS.get(lang, {}):
            return LANG_TEXTS[lang][key]
        elif key in LANG_TEXTS.get(DEFAULT_LANG, {}):
            return LANG_TEXTS[DEFAULT_LANG][key]
        else:
            return key

    @staticmethod
    def find_missing_keys(target_lang='zh', default_lang='en'):
        missing = []
        for key in LANG_TEXTS.get(default_lang, {}):
            if key not in LANG_TEXTS.get(target_lang, {}):
                missing.append(key)
        return missing

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path.set(folder)

    def show_info(self, msg, title=None):
        if title is None:
            title = self.lang_text('video_info')
        messagebox.showinfo(title, msg)

    def show_warning(self, msg, title=None):
        if title is None:
            title = self.lang_text('error')
        messagebox.showwarning(title, msg)

    def show_error(self, e):
        log_error(f"{str(e)}\n{traceback.format_exc()}")
        messagebox.showerror(self.lang_text('error'), f"{str(e)}")

    def show_thumbnail(self, url):
        try:
            yt = YouTube(url)
            thumb_url = yt.thumbnail_url
            response = requests.get(thumb_url, timeout=10)
            img_data = Image.open(BytesIO(response.content)).resize((320, 180))
            self.thumbnail_photo = ImageTk.PhotoImage(img_data)
            self.thumbnail_label.config(image=self.thumbnail_photo, text='')
        except Exception as e:
            self.thumbnail_label.config(text=self.lang_text('thumbnail_loading_failed'), image='')
            self.thumbnail_photo = None
            log_error(str(e))

    def populate_resolutions(self, url):
        try:
            yt = YouTube(url)
            fmt = self.format_var.get()
            if fmt == 'mp3':
                self.res_combo['values'] = []
                self.res_var.set('')
                return
            resolutions = set()
            for s in yt.streams.filter(progressive=True, file_extension=fmt):
                if s.resolution:
                    resolutions.add(s.resolution)
            for s in yt.streams.filter(adaptive=True, only_video=True, file_extension=fmt):
                if s.resolution:
                    resolutions.add(s.resolution)
            res_list = sorted(resolutions, key=lambda x: int(x.replace('p', '')), reverse=True)
            self.res_combo['values'] = res_list
            if res_list:
                self.res_var.set(res_list[0])
            else:
                self.res_var.set('')
        except Exception as e:
            self.res_combo['values'] = []
            self.res_var.set('')
            log_error(str(e))

    def load_playlist_or_video(self):
        url = self.url.get().strip()
        if not url:
            return
        if "playlist?" in url or "&list=" in url:
            self.label_info.config(text=self.lang_text('playlist_mode_info'))
            self.show_info(self.lang_text('downloading_playlist'))
            threading.Thread(target=self.download_playlist, args=(url,)).start()
        else:
            self.label_info.config(text="")
            self.show_thumbnail(url)
            self.populate_resolutions(url)
            self.show_info(self.lang_text('load_complete'))

    def download_by_url(self):
        url = self.url.get().strip()
        if not url:
            return
        if "playlist?" in url or "&list=" in url:
            threading.Thread(target=self.download_playlist, args=(url,)).start()
        else:
            threading.Thread(target=self.download_single_video, args=(url,)).start()

    def download_single_video(self, url):
        folder = self.save_path.get()
        if not folder:
            self.show_warning(self.lang_text('select_folder_first'))
            return
        try:
            yt = YouTube(url)
            video_title = sanitize_filename(yt.title)
            fmt = self.format_var.get()
            selected_res = self.res_var.get()
            final_path = os.path.join(folder, f"{video_title}.{fmt if fmt != 'mp3' else 'mp3'}")

            if fmt == 'mp3':
                audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
                temp_audio = os.path.join(folder, f"{video_title}_audio.mp4")
                audio_stream.download(output_path=folder, filename=f"{video_title}_audio.mp4")
                subprocess.call([FFMPEG_PATH, '-i', temp_audio, '-vn', '-ab', '192k', '-ar', '44100', '-y', final_path])
                os.remove(temp_audio)
            else:
                stream = yt.streams.filter(progressive=True, file_extension=fmt, resolution=selected_res).first()
                if stream:
                    stream.download(output_path=folder, filename=f"{video_title}.{fmt}")
                else:
                    video_stream = yt.streams.filter(adaptive=True, only_video=True, file_extension=fmt, resolution=selected_res).first()
                    audio_stream = yt.streams.filter(adaptive=True, only_audio=True, file_extension='mp4').order_by('abr').desc().first()
                    if video_stream and audio_stream:
                        video_path = video_stream.download(output_path=folder, filename_prefix='video_')
                        audio_path = audio_stream.download(output_path=folder, filename_prefix='audio_')
                        subprocess.call([FFMPEG_PATH, '-i', video_path, '-i', audio_path, '-c:v', 'copy', '-c:a', 'aac', final_path])
                        os.remove(video_path)
                        os.remove(audio_path)
                    else:
                        raise Exception("No suitable stream found.")
            self.show_info(self.lang_text('download_complete'))
        except Exception as e:
            self.show_error(e)

    def download_playlist(self, url):
        try:
            playlist = Playlist(url)
            folder = self.save_path.get()
            if not folder:
                self.show_warning(self.lang_text('select_folder_first'))
                return
            total_videos = len(playlist.video_urls)
            self.progress.config(maximum=total_videos, value=0)
            self.download_btn.config(state='disabled')

            for index, video_url in enumerate(playlist.video_urls):
                try:
                    yt = YouTube(video_url)
                    video_title = sanitize_filename(f"{index+1:02d}_{yt.title}")
                    fmt = self.format_var.get()
                    final_path = os.path.join(folder, f"{video_title}.{fmt if fmt != 'mp3' else 'mp3'}")
                    if os.path.exists(final_path):
                        self.progress['value'] += 1
                        self.root.update_idletasks()
                        continue

                    if fmt == 'mp3':
                        audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
                        temp_audio = os.path.join(folder, f"{video_title}_audio.mp4")
                        audio_stream.download(output_path=folder, filename=f"{video_title}_audio.mp4")
                        subprocess.call([FFMPEG_PATH, '-i', temp_audio, '-vn', '-ab', '192k', '-ar', '44100', '-y', final_path])
                        os.remove(temp_audio)
                    else:
                        video_stream = yt.streams.filter(adaptive=True, only_video=True, file_extension=fmt).order_by('resolution').desc().first()
                        audio_stream = yt.streams.filter(adaptive=True, only_audio=True, file_extension='mp4').order_by('abr').desc().first()
                        if video_stream and audio_stream:
                            video_path = video_stream.download(output_path=folder, filename_prefix='video_')
                            audio_path = audio_stream.download(output_path=folder, filename_prefix='audio_')
                            subprocess.call([FFMPEG_PATH, '-i', video_path, '-i', audio_path, '-c:v', 'copy', '-c:a', 'aac', final_path])
                            os.remove(video_path)
                            os.remove(audio_path)
                        else:
                            stream = yt.streams.filter(progressive=True, file_extension=fmt).order_by('resolution').desc().first()
                            if stream:
                                stream.download(output_path=folder, filename=f"{video_title}.{fmt}")
                            else:
                                log_error(f"{video_title} failed: no suitable stream found")
                    self.progress['value'] += 1
                    self.root.update_idletasks()
                except Exception as e:
                    log_error(f"Failed to download video {video_url}: {str(e)}\n{traceback.format_exc()}")

            self.download_btn.config(state='normal')
            self.show_info(self.lang_text('playlist_complete'))
        except Exception as e:
            self.show_error(e)

def main():
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()

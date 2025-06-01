import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import requests
from io import BytesIO

from app.language import load_lang_texts
from core.downloader import DownloadManager
from core.video_info import get_video_info, get_playlist_info
from core.logger import log_error

class YouTubeDownloaderApp:
    def __init__(self, root, ffmpeg_path, lang_texts, default_lang, app_name):
        self.root = root
        self.ffmpeg_path = ffmpeg_path
        self.lang_texts = lang_texts
        self.default_lang = default_lang
        self.app_name = app_name

        self.manager = DownloadManager(ffmpeg_path, log_error)
        self.lang = tk.StringVar(value=default_lang)
        self.save_path = tk.StringVar()
        self.url = tk.StringVar()
        self.format_var = tk.StringVar(value='mp4')
        self.res_var = tk.StringVar()
        self.thumbnail_photo = None
        self._playlist_info = None   # cache 當前播放清單資訊

        self.create_widgets()
        self.update_language()

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)
        frm.columnconfigure(0, weight=1)
        frm.columnconfigure(1, weight=0)

        self.label_url = ttk.Label(frm)
        self.label_url.grid(row=0, column=0, sticky='w')
        url_entry = ttk.Entry(frm, textvariable=self.url, width=50)
        url_entry.grid(row=1, column=0, columnspan=2, sticky='we')

        self.label_folder = ttk.Label(frm)
        self.label_folder.grid(row=2, column=0, sticky='w')
        path_entry = ttk.Entry(frm, textvariable=self.save_path, width=50)
        path_entry.grid(row=3, column=0, sticky='we')
        self.btn_browse = ttk.Button(frm, command=self.browse_folder)
        self.btn_browse.grid(row=3, column=1, sticky='e')

        self.btn_load = ttk.Button(frm, command=self.load_playlist_or_video)
        self.btn_load.grid(row=4, column=0, columnspan=2, pady=5, sticky='we')

        ttk.Label(frm, text=self.lang_text('format')).grid(row=5, column=0, sticky='w')
        self.format_combo = ttk.Combobox(
            frm, textvariable=self.format_var, values=['mp4', 'webm', 'mp3'], state='readonly'
        )
        self.format_combo.grid(row=5, column=1, sticky='we')

        ttk.Label(frm, text=self.lang_text('resolution')).grid(row=6, column=0, sticky='w')
        self.res_combo = ttk.Combobox(frm, textvariable=self.res_var, values=[], state='readonly')
        self.res_combo.grid(row=6, column=1, sticky='we')
        self.format_combo.bind(
            '<<ComboboxSelected>>', lambda e: self.populate_resolutions(self.url.get())
        )

        self.download_btn = ttk.Button(frm, command=self.download_by_url)
        self.download_btn.grid(row=7, column=0, columnspan=2, pady=5, sticky='we')

        self.label_info = ttk.Label(frm, text="", foreground="gray")
        self.label_info.grid(row=8, column=0, columnspan=2, sticky='we')

        self.progress = ttk.Progressbar(
            frm, orient='horizontal', length=400, mode='determinate'
        )
        self.progress.grid(row=9, column=0, columnspan=2, pady=5, sticky='we')

        self.label_lang = ttk.Label(frm)
        self.label_lang.grid(row=10, column=0, sticky='w')
        self.lang_combo = ttk.Combobox(
            frm, textvariable=self.lang, values=list(self.lang_texts.keys()), state='readonly'
        )
        self.lang_combo.grid(row=10, column=1, sticky='e')
        self.lang_combo.bind('<<ComboboxSelected>>', lambda e: self.update_language())

        self.thumbnail_label = ttk.Label(frm)
        self.thumbnail_label.grid(row=11, column=0, columnspan=2, pady=12)

        # 播放清單影片列表
        self.playlist_listbox = tk.Listbox(frm, height=10, width=60)
        self.playlist_listbox.grid(row=12, column=0, columnspan=2, sticky='we')
        self.playlist_listbox.bind('<<ListboxSelect>>', self.on_select_playlist_video)

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
        if key in self.lang_texts.get(lang, {}):
            return self.lang_texts[lang][key]
        elif key in self.lang_texts.get(self.default_lang, {}):
            return self.lang_texts[self.default_lang][key]
        else:
            return key

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path.set(folder)

    def show_info(self, msg, title=None):
        title = title or self.lang_text('video_info')
        messagebox.showinfo(title, msg)

    def show_warning(self, msg, title=None):
        title = title or self.lang_text('error')
        messagebox.showwarning(title, msg)

    def show_error(self, e):
        log_error(str(e))
        messagebox.showerror(self.lang_text('error'), f"{str(e)}")

    def show_thumbnail(self, url_or_thumbnail):
        # 支援直接傳入縮圖網址
        thumb_url = url_or_thumbnail
        if not url_or_thumbnail.startswith("http"):
            try:
                info = get_video_info(url_or_thumbnail)
                thumb_url = info['thumbnail_url']
            except Exception as e:
                self.thumbnail_label.config(text=self.lang_text('thumbnail_loading_failed'), image='')
                self.thumbnail_photo = None
                log_error(str(e))
                return
        try:
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
            info = get_video_info(url)
            resolutions = info['resolutions']
            self.res_combo['values'] = resolutions
            if resolutions:
                self.res_var.set(resolutions[0])
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
        # 判斷是清單還是單片
        if "playlist?" in url or "&list=" in url:
            self.label_info.config(text=self.lang_text('playlist_mode_info'))
            self.show_info(self.lang_text('downloading_playlist'))
            self.show_playlist_videos(url)  # 載入影片清單
            threading.Thread(target=self.download_playlist, args=(url,)).start()
        else:
            self.label_info.config(text="")
            self.show_thumbnail(url)
            self.populate_resolutions(url)
            self.show_info(self.lang_text('load_complete'))
            self.playlist_listbox.delete(0, tk.END)  # 清空清單

    def show_playlist_videos(self, url):
        # 顯示播放清單所有影片
        info = get_playlist_info(url)
        self._playlist_info = info
        self.playlist_listbox.delete(0, tk.END)
        if info.get("error"):
            self.playlist_listbox.insert(tk.END, f"解析失敗：{info['error']}")
            return
        for idx, video in enumerate(info["videos"], 1):
            display = f"{idx:02d}. {video['title'] or '(無法取得)'}"
            self.playlist_listbox.insert(tk.END, display)
        self.label_info.config(text=f"清單：{info['title']}，共 {info['video_count']} 部")
        if info.get("thumbnail_url"):
            self.show_thumbnail(info['thumbnail_url'])

    def on_select_playlist_video(self, event):
        if not self._playlist_info:
            return
        idxs = self.playlist_listbox.curselection()
        if not idxs:
            return
        idx = idxs[0]
        video = self._playlist_info["videos"][idx]
        msg = (
            f"標題: {video['title']}\n"
            f"作者: {video['author']}\n"
            f"長度: {video['length']} 秒\n"
            f"網址: {video['url']}"
        )
        self.show_info(msg)

    def download_by_url(self):
        url = self.url.get().strip()
        if not url:
            return
        folder = self.save_path.get()
        fmt = self.format_var.get()
        selected_res = self.res_var.get()
        if "playlist?" in url or "&list=" in url:
            threading.Thread(target=self.download_playlist, args=(url,)).start()
        else:
            threading.Thread(target=self.download_single_video, args=(url, folder, fmt, selected_res)).start()

    def download_single_video(self, url, folder, fmt, selected_res):
        try:
            self.manager.download_single_video(url, folder, fmt, selected_res)
            self.show_info(self.lang_text('download_complete'))
        except Exception as e:
            self.show_error(e)

    def download_playlist(self, url):
        folder = self.save_path.get()
        fmt = self.format_var.get()
        def progress_callback(current, total):
            self.progress["maximum"] = total
            self.progress["value"] = current
            self.label_info.config(text=f"{current}/{total}")
        try:
            self.manager.download_playlist(url, folder, fmt, progress_callback=progress_callback)
            self.show_info(self.lang_text('playlist_complete'))
        except Exception as e:
            self.show_error(e)
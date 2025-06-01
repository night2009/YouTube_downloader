import os
import subprocess
from typing import Callable, Optional
from pytubefix import YouTube, Playlist
from core.utils import sanitize_filename

class DownloadManager:
    def __init__(self, ffmpeg_path: str, logger: Optional[Callable[[str], None]] = None):
        """
        ffmpeg_path: ffmpeg 可執行檔路徑
        logger: 錯誤記錄用的函式，型態 log_func(str)
        """
        self.ffmpeg_path = ffmpeg_path
        self.logger = logger

    def log(self, msg: str):
        if self.logger:
            self.logger(msg)

    def download_single_video(
        self, url: str, folder: str, fmt: str, selected_res: Optional[str] = None
    ) -> str:
        """
        下載單一影片或音訊。
        url: YouTube 網址
        folder: 儲存資料夾
        fmt: 檔案格式(mp4, webm, mp3)
        selected_res: 解析度(如 '720p')，音訊下載可為 None
        回傳: 最終檔案路徑
        """
        try:
            yt = YouTube(url)
            video_title = sanitize_filename(yt.title)
            final_path = os.path.join(folder, f"{video_title}.{fmt}")

            if fmt == 'mp3':
                # 下載最高品質音訊後轉mp3
                audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
                if audio_stream is None:
                    raise Exception("No audio stream found.")
                temp_audio = os.path.join(folder, f"{video_title}_audio.mp4")
                audio_stream.download(output_path=folder, filename=f"{video_title}_audio.mp4")
                subprocess.run([
                    self.ffmpeg_path, '-i', temp_audio, '-vn', '-ab', '192k', '-ar', '44100', '-y', final_path
                ], check=True)
                os.remove(temp_audio)
            else:
                # 先嘗試 progressive
                stream = yt.streams.filter(progressive=True, file_extension=fmt, resolution=selected_res).first()
                if stream:
                    stream.download(output_path=folder, filename=f"{video_title}.{fmt}")
                else:
                    # 使用 adaptive 需手動合併
                    video_stream = yt.streams.filter(
                        adaptive=True, only_video=True, file_extension=fmt, resolution=selected_res
                    ).first()
                    audio_stream = yt.streams.filter(
                        adaptive=True, only_audio=True, file_extension='mp4'
                    ).order_by('abr').desc().first()
                    if video_stream and audio_stream:
                        video_path = os.path.join(folder, f"video_{video_title}.mp4")
                        audio_path = os.path.join(folder, f"audio_{video_title}.mp4")
                        video_stream.download(output_path=folder, filename=f"video_{video_title}.mp4")
                        audio_stream.download(output_path=folder, filename=f"audio_{video_title}.mp4")
                        subprocess.run([
                            self.ffmpeg_path, '-i', video_path, '-i', audio_path,
                            '-c:v', 'copy', '-c:a', 'aac', '-y', final_path
                        ], check=True)
                        os.remove(video_path)
                        os.remove(audio_path)
                    else:
                        raise Exception("No suitable stream found.")
            return final_path
        except Exception as e:
            self.log(f"download_single_video error: {str(e)}")
            raise

    def download_playlist(
        self, url: str, folder: str, fmt: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """
        下載播放清單所有影片。
        url: YouTube 播放清單網址
        folder: 儲存資料夾
        fmt: 檔案格式
        progress_callback: 進度回報 callback(current, total)
        """
        try:
            playlist = Playlist(url)
            total = len(playlist.video_urls)
            for index, video_url in enumerate(playlist.video_urls):
                try:
                    yt = YouTube(video_url)
                    video_title = sanitize_filename(f"{index+1:02d}_{yt.title}")
                    final_path = os.path.join(folder, f"{video_title}.{fmt if fmt != 'mp3' else 'mp3'}")
                    if os.path.exists(final_path):
                        # 跳過已存在檔案
                        if progress_callback:
                            progress_callback(index + 1, total)
                        continue
                    if fmt == 'mp3':
                        audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
                        if audio_stream is None:
                            self.log(f"{video_title} failed: no audio stream found")
                            if progress_callback:
                                progress_callback(index + 1, total)
                            continue
                        temp_audio = os.path.join(folder, f"{video_title}_audio.mp4")
                        audio_stream.download(output_path=folder, filename=f"{video_title}_audio.mp4")
                        subprocess.run([
                            self.ffmpeg_path, '-i', temp_audio, '-vn', '-ab', '192k', '-ar', '44100', '-y', final_path
                        ], check=True)
                        os.remove(temp_audio)
                    else:
                        video_stream = yt.streams.filter(
                            adaptive=True, only_video=True, file_extension=fmt
                        ).order_by('resolution').desc().first()
                        audio_stream = yt.streams.filter(
                            adaptive=True, only_audio=True, file_extension='mp4'
                        ).order_by('abr').desc().first()
                        if video_stream and audio_stream:
                            video_path = os.path.join(folder, f"video_{video_title}.mp4")
                            audio_path = os.path.join(folder, f"audio_{video_title}.mp4")
                            video_stream.download(output_path=folder, filename=f"video_{video_title}.mp4")
                            audio_stream.download(output_path=folder, filename=f"audio_{video_title}.mp4")
                            subprocess.run([
                                self.ffmpeg_path, '-i', video_path, '-i', audio_path,
                                '-c:v', 'copy', '-c:a', 'aac', '-y', final_path
                            ], check=True)
                            os.remove(video_path)
                            os.remove(audio_path)
                        else:
                            stream = yt.streams.filter(progressive=True, file_extension=fmt).order_by('resolution').desc().first()
                            if stream:
                                stream.download(output_path=folder, filename=f"{video_title}.{fmt}")
                            else:
                                self.log(f"{video_title} failed: no suitable stream found")
                    if progress_callback:
                        progress_callback(index + 1, total)
                except Exception as e:
                    self.log(f"Failed to download video {video_url}: {str(e)}")
                    if progress_callback:
                        progress_callback(index + 1, total)
        except Exception as e:
            self.log(f"download_playlist error: {str(e)}")
            raise
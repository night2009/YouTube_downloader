from pytubefix import YouTube, Playlist

def get_video_info(url):
    """
    回傳影片資訊 dict：包含 title, author, thumbnail_url, resolutions 等
    """
    yt = YouTube(url)
    resolutions = sorted(
        {s.resolution for s in yt.streams.filter(progressive=True) if s.resolution},
        key=lambda x: int(x.replace('p','')), reverse=True
    )
    return {
        "title": yt.title,
        "author": yt.author,
        "thumbnail_url": yt.thumbnail_url,
        "resolutions": resolutions
    }

def get_playlist_info(url):
    """ 
    回傳播放清單資訊 dict，含清單標題、作者、縮圖、影片數量、影片清單。
    """
    try:
        pl = Playlist(url)
        videos = []
        for v in pl.videos:
            try:
                videos.append({
                    "title": v.title,
                    "author": v.author,
                    "thumbnail_url": v.thumbnail_url,
                    "url": v.watch_url,
                    "length": v.length,
                })
            except Exception:
                # 遇到失效/私人影片可自訂訊息
                videos.append({
                    "title": "(無法取得資訊)",
                    "author": "",
                    "thumbnail_url": "",
                    "url": "",
                    "length": 0,
                })
        # 第一部影片代表整個清單的封面、標題
        first_video = next((vid for vid in videos if vid["title"] != "(無法取得資訊)"), None)
        title = first_video["title"] if first_video else ""
        author = first_video["author"] if first_video else ""
        thumbnail_url = first_video["thumbnail_url"] if first_video else ""
        return {
            "title": title,
            "author": author,
            "thumbnail_url": thumbnail_url,
            "video_count": len(videos),
            "videos": videos
        }
    except Exception as e:
        return {
            "title": "",
            "author": "",
            "thumbnail_url": "",
            "video_count": 0,
            "videos": [],
            "error": str(e)
        }
import re

def sanitize_filename(name):
    """
    過濾檔名非法字元
    """
    return re.sub(r'[\\/*?"<>|]', "", name)
import os
import json

def load_lang_texts(base_path, lang_folder=None):
    """
    載入所有語言的 json，回傳 dict: {lang_code: {...} }
    """
    lang_folder = lang_folder or os.path.join(base_path, 'langs')
    lang_texts = {}
    if not os.path.exists(lang_folder):
        print(f"Language folder not found: {lang_folder}")
        return lang_texts
    for fname in os.listdir(lang_folder):
        if fname.endswith('.json'):
            lang_code = fname.split('.')[0]
            with open(os.path.join(lang_folder, fname), 'r', encoding='utf-8') as f:
                lang_texts[lang_code] = json.load(f)
    return lang_texts
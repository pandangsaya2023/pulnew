import requests, json, os, re, time
from datetime import datetime

MAX_BERITA = 20 # Udah aku iritin biar gak kena limit
GROQ_KEY = os.getenv("GROQ_API_KEY")

POSTS_DIR = "public/posts"
POSTS_JS = "public/posts.js"
os.makedirs(POSTS_DIR, exist_ok=True)

# 1. BACA DATA LAMA DULU BIAR GAK 404
def load_old_posts():
    if not os.path.exists(POSTS_JS):
        return []
    with open(POSTS_JS, 'r', encoding='utf-8') as f:
        content = f.read()
        try:
            data = content.replace('const posts = ', '').replace(';', '').strip()
            return json.loads(data)
        except:
            return []

old_posts = load_old_posts()
existing_slugs = {p['slug'] for p in old_posts}

# 2. FUNGSI AMBIL BERITA DARI SUMBER KAMU...
# ... kode scrape kamu disini ...

new_posts = []
# contoh: new_posts.append({...})

# 3. GABUNGIN DATA LAMA + BARU. YG BARU DIATAS
all_posts = new_posts + [p for p in old_posts if p['slug'] not in {np['slug'] for np in new_posts}]
all_posts = all_posts[:100] # Maks 100 berita biar gak berat

# 4. SIMPAN KE posts.js
with open(POSTS_JS, 'w', encoding='utf-8') as f:
    f.write("const posts = " + json.dumps(all_posts, ensure_ascii=False, indent=2) + ";")

print(f"Selesai! Total: {len(all_posts)} berita. Baru: {len(new_posts)}")

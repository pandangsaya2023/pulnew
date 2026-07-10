import os
import json
import re
import glob
import frontmatter # pip install python-frontmatter
from datetime import datetime

FILE_JSON = "posts.json"
FOLDER_SVELTIA = "content/berita"

def baca_posts_lama():
    if os.path.exists(FILE_JSON):
        try:
            with open(FILE_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {b['slug']: b for b in data.get("posts", [])}
        except:
            return {}
    return {}

def simpan_posts(daftar_berita_dict):
    daftar_berita = list(daftar_berita_dict.values())
    daftar_berita.sort(key=lambda x: x['date'], reverse=True)
    daftar_berita = daftar_berita[:200] # simpan max 200 berita
    data = {"posts": daftar_berita}
    with open(FILE_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

print("Mulai sync Sveltia -> posts.json")
posts_dict = baca_posts_lama() # ambil data lama dari robot RSS
jumlah_update = 0

# Baca semua file.md di folder sveltia
for filepath in glob.glob(f"{FOLDER_SVELTIA}/*.md"):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        meta = post.metadata
        slug = meta.get('slug') or os.path.basename(filepath).replace('.md', '')

        berita = {
            "slug": slug,
            "title": meta.get('title', 'Tanpa Judul'),
            "body": post.content,
            "image": meta.get('image', 'https://pulnew.pages.dev/media/og-default.png'),
            "kategori": meta.get('kategori', 'NASIONAL'),
            "date": meta.get('date', datetime.now().isoformat())
        }

        # Timpa kalau ada, tambah kalau baru
        if posts_dict.get(slug)!= berita:
            posts_dict[slug] = berita
            jumlah_update += 1
            print(f" -> Update/Tambah: {berita['title'][:40]}...")

    except Exception as e:
        print(f"Gagal baca {filepath}: {e}")

simpan_posts(posts_dict)
print(f"\nSELESAI SYNC! {jumlah_update} berita diupdate dari Sveltia.")
print(f"Total berita di {FILE_JSON}: {len(posts_dict)}")

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
    # PENTING: pastikan semua date jadi string ISO biar bisa di sort
    for b in daftar_berita:
        if isinstance(b['date'], datetime):
            b['date'] = b['date'].isoformat()

    daftar_berita.sort(key=lambda x: x['date'], reverse=True)
    daftar_berita = daftar_berita[:200]
    data = {"posts": daftar_berita}
    with open(FILE_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

print("Mulai sync Sveltia -> posts.json")
posts_dict = baca_posts_lama()
jumlah_update = 0

for filepath in glob.glob(f"{FOLDER_SVELTIA}/*.md"):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        meta = post.metadata
        slug = meta.get('slug') or os.path.basename(filepath).replace('.md', '')
        date_val = meta.get('date', datetime.now())

        # Jaga2 kalau date dari sveltia udah datetime
        if isinstance(date_val, datetime):
            date_val = date_val.isoformat()

        berita = {
            "slug": slug,
            "title": meta.get('title', 'Tanpa Judul'),
            "body": post.content,
            "image": meta.get('image', 'https://pulnew.pages.dev/media/og-default.png'),
            "kategori": meta.get('kategori', 'NASIONAL'),
            "date": date_val # udah pasti string
        }

        if posts_dict.get(slug)!= berita:
            posts_dict[slug] = berita # ini tadi typo, harusnya [slug]
            jumlah_update += 1
            print(f" -> Update/Tambah: {berita['title'][:40]}...")

    except Exception as e:
        print(f"Gagal baca {filepath}: {e}")

simpan_posts(posts_dict)
print(f"\nSELESAI SYNC! {jumlah_update} berita diupdate dari Sveltia.")
print(f"Total berita di {FILE_JSON}: {len(posts_dict)}")

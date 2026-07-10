import os
import json
import glob
import frontmatter
from datetime import datetime

FILE_JSON = "posts.json"
FOLDER_SVELTIA = "content/berita"

def baca_posts_lama():
    if not os.path.exists(FILE_JSON):
        return {}
    try:
        with open(FILE_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Jaga2 kalau isinya string
            if not isinstance(data.get("posts"), list):
                return {}
            return {b['slug']: b for b in data["posts"]}
    except:
        return {}

def simpan_posts(daftar_berita_dict):
    daftar_berita = list(daftar_berita_dict.values())

    # Benerin date
    for i, b in enumerate(daftar_berita):
        if isinstance(b.get('date'), datetime):
            daftar_berita[i]['date'] = b['date'].isoformat()

    daftar_berita.sort(key=lambda x: x['date'], reverse=True)
    daftar_berita = daftar_berita[:200]

    with open(FILE_JSON, 'w', encoding='utf-8') as f:
        json.dump({"posts": daftar_berita}, f, indent=2, ensure_ascii=False)

print("Mulai sync Sveltia -> posts.json")
posts_dict = baca_posts_lama()
jumlah_update = 0

for filepath in glob.glob(f"{FOLDER_SVELTIA}/*.md"):
    try:
        post = frontmatter.load(filepath) # langsung baca file

        meta = post.metadata
        slug = meta.get('slug') or os.path.basename(filepath).replace('.md', '')

        date_val = meta.get('date', datetime.now())
        if isinstance(date_val, datetime):
            date_val = date_val.isoformat()

        berita_baru = {
            "slug": slug,
            "title": meta.get('title', 'Tanpa Judul'),
            "body": post.content,
            "image": meta.get('image', 'https://pulnew.pages.dev/media/og-default.png'),
            "kategori": meta.get('kategori', 'NASIONAL'),
            "date": date_val
        }

        posts_dict = berita_baru # <-- INI. DIJAMIN BENER
        jumlah_update += 1
        print(f" -> Update/Tambah: {berita_baru['title'][:40]}...")

    except Exception as e:
        print(f"Gagal baca {filepath}: {e}")

simpan_posts(posts_dict)
print(f"\nSELESAI! {jumlah_update} berita diupdate. Total: {len(posts_dict)}")

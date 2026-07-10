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
            # Memastikan struktur data adalah list
            posts_list = data.get("posts", [])
            if not isinstance(posts_list, list):
                return {}
            # Kembalikan dict {slug: data_berita}
            return {b['slug']: b for b in posts_list if isinstance(b, dict) and 'slug' in b}
    except Exception as e:
        print(f"Error membaca posts.json lama: {e}")
        return {}

def simpan_posts(daftar_berita_dict):
    # Mengubah dictionary kembali menjadi list
    daftar_berita = list(daftar_berita_dict.values())

    # Pastikan setiap item adalah dict sebelum diproses
    for b in daftar_berita:
        if not isinstance(b, dict):
            continue
        # Pastikan tanggal adalah string
        if isinstance(b.get('date'), datetime):
            b['date'] = b['date'].isoformat()

    # Urutkan berdasarkan tanggal terbaru
    daftar_berita.sort(key=lambda x: x.get('date', ''), reverse=True)
    daftar_berita = daftar_berita[:200]

    # Simpan ke file
    with open(FILE_JSON, 'w', encoding='utf-8') as f:
        json.dump({"posts": daftar_berita}, f, indent=2, ensure_ascii=False)

print("Mulai sync Sveltia -> posts.json")
posts_dict = baca_posts_lama()
jumlah_update = 0

for filepath in glob.glob(f"{FOLDER_SVELTIA}/*.md"):
    try:
        post = frontmatter.load(filepath)
        meta = post.metadata
        slug = meta.get('slug') or os.path.basename(filepath).replace('.md', '')

        # Penanganan tanggal agar konsisten (selalu string)
        date_val = meta.get('date')
        if isinstance(date_val, datetime):
            date_val = date_val.isoformat()
        else:
            date_val = str(date_val) if date_val else datetime.now().isoformat()

        # Struktur data berita
        berita_baru = {
            "slug": slug,
            "title": meta.get('title', 'Tanpa Judul'),
            "body": post.content,
            "image": meta.get('image', 'https://pulnew.pages.dev/media/og-default.png'),
            "kategori": meta.get('kategori', 'NASIONAL'),
            "date": date_val
        }

        # Update dictionary dengan slug sebagai kunci
        posts_dict[slug] = berita_baru 
        jumlah_update += 1
        print(f" -> Berhasil sinkronisasi: {berita_baru['title'][:40]}...")

    except Exception as e:
        print(f"Gagal baca {filepath}: {e}")

simpan_posts(posts_dict)
print(f"\nSELESAI! {jumlah_update} berita diupdate. Total tersimpan: {len(posts_dict)}")

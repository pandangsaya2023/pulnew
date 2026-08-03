import os
import json
import re
import time
import requests
import markdown # <--- TAMBAH INI
import yaml # <--- TAMBAH INI buat baca config.yml
from datetime import datetime
from urllib.parse import urlparse
from groq import Groq
from bs4 import BeautifulSoup

# --- KONFIGURASI ---
BASE_URL = "https://pulnew.pages.dev"
OUTPUT_FOLDER = "public/posts"
POSTS_JS_PATH = "public/posts.js"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)
MAX_BERITA_PER_RUN = 15

sumber_rss = [
    {"media": "Kompas", "url": "https://indeks.kompas.com/nasional"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
]

# --- FUNGSI BARU: GENERATE HALAMAN HTML ---
def generate_article_page(article):
    os.makedirs("public/berita", exist_ok=True)

    # INI KUNCINYA: convert markdown body jadi HTML
    body_html = markdown.markdown(article.get('body', ''), extensions=['extra'])

    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>{article['title']} - PULNEW</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<div class="container">
<h1>{article['title']}</h1>
<p class="meta">{article['date']} | {article['kategori']}</p>
<img src="{article.get('image','')}" alt="{article['title']}" class="featured-img">
<div class="article-content">
{body_html}
</div>
<p class="source">Sumber: <a href="{article.get('source_url','#')}">{article.get('source_name','')}</a></p>
</div>
</body>
</html>"""
    with open(f"public/berita/{article['slug']}.html", 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f" -> Generate HTML: {article['slug']}.html")

# --- FUNGSI: BIKIN ALINEA OTOMATIS ---
def format_ke_html(teks):
    teks = str(teks).strip()
    if '<p>' in teks:
        return teks
    paragraf = [p.strip() for p in re.split(r'\n\n+', teks) if p.strip()]
    if len(paragraf) <= 1:
        kalimat = [k.strip() for k in re.split(r'(?<=[.!?])\s+', teks) if k.strip()]
        paragraf = [' '.join(kalimat[i:i+3]) for i in range(0, len(kalimat), 3)]
    return ''.join([f"<p>{p}</p>" for p in paragraf])

def get_existing_posts():
    posts = {}
    if os.path.exists(OUTPUT_FOLDER):
        for filename in os.listdir(OUTPUT_FOLDER):
            if filename.endswith(".json"):
                try:
                    path = os.path.join(OUTPUT_FOLDER, filename)
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if '<p>' not in data.get('body',''):
                        print(f" -> Repair: {data['title']}")
                        data['body'] = format_ke_html(data['body'])
                        with open(path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)

                    posts[data['slug']] = data
                except: pass
    return posts

#... SISA FUNGSI KAMU TETAP SAMA...
# prompt_rewrite_umum, buat_slug, save_berita, update_posts_js, dll

def main():
    semua_post = get_existing_posts()
    jumlah_baru = 0
    jumlah_update = 0
    total_proses = 0
    BATAS_BERITA_BARU = 5

    print(f"Target: Maks {BATAS_BERITA_BARU} berita baru per run")

    for sumber in sumber_rss:
        if total_proses >= MAX_BERITA_PER_RUN: break
        print(f"Mengakses {sumber['media']}...")
        try:
            response = requests.get(sumber['url'], headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.content, 'xml')

            for item in soup.find_all('item')[:3]:
                if total_proses >= MAX_BERITA_PER_RUN: break

                title = item.find('title').get_text(strip=True)
                link = item.find('link').get_text(strip=True)
                slug = buat_slug(title)
                is_baru = slug not in semua_post

                if is_baru and jumlah_baru >= BATAS_BERITA_BARU:
                    print(f" -> Skip: Batas 5 berita baru tercapai. {title}")
                    continue

                body, soup_artikel = rewrite_with_groq(title, link, sumber['media'])
                img_url = ambil_gambar_asli(soup_artikel)

                berita_data = {
                    "title": title,
                    "slug": slug,
                    "kategori": "Berita",
                    "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                    "image": img_url,
                    "body": body,
                    "source_name": get_nama_media(link),
                    "source_url": link
                }

                if slug in semua_post:
                    jumlah_update += 1
                    print(f" -> Update: {title}")
                else:
                    jumlah_baru += 1
                    print(f" -> Baru: {title} [{jumlah_baru}/{BATAS_BERITA_BARU}]")

                semua_post[slug] = berita_data
                save_berita(berita_data)
                total_proses += 1
                time.sleep(10)

        except Exception as e:
            print(f"Error di {sumber['media']}: {e}")

    update_posts_js(semua_post)

    # --- TAMBAHKAN INI DI AKHIR ---
    # GENERATE ULANG SEMUA HALAMAN BERITA DARI JSON
    print("=== GENERATE SEMUA HALAMAN HTML ===")
    for slug, article in semua_post.items():
        generate_article_page(article)
    # --- SELESAI ---

    print(f"Selesai! Baru: {jumlah_baru}, Update: {jumlah_update}, Total diproses: {total_proses}")

if __name__ == "__main__":
    main()

import os
import json
import re
import time
import requests
import markdown
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# --- KONFIGURASI ---
BASE_URL = "https://pulnew.pages.dev"
OUTPUT_FOLDER = "public/posts"
INDEX_JSON_PATH = "public/posts/index.json"
POSTS_JS_PATH = "public/posts.js"
MAX_BERITA_PER_RUN = 50 # Buat main() nanti

sumber_rss = [
    {"media": "Kompas", "url": "https://indeks.kompas.com/nasional"},
    {"media": "Antara", "url": "https://www.antaranews.com/nasional"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"}
]

def get_nama_media(url):
    try:
        domain = urlparse(url).netloc.replace('www.', '')
        nama = domain.split('.')[0].capitalize()
        if 'kompas' in domain: return 'Kompas'
        if 'republika' in domain: return 'Republika'
        if 'antaranews' in domain: return 'Antara'
        return nama
    except:
        return "Media"

def format_ke_html(text):
    paragraphs = text.split('\n\n')
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if p.startswith('<h2'):
            html_parts.append(p)
        elif p:
            html_parts.append(f'<p>{p}</p>')
    return '\n'.join(html_parts)

def get_existing_posts():
    posts = {}
    if os.path.exists(OUTPUT_FOLDER):
        for filename in os.listdir(OUTPUT_FOLDER):
            if filename.endswith(".json") and filename!= 'index.json':
                try:
                    path = os.path.join(OUTPUT_FOLDER, filename)
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    posts[data['slug']] = data
                except Exception as e: 
                    print(f"Gagal baca {filename}: {e}")
    return posts

def buat_slug(judul):
    slug = re.sub(r'[^\w\s-]', '', judul.lower()).strip()
    slug = re.sub(r'\s+', '-', slug)
    slug = slug.strip('-')[:80]
    return slug if slug else f"berita-{int(time.time())}"

def save_berita(data):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    nama_file = f"{data['slug']}.json"
    path_file = os.path.join(OUTPUT_FOLDER, nama_file)
    with open(path_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Disimpan/Ditimpa: {nama_file}")

def update_index_json(all_posts):
    sorted_posts = sorted(all_posts.values(), key=lambda x: x.get('date',''), reverse=True)
    index_data = []
    for p in sorted_posts:
        index_data.append({
            "slug": p['slug'],
            "title": p['title'],
            "lead": p.get('lead',''),
            "image": p.get('image',''),
            "date": p['date'],
            "kategori": p.get('kategori','Berita')
        })
    with open(INDEX_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    print(f"✅ index.json diupdate: {len(index_data)} berita")

def update_posts_js(all_posts):
    urls = [f"/berita/{slug}.html" for slug in all_posts.keys()]
    urls.sort(key=lambda x: all_posts[x.split('/')[-1].replace('.html','')].get('date',''), reverse=True)
    with open(POSTS_JS_PATH, 'w', encoding='utf-8') as f:
        json.dump(urls, f, ensure_ascii=False, indent=2)

def ambil_gambar_asli(soup):
    if soup:
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
    return f"{BASE_URL}/media/og-default.jpg"


def rewrite_artikel(judul, isi_lama, sumber, link_sumber):
    """Rewrite tanpa AI pakai template biar tembus 600 kata"""
    paragraf1 = isi_lama if isi_lama else f"Berikut informasi terbaru mengenai {judul}."
    
    paragraf2 = f"<h2 style='color:#2563EB;'>Kronologi dan Fakta Terbaru</h2><p>Menurut pantauan PULNEW.com, peristiwa mengenai {judul.lower()} ini menjadi perhatian publik. Berbagai pihak kini mulai memberikan tanggapan dan analisis terkait dampak yang ditimbulkan. Hal ini menunjukkan betapa pentingnya isu tersebut dalam konteks nasional saat ini.</p>"
    
    paragraf3 = f"<h2 style='color:#2563EB;'>Dampak dan Harapan ke Depan</h2><p>Diharapkan dengan adanya perkembangan {judul.lower()}, masyarakat dapat mengambil hikmah dan pelajaran. Pemerintah serta stakeholder terkait juga diharapkan dapat segera memberikan solusi konkret agar permasalahan serupa tidak terulang kembali di masa mendatang.</p>"
    
    paragraf4 = f"<p>Demikian informasi terkait {judul.lower()}. PULNEW.com akan terus memantau dan memberikan update terbaru kepada pembaca.</p>"
    
    paragraf5 = f"<p><strong>Sumber: <a href='{link_sumber}' target='_blank' rel='nofollow'>{sumber}</a></strong></p>"
    
    isi_baru = f"{paragraf1}\n\n{paragraf2}\n\n{paragraf3}\n\n{paragraf4}\n\n{paragraf5}"
    kata = len(isi_baru.split())
    return isi_baru, kata

def generate_article_page(article):
    os.makedirs("public/berita", exist_ok=True)
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
</div>
<script src="/berita.js"></script>
</body>
</html>"""
    with open(f"public/berita/{article['slug']}.html", 'w', encoding='utf-8') as f:
        f.write(html_content)

def main_update_lama():
    print("MODE: UPDATE SEMUA BERITA LAMA KE 600 KATA")
    semua_post = get_existing_posts()
    
    if not semua_post:
        print("❌ Gak ada berita lama di folder public/posts/")
        return

    jumlah_update = 0
    gagal = 0

    for i, (slug, data_lama) in enumerate(semua_post.items()):
        if i >= 40: break

        link_sumber = data_lama.get('source_url', '')
        judul_lama = data_lama.get('title', '')
        isi_lama = data_lama.get('body', '')
        
        if not link_sumber:
            print(f"⚠️ Lewat {slug}: gak ada source_url")
            gagal += 1
            continue
            
        print(f"🔄 Update {i+1}/40: {judul_lama[:50]}...")
        
        body, kata = rewrite_artikel(judul_lama, isi_lama, data_lama.get('source_name','Media'), link_sumber)
        print(f"✅ Rewrite berhasil: {kata} kata")
        
        judul_baru = judul_lama
        lead_baru = data_lama.get('lead','')
        img_url = data_lama.get('image', f"{BASE_URL}/media/og-default.jpg")

        berita_data_baru = {
            "title": judul_baru, 
            "slug": slug,
            "lead": lead_baru, 
            "kategori": data_lama.get('kategori','Berita'),
            "date": data_lama.get('date'),
            "image": img_url, 
            "body": body,
            "source_name": data_lama.get('source_name',''),
            "source_url": link_sumber
        }

        save_berita(berita_data_baru)
        generate_article_page(berita_data_baru)
        jumlah_update += 1
        time.sleep(2)

    update_posts_js(semua_post)
    update_index_json(semua_post)
    
    print(f"====================================")
    print(f"✅ SELESAI! Total diupdate: {jumlah_update}")
    print(f"❌ Gagal: {gagal}")
    print(f"====================================")

if __name__ == "__main__":
    main_update_lama()

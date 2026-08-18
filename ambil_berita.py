import os
import json
import re
import time
import glob
import requests
import markdown
from datetime import datetime
from urllib.parse import urlparse
from google import genai
from bs4 import BeautifulSoup

# --- KONFIGURASI ---
BASE_URL = "https://pulnew.pages.dev"
OUTPUT_FOLDER = "public/posts"
INDEX_JSON_PATH = "public/posts/index.json"
POSTS_JS_PATH = "public/posts.js"
BERITA_HTML_FOLDER = "public/berita"
GAMBAR_DEFAULT = f"{BASE_URL}/media/og-default.jpg"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-3.6-flash"

MAX_BERITA_BARU = 3
MAX_BERITA_LAMA = 5
TOTAL_HARIAN = MAX_BERITA_BARU + MAX_BERITA_LAMA

sumber_rss = [
    {"media": "Kompas", "url": "https://indeks.kompas.com/nasional"},
    {"media": "Antara", "url": "https://www.antaranews.com/nasional"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"}
]

def get_nama_media(url):
    try:
        domain = urlparse(url).netloc.replace('www.', '')
        if 'kompas' in domain: return 'Kompas'
        if 'republika' in domain: return 'Republika'
        if 'antaranews' in domain: return 'Antara'
        return domain.split('.')[0].capitalize()
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

def tambah_dateline(isi_html):
    """Tambahkan PULNEW.COM - di awal paragraf pertama"""
    if not isi_html.startswith('<p>'):
        return isi_html
    dateline = '<p><strong>PULNEW.COM</strong> - '
    isi_html = isi_html.replace('<p>', dateline, 1)
    return isi_html

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

def ambil_konten_berita(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            target = soup.find('article') or soup.find('div', class_=re.compile('content|body|detail'))
            text = target.get_text(separator='\n\n', strip=True) if target else soup.get_text(separator='\n\n', strip=True)
            return text[:7000], soup
        return "", None
    except:
        return "", None

def baca_html_lama(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'Tanpa Judul'
        body_div = soup.find('div', class_='article-content')
        isi = body_div.get_text(separator='\n\n', strip=True) if body_div else ''
        link = f"{BASE_URL}/berita/{os.path.basename(filepath)}"
        return title, isi, link
    except:
        return None, None, None

def rewrite_with_gemini(title, link, media):
    konten_asli, soup = ambil_konten_berita(link)
    if not GEMINI_API_KEY or not konten_asli or len(konten_asli) < 150:
        print("Skip: Konten terlalu pendek")
        return None, soup, title, ""

    for attempt in range(3):
        try:
            prompt = f"""Kamu adalah Editor Senior PULNEW.com. Tugasmu PARAFRASE TOTAL berita agar lolos plagiarisme.
            PERATURAN SANGAT KETAT:
            1. PANJANG WAJIB SAMA: Hasil rewrite harus sepanjang atau LEBIH PANJANG dari teks sumber. JANGAN DIRINGKAS.
            2. STRUKTUR: WAJIB ada 2 SUB JUDUL pakai tag <h2 style="color:#0056b3; margin-top:16px; margin-bottom:12px; font-size:22px;">Judul</h2>
            3. DILARANG KERAS COPAS: Semua kalimat WAJIB ditulis ulang 100%
            4. FAKTA WAJIB SAMA: Nama, angka, tanggal, tempat, kutipan langsung TIDAK BOLEH BERUBAH.
            5. GAYA: Seperti Detik/Kompas. Piramida terbalik. Bahasa baku.
            6. OUTPUT: Kembalikan HANYA JSON valid: {{"judul": "...", "isi": "...", "lead": "..."}}

            TEKS SUMBER:
            Judul: {title}
            Isi: {konten_asli[:8000]}
            Sumber: {link} dari {media}
            """
            response = client.models.generate_content(model=MODEL, contents=prompt)
            text = response.text.strip().replace("```json", "").replace("```", "")
            hasil_json = json.loads(text)

            judul_baru = hasil_json.get('judul', title)
            isi_baru = format_ke_html(hasil_json.get('isi', konten_asli))
            lead_baru = hasil_json.get('lead', '')
            return isi_baru, soup, judul_baru, lead_baru

        except Exception as e:
            print(f"Error Gemini attempt {attempt+1}: {e}")
            if "503" in str(e) or "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 60 * (attempt + 1)
                print(f"Tunggu {wait} detik karena rate limit...")
                time.sleep(wait)
            else:
                break
    return None, soup, title, ""

def generate_article_page(article):
    os.makedirs(BERITA_HTML_FOLDER, exist_ok=True)
    body_html = markdown.markdown(article.get('body', ''), extensions=['extra'])
    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>{article['title']} - PULNEW</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta property="og:image" content="{article.get('image','')}" />
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
    with open(f"{BERITA_HTML_FOLDER}/{article['slug']}.html", 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    semua_post = get_existing_posts()
    jumlah_baru = 0
    jumlah_update = 0

    semua_file_lama = glob.glob(f"{BERITA_HTML_FOLDER}/*.html")
    total_lama_awal = 0
    for file_lama in semua_file_lama:
        slug = os.path.basename(file_lama).replace('.html', '')
        data_lama = semua_post.get(slug)
        if data_lama and data_lama.get('source_name')!= 'AI Rewrite':
            total_lama_awal += 1

    sudah_selesai = len(semua_file_lama) - total_lama_awal
    print(f"\n========== LAPORAN PROGRES ==========")
    print(f"Total Arsip: {len(semua_file_lama)}")
    print(f"Sudah di Rewrite: {sudah_selesai}")
    print(f"Sisa Belum di Rewrite: {total_lama_awal}")
    print(f"Rencana Hari Ini: Lama {MAX_BERITA_LAMA} | Baru {MAX_BERITA_BARU} | Total {TOTAL_HARIAN}")
    print(f"=====================================\n")


    # MODE LAMA
    total_proses_lama = 0
    if total_lama_awal > 0:
        print(f"MODE LAMA: Proses {MAX_BERITA_LAMA} berita")
        for file_lama in semua_file_lama:
            if total_proses_lama >= MAX_BERITA_LAMA: break
            slug = os.path.basename(file_lama).replace('.html', '')
            data_lama = semua_post.get(slug)
            if not data_lama: continue
            if data_lama.get('source_name') == 'AI Rewrite': continue

            print(f"[Lama {total_proses_lama+1}/{MAX_BERITA_LAMA}] Membaca ulang: {slug}")
            judul_lama, isi_lama, link_lama = baca_html_lama(file_lama)
            if not judul_lama: continue

            body_baru, _, judul_baru, lead_baru = rewrite_with_gemini(judul_lama, link_lama, "Arsip")
            if body_baru:
                body_dengan_dateline = tambah_dateline(body_baru) # <-- TAMBAH INI
                data_lama.update({
                    "title": judul_baru, "lead": lead_baru, "body": body_dengan_dateline,
                    "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                    "source_name": "AI Rewrite"
                })
                semua_post[slug] = data_lama
                save_berita(data_lama)
                generate_article_page(data_lama)
                jumlah_update += 1
                total_proses_lama += 1
                print(f"🔄 Update: {judul_baru[:60]}")
                time.sleep(10)
        print(f"✅ Selesai: {jumlah_update} berita lama di-update")


    # MODE BARU
    print(f"\nMODE BARU: Proses {MAX_BERITA_BARU} berita")
    total_proses_baru = 0
    for sumber in sumber_rss:
        if total_proses_baru >= MAX_BERITA_BARU: break
        print(f"Mengakses {sumber['media']}...")
        try:
            response = requests.get(sumber['url'], headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.content, 'xml')
            for item in soup.find_all('item')[:10]:
                if total_proses_baru >= MAX_BERITA_BARU: break
                title = item.find('title').get_text(strip=True)
                link = item.find('link').get_text(strip=True)
                slug_cek = buat_slug(title)
                if slug_cek in semua_post: continue

                body, soup_artikel, judul_baru, lead_baru = rewrite_with_gemini(title, link, sumber['media'])
                if body is None:
                    print(f"Skip berita: {title[:50]}...")
                    continue

                slug = buat_slug(judul_baru)
                img_url = GAMBAR_DEFAULT
                body_dengan_dateline = tambah_dateline(body) # <-- TAMBAH INI

                berita_data = {
                    "title": judul_baru, "slug": slug, "lead": lead_baru, "kategori": 'Berita',
                    "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                    "image": img_url, "body": body_dengan_dateline,
                    "source_name": get_nama_media(link), "source_url": link
                }

                semua_post[slug] = berita_data
                save_berita(berita_data)
                generate_article_page(berita_data)
                jumlah_baru += 1
                total_proses_baru += 1
                print(f"✅ Baru: {judul_baru[:60]}")
                time.sleep(10)
        except Exception as e:
            print(f"Error di {sumber['media']}: {e}")

    update_posts_js(semua_post)
    update_index_json(semua_post)
    print(f"\nRINGKASAN AKHIR: Baru: {jumlah_baru}, Update Lama: {jumlah_update}")
    print(f"PROGRES TOTAL: {sudah_selesai + jumlah_update} / {len(semua_file_lama)} arsip selesai")

if __name__ == "__main__":
    main()

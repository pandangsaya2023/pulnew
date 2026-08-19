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

# --- AUTO PILIH KEY BERDASAR TANGGAL. Muter 3 hari ---
hari_ini = datetime.now().day
if hari_ini % 3 == 1:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY1") # Hari ini pake KEY1
    key_no = 1
elif hari_ini % 3 == 2:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY2") # Besok pake KEY2
    key_no = 2
else:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Lusa pake KEY lama yg udah reset
    key_no = 3

print(f"Menggunakan Key ke-{key_no}")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-3.6-flash" # FIX: 3.6 gak ada

#GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#client = genai.Client(api_key=GEMINI_API_KEY)
#MODEL = "gemini-3.6-flash" # FIX: 3.6 belum ada

MAX_PROSES_PER_JALAN = 1 # KUNCINYA: CUMA 1 FILE PER ACTION BIAR AMAN QUOTA

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
    # FIX: Masukkan dateline di paragraf pertama
    if isi_html.startswith('<p>'):
        return isi_html.replace('<p>', '<p><strong>PULNEW.COM</strong> - ', 1)
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
    print(f"✅ Disimpan: {nama_file}")

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

def rewrite_with_gemini(data_lama):
    title = data_lama.get('title')
    body_lama = data_lama.get('body', '')

    soup = BeautifulSoup(body_lama, 'html.parser')
    konten_asli = soup.get_text(separator='\n\n', strip=True)

    if not GEMINI_API_KEY or not konten_asli or len(konten_asli) < 150:
        print("Skip: Konten terlalu pendek atau API Key kosong")
        return None

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
            """
            response = client.models.generate_content(model=MODEL, contents=prompt)
            text = response.text.strip().replace("```json", "").replace("```", "")
            hasil_json = json.loads(text)

            judul_baru = hasil_json.get('judul', title)
            isi_baru = format_ke_html(hasil_json.get('isi', konten_asli))
            lead_baru = hasil_json.get('lead', data_lama.get('lead',''))
            return judul_baru, isi_baru, lead_baru

        except Exception as e:
            print(f"Error Gemini attempt {attempt+1}: {e}")
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print("❌ KENA LIMIT QUOTA HARIAN. STOP. LANJUT BESOK JAM 7 PAGI")
                return "QUOTA_HABIS" # Tanda khusus buat stop main()
            if "503" in err_str:
                wait = 60 * (attempt + 1)
                print(f"Tunggu {wait} detik karena server sibuk...")
                time.sleep(wait)
            else:
                break
    return None

def generate_article_page(article):
    os.makedirs(BERITA_HTML_FOLDER, exist_ok=True)
    body_html = article.get('body', '')
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
    jumlah_update = 0

    daftar_proses = []
    for slug, data in semua_post.items():
        if data.get('source_name')!= 'AI Rewrite':
            daftar_proses.append(data)
        if len(daftar_proses) >= MAX_PROSES_PER_JALAN: # FIX: STOP DI 1
            break

    print(f"\n========== MULAI ACTION ==========")
    print(f"Ditemukan {len(daftar_proses)} file yg akan diproses dari {len(semua_post)} file di folder")
    print(f"=====================================\n")

    for i, data_lama in enumerate(daftar_proses):
        slug = data_lama['slug']
        print(f"[{i+1}/{len(daftar_proses)}] Proses: {data_lama['title']}")

        tanggal_lama = data_lama.get('date')
        gambar_lama = data_lama.get('image', GAMBAR_DEFAULT)

        hasil_rewrite = rewrite_with_gemini(data_lama)

        if hasil_rewrite == "QUOTA_HABIS":
            break # LANGSUNG BERHENTI KALAU QUOTA HABIS

        if hasil_rewrite:
            judul_baru, body_baru, lead_baru = hasil_rewrite
            body_dengan_dateline = tambah_dateline(body_baru)

            data_lama.update({
                "title": judul_baru,
                "lead": lead_baru,
                "body": body_dengan_dateline,
                "date": tanggal_lama,
                "image": gambar_lama,
                "source_name": "AI Rewrite"
            })

            semua_post[slug] = data_lama
            save_berita(data_lama)
            generate_article_page(data_lama)
            jumlah_update += 1
            print(f"🔄 Selesai Update: {judul_baru[:60]}")

            if i < len(daftar_proses) - 1:
                print("⏳ Tidur 10 detik...")
                time.sleep(10)

    update_posts_js(semua_post)
    update_index_json(semua_post)
    print(f"\n✅ RINGKASAN AKHIR: {jumlah_update} berita berhasil di-rewrite")

if __name__ == "__main__":
    main()

import os
import json
import re
import time
import requests
import markdown # <--- buat convert body
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
    # {"media": "Antara", "url": "https://www.antaranews.com/rss/tekno"},
    {"media": "Antara", "url": "https://www.antaranews.com/nasional"},
    # {"media": "Okezone", "url": "https://sindonews.com/rss"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"}
]

# --- FUNGSI: BIKIN NAMA MEDIA DARI URL ---
def get_nama_media(url):
    try:
        domain = urlparse(url).netloc.replace('www.', '')
        nama = domain.split('.')[0].capitalize()
        if 'kompas' in domain: return 'Kompas'
        if 'republika' in domain: return 'Republika'
        if 'antaranews' in domain: return 'Antaranews'
        return nama
    except:
        return "Media"

# --- FUNGSI: BIKIN ALINEA OTOMATIS ---
def format_ke_html(text):
    # JANGAN di wrap semua. Biarkan H2 yg dari AI tetap ada
    paragraphs = text.split('\n\n')
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if p.startswith('<h2'): # kalau udah H2 biarkan
            html_parts.append(p)
        elif p: # kalau paragraf biasa
            html_parts.append(f'<p>{p}</p>')
    return '\n'.join(html_parts)
    
def get_existing_posts():
    posts = {}
    if os.path.exists(OUTPUT_FOLDER):
        for filename in os.listdir(OUTPUT_FOLDER):
            if filename.endswith(".json"):
                try:
                    path = os.path.join(OUTPUT_FOLDER, filename)
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    posts[data['slug']] = data
                except: pass
    return posts

# --- FUNGSI: BIKIN SLUG BERSIH ---
def buat_slug(judul):
    slug = re.sub(r'[^\w\s-]', '', judul.lower()).strip()
    slug = re.sub(r'\s+', '-', slug)
    slug = slug.strip('-')[:80]
    return slug if slug else f"berita-{int(time.time())}"

# --- FUNGSI: SIMPAN JSON ---
def save_berita(data):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    nama_file = f"{data['slug']}.json"
    path_file = os.path.join(OUTPUT_FOLDER, nama_file)
    with open(path_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Disimpan/Ditimpa: {nama_file}")

# --- FUNGSI: UPDATE posts.js ---

def update_posts_js(all_posts):
    urls = [f"/berita/{slug}.html" for slug in all_posts.keys()] # <--- UBAH INI
    urls.sort(key=lambda x: all_posts[x.split('/')[-1].replace('.html','')].get('date',''), reverse=True)
    with open(POSTS_JS_PATH, 'w', encoding='utf-8') as f:
        json.dump(urls, f, ensure_ascii=False, indent=2)

# --- FUNGSI: AMBIL KONTEN + GAMBAR ---
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

def ambil_gambar_asli(soup):
    if soup:
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
    return f"{BASE_URL}/media/og-default.jpg"

# --- FUNGSI: REWRITE PAKE GROQ ---
def rewrite_with_groq(title, link, media):
    konten_asli, soup = ambil_konten_berita(link)
    if not GROQ_API_KEY or not konten_asli or len(konten_asli) < 150:
        return format_ke_html(f"Baca selengkapnya di {media}"), soup, title, ""

    try:
        prompt = f"""Kamu adalah Editor Senior PULNEW.com. Tugasmu PARAFRASE TOTAL berita agar lolos plagiarisme.
        PERATURAN SANGAT KETAT:
        1. PANJANG WAJIB SAMA: Hasil rewrite harus sepanjang atau LEBIH PANJANG dari teks sumber. JANGAN DIRINGKAS. Tulis semua detail, data, kutipan.
        2. STRUKTUR: WAJIB ada 2 SUB JUDUL pakai tag <h2>. Taruh di 1/3 dan 2/3 artikel.
        3. WARNA: Setiap <h2> WAJIB dikasih style: <h2 style="color:#0056b3; margin-top:16px; margin-bottom:12px; font-size:22px;">Judul</h2>
        4. DILARANG KERAS COPAS: Semua kalimat WAJIB ditulis ulang 100% dengan struktur dan diksi berbeda.
        5. ACAK URUTAN: Pindahkan paragraf. Gabung dan pecah kalimat.
        6. FAKTA WAJIB SAMA: Nama, angka, tanggal, tempat, kutipan langsung TIDAK BOLEH BERUBAH.
        7. GAYA: Seperti Detik/Kompas. Piramida terbalik. Bahasa baku.
        8. OUTPUT: Kembalikan HANYA JSON valid: {{"judul": "...", "isi": "...", "lead": "..."}}

        TEKS SUMBER:
        Judul: {title}
        Isi: {konten_asli[:8000]}
        Sumber: {link}
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=3000, # <--- NAIKIN DARI 1200 JADI 3000
            response_format={"type": "json_object"}
        )

        hasil_json = json.loads(completion.choices[0].message.content)

        judul_baru = hasil_json.get('judul', title)
        isi_baru = format_ke_html(hasil_json.get('isi', konten_asli))
        lead_baru = hasil_json.get('lead', '')

        print(f"Asli: {len(konten_asli)} char -> Rewrite: {len(hasil_json.get('isi',''))} char") # debug panjang
        return isi_baru, soup, judul_baru, lead_baru

    except Exception as e:
        print(f"Error Groq: {e}")
        return format_ke_html(konten_asli), soup, title, ""
        
# --- FUNGSI: GENERATE HALAMAN HTML DARI JSON ---
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
<p class="source">Sumber: <a href="{article.get('source_url','#')}">{article.get('source_name','')}</a></p>
</div>
</body>
</html>"""
    with open(f"public/berita/{article['slug']}.html", 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    semua_post = get_existing_posts()
    jumlah_baru = 0
    jumlah_update = 0
    total_proses = 0
    BATAS_BERITA_BARU = 5

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

                body, soup_artikel, judul_baru, lead_baru = rewrite_with_groq(title, link, sumber['media'])
                slug= buat_slug(judul_baru)
                img_url = ambil_gambar_asli(soup_artikel)

                berita_data = {
                    "title": judul_baru, "slug": slug, "lead": lead_baru, "kategori": "Berita",
                    "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                    "image": img_url, "body": body,
                    "source_name": get_nama_media(link), "source_url": link
                }

                if slug in semua_post: jumlah_update += 1
                else: jumlah_baru += 1

                semua_post[slug] = berita_data
                save_berita(berita_data)
                total_proses += 1
                time.sleep(10)
        except Exception as e:
            print(f"Error di {sumber['media']}: {e}")

    update_posts_js(semua_post)

    print("=== GENERATE SEMUA HALAMAN HTML ===")
    for slug, article in semua_post.items():
        generate_article_page(article)

    print(f"Selesai! Baru: {jumlah_baru}, Update: {jumlah_update}")

#def hapus_berita_lama():
    #"""Hapus semua file json yg tanggalnya < 2026-07-17"""
    #print("=== MULAI HAPUS BERITA LAMA < 2026-07-17 ===")
    #batas_tanggal = datetime(2026, 7, 17) # <--- TANGGAL PATOKAN
    #count_hapus = 0

    #if os.path.exists(OUTPUT_FOLDER):
        #for filename in os.listdir(OUTPUT_FOLDER):
            #if filename.endswith(".json"):
                #path = os.path.join(OUTPUT_FOLDER, filename)
                #try:
                    #with open(path, 'r', encoding='utf-8') as f:
                        #data = json.load(f)
                    
                    #tgl_berita = datetime.strptime(data['date'][:10], "%Y-%m-%d")
                    
                    #if tgl_berita < batas_tanggal:
                        #os.remove(path) # HAPUS FILE
                        #print(f" -> Dihapus: {data['title']} | {data['date'][:10]}")
                        #count_hapus += 1

                #except Exception as e:
                    #print(f"Gagal hapus {filename}: {e}")
    
    #print(f"=== SELESAI HAPUS: {count_hapus} file dihapus ===")

if __name__ == "__main__":
    #hapus_berita_lama()
    main()

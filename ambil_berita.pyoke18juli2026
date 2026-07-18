import os
import json
import re
import time
import requests
from datetime import datetime
from groq import Groq
from bs4 import BeautifulSoup

# --- KONFIGURASI ---
BASE_URL = "https://pulnew.pages.dev"
OUTPUT_FOLDER = "public/posts" # SESUAI config.yml: folder: "public/posts"
POSTS_JS_PATH = "public/posts.js"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

sumber_rss = [
    {"media": "Kompas", "url": "https://indeks.kompas.com/nasional"},
    {"media": "Antara", "url": "https://www.antaranews.com/rss/tekno"},
    {"media": "CNBC", "url": "https://www.cnbcindonesia.com/techno/rss"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
    {"media": "Pikiran Rakyat", "url": "https://www.pikiran-rakyat.com/feed"},
    {"media": "Tribunnews", "url": "https://www.tribunnews.com/rss"},
    {"media": "Okezone", "url": "https://sindonews.com/rss"}
]

# --- PROMPT GAYA PULNEW ---
def prompt_rewrite_umum(title, konten_asli, link, media):
    return f"""
    Kamu adalah Editor Senior PULNEW.com. Tugasmu: Tulis ulang berita ini jadi artikel 450-500 kata.
    ATURAN:
    1. Bahasa Indonesia formal, padat, kredibel. Gunakan tag <p> dan <h2> untuk 3 subjudul.
    2. Parafrase 100%. Jangan copy paste.
    3. Akhiri dengan: <p><i>Sumber: {media}</i></p>
    JUDUL ASLI: {title}
    KONTEN ASLI: {konten_asli[:4000]}
    """

# --- FUNGSI BARU: BIKIN SLUG BERSIH ---
def buat_slug(judul):
    slug = re.sub(r'[^\w\s-]', '', judul.lower()).strip()
    slug = re.sub(r'\s+', '-', slug)
    slug = slug.strip('-')[:80] # max 80 karakter
    return slug if slug else f"berita-{int(time.time())}"

# --- FUNGSI: BACA SEMUA FILE YG ADA ---
def get_existing_posts():
    """Baca semua file json yg ada dan return dict {slug: data}"""
    posts = {}
    if os.path.exists(OUTPUT_FOLDER):
        for filename in os.listdir(OUTPUT_FOLDER):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(OUTPUT_FOLDER, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        posts[data['slug']] = data
                except: pass
    return posts

# --- FUNGSI: SIMPAN + TIMPA ---
def save_berita(data):
    """Simpan 1 berita = 1 file json. Kalau slug sama, ditimpa"""
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # KUNCI: NAMA FILE CUMA DARI SLUG. GAK PAKE TANGGAL LAGI
    nama_file = f"{data['slug']}.json"
    path_file = os.path.join(OUTPUT_FOLDER, nama_file)

    with open(path_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Disimpan/Ditimpa: {nama_file}")

# --- FUNGSI: UPDATE posts.js ---
def update_posts_js(all_posts):
    """Buat posts.js dari semua file yg ada di folder"""
    urls = [f"/posts/{slug}.json" for slug in all_posts.keys()]
    # Urutkan dari tanggal terbaru
    urls.sort(key=lambda x: all_posts[x.split('/')[-1].replace('.json','')].get('date',''), reverse=True)

    with open(POSTS_JS_PATH, 'w', encoding='utf-8') as f:
        json.dump(urls, f)
    print(f"✅ posts.js diupdate. Total {len(urls)} berita")

def ambil_konten_berita(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for s in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
                s.decompose()
            target = soup.find('article') or soup.find('div', class_=re.compile('content|body|detail'))
            text = target.get_text(separator=' ', strip=True) if target else soup.get_text(separator=' ', strip=True)
            return text[:8000], soup
        return "", None
    except:
        return "", None

def ambil_gambar_asli(soup):
    if soup:
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
    return f"{BASE_URL}/media/og-default.jpg"

def rewrite_with_groq(title, link, media):
    konten_asli, soup = ambil_konten_berita(link)
    if not GROQ_API_KEY or not konten_asli or len(konten_asli) < 150:
        return f"<p>Baca selengkapnya di <a href='{link}'>{media}</a></p>", soup

    try:
        prompt = prompt_rewrite_umum(title, konten_asli, link, media)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )
        return completion.choices[0].message.content, soup
    except Exception as e:
        print(f"Error Groq: {e}")
        return f"<p>{konten_asli[:500]}...</p>", soup

# --- EKSEKUSI UTAMA ---
def main():
    semua_post = get_existing_posts() # Baca file lama
    jumlah_baru = 0
    jumlah_update = 0

    for sumber in sumber_rss:
        print(f"Mengakses {sumber['media']}...")
        try:
            response = requests.get(sumber['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            soup = BeautifulSoup(response.content, 'xml')
            for item in soup.find_all('item')[:5]:
                title = item.find('title').get_text(strip=True)
                link = item.find('link').get_text(strip=True)
                slug = buat_slug(title)

                body, soup_artikel = rewrite_with_groq(title, link, sumber['media'])
                img_url = ambil_gambar_asli(soup_artikel)

                berita_data = {
                    "title": title,
                    "slug": slug,
                    "kategori": "Berita",
                    "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"), # Update tanggal tiap kali di-scrape
                    "image": img_url,
                    "body": body
                }

                if slug in semua_post:
                    jumlah_update += 1
                    print(f" -> Update: {title}")
                else:
                    jumlah_baru += 1
                    print(f" -> Baru: {title}")

                semua_post[slug] = berita_data # Timpa atau tambah
                save_berita(berita_data)
                time.sleep(15) # jeda groq

                if jumlah_baru + jumlah_update >= 10: break
        except Exception as e:
            print(f"Error di {sumber['media']}: {e}")
        if jumlah_baru + jumlah_update >= 10: break

    # STEP PALING PENTING: REGENERATE posts.js DARI SEMUA FILE YG ADA
    update_posts_js(semua_post)
    print(f"Selesai! Baru: {jumlah_baru}, Update: {jumlah_update}")

if __name__ == "__main__":
    main()

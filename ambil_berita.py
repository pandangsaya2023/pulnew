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

# --- FUNGSI ---
def get_existing_slugs():
    """Baca semua slug yg udah ada di public/posts biar gak duplikat"""
    slugs = set()
    if os.path.exists(OUTPUT_FOLDER):
        for filename in os.listdir(OUTPUT_FOLDER):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(OUTPUT_FOLDER, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        slugs.add(data.get('slug'))
                except: pass
    return slugs

def save_berita(data):
    """Simpan 1 berita = 1 file json ke public/posts/"""
    os.makedirs(OUTPUT_FOLDER, exist_ok=True) # FIX KUTIP
    
    # Bikin nama file: 2025-10-04-judul-berita.json
    tanggal = datetime.now().strftime("%Y-%m-%d")
    nama_file = f"{tanggal}-{data['slug']}.json"
    path_file = os.path.join(OUTPUT_FOLDER, nama_file)
    
    with open(path_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Disimpan: {nama_file}")

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
    slug_tercatat = get_existing_slugs() # Cek file lama
    jumlah_baru = 0

    for sumber in sumber_rss:
        print(f"Mengakses {sumber['media']}...")
        try:
            response = requests.get(sumber['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            soup = BeautifulSoup(response.content, 'xml')
            for item in soup.find_all('item')[:5]:
                title = item.find('title').get_text(strip=True)
                link = item.find('link').get_text(strip=True)

                slug = re.sub(r'[^\w\s-]', '', title.lower()).strip()
                slug = re.sub(r'\s+', '-', slug)
                slug = slug.strip('-')

                # slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60]# 
                if not slug: slug = f"berita-{int(time.time())}"

                if slug not in slug_tercatat:
                    print(f" -> Memproses: {title}")
                    body, soup_artikel = rewrite_with_groq(title, link, sumber['media'])
                    img_url = ambil_gambar_asli(soup_artikel)
                    
                    # FORMAT INI 100% SAMA DENGAN fields DI config.yml
                    berita_baru = {
                        "title": title,
                        "slug": slug,
                        "kategori": "Berita", # HURUF BESAR K SESUAI config.yml baris 20
                        "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"), # ISO format
                        "image": img_url,
                        "body": body
                    }
                    save_berita(berita_baru)
                    slug_tercatat.add(slug)
                    jumlah_baru += 1
                    time.sleep(15) # jeda groq
                if jumlah_baru >= 10: break
        except Exception as e:
            print(f"Error di {sumber['media']}: {e}")
        if jumlah_baru >= 10: break

    print(f"Selesai! Nambah {jumlah_baru} Berita Baru ke {OUTPUT_FOLDER}/")

if __name__ == "__main__":
    main()

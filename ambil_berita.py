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
FILE_JSON = "data/posts.json" # PENTING: INI FILE UTAMA
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
    Kamu adalah Editor Senior PULNEW.com. Kamu profesional, analitis, dan punya wawasan luas di semua bidang.
    Tugasmu: Tulis ulang berita ini jadi artikel 500 kata dengan standar media nasional.

    ATURAN PENULISAN:
    1. Bahasa: Indonesia formal tapi mengalir. Tajam, padat, kredibel. Tanpa bahasa lebay.
    2. Panjang: 450-500 kata. Gunakan tag <p> untuk paragraf dan <h2> untuk 3 subjudul.
    3. Struktur:
       - Paragraf 1: Lead kuat, langsung ke inti berita + kenapa ini penting
       - Isi: Bedah fakta + data + konteks
       - Analisis: Berikan sudut pandang "Apa dampaknya bagi masyarakat/Indonesia"
       - Penutup: Outlook ke depan
    4. Gaya: Parafrase 100%. Jangan copy paste. Sesuaikan gaya bahasa dengan topik beritanya.
       Kalau berita ekonomi = gaya bisnis. Kalau bola = gaya sport. Kalau politik = gaya tajam.
    5. Tambahkan insight 1-2 kalimat hasil analisis kamu di setiap subjudul <h2>.
    6. Akhiri dengan: <p><i>Sumber: {media}</i></p>

    JUDUL ASLI: {title}
    KONTEN ASLI: {konten_asli}
    """

# --- FUNGSI ---
def load_data():
    """Baca data lama biar gak ketimpa"""
    if os.path.exists(FILE_JSON):
        with open(FILE_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"posts": []}

def save_data(data):
    """Simpan ke data/posts.json"""
    os.makedirs('data', exist_ok=True)
    with open(FILE_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Data disimpan ke {FILE_JSON}. Total berita: {len(data['posts'])}")

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

def ambil_gambar_asli(soup, url):
    if soup:
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
    return f"{BASE_URL}/media/og-default.jpg" # disamain sama index.html

def rewrite_with_groq(title, link, media):
    konten_asli, soup = ambil_konten_berita(link)
    if not GROQ_API_KEY or not konten_asli or len(konten_asli) < 150:
        return f"<p>Berita selengkapnya bisa dibaca di <a href='{link}'>{media}</a></p>", soup

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
    data = load_data()
    slug_tercatat = {p['slug'] for p in data['posts']} # Cek dari data lama
    jumlah_baru = 0

    for sumber in sumber_rss:
        print(f"Mengakses {sumber['media']}...")
        try:
            response = requests.get(sumber['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            soup = BeautifulSoup(response.content, 'xml')
            for item in soup.find_all('item')[:5]:
                title = item.find('title').get_text(strip=True)
                link = item.find('link').get_text(strip=True)

                slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]
                if not slug:
                    slug = f"berita-{int(time.time() * 1000)}"

                if slug not in slug_tercatat:
                    print(f" -> Memproses: {title}")
                    body, soup_artikel = rewrite_with_groq(title, link, sumber['media'])
                    img_url = ambil_gambar_asli(soup_artikel, link)
                    deskripsi = BeautifulSoup(body, 'html.parser').get_text()[:160] + "..."

                    # FORMAT INI HARUS SAMA DENGAN SVELTIA
                    berita_baru = {
                        "title": title,
                        "slug": slug,
                        "kategori": "NASIONAL", # Default. Nanti bisa di AI-kan
                        "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"), # Format ISO buat sort
                        "image": img_url,
                        "body": body
                    }

                    data['posts'].insert(0, berita_baru) # Masukkan ke paling atas
                    slug_tercatat.add(slug)
                    jumlah_baru += 1
                    time.sleep(15) # jeda biar gak kena limit groq
                if jumlah_baru >= 10:
                    break
        except Exception as e:
            print(f"Error di {sumber['media']}: {e}")
        if jumlah_baru >= 10:
            break

    if jumlah_baru > 0:
        save_data(data)

    print(f"Selesai! Nambah {jumlah_baru} Berita Baru")

if __name__ == "__main__":
    main()

import os
import json
import re
import time
import requests
import random
from datetime import datetime
from urllib.parse import urlparse
from groq import Groq
from bs4 import BeautifulSoup

# --- KONFIGURASI ---
BASE_URL = "https://pulnew.pages.dev"
OUTPUT_FOLDER = "public/posts"
POSTS_JS_PATH = "public/posts.js"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AUTHOR_NAME = "Tim Redaksi PULNEW" # <--- TAMBAH AUTHOR
client = Groq(api_key=GROQ_API_KEY)
MAX_BERITA_PER_RUN = 10 # <--- JANGAN TERLALU BANYAK. 5-10 cukup
MIN_WORDS = 500 # <--- MINIMAL 500 KATA BUAT ADSENSE

sumber_rss = [
    {"media": "Kompas", "url": "https://indeks.kompas.com/nasional"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
    {"media": "Sindonews", "url": "https://sindonews.com/rss"}
]

# --- FUNGSI BARU: TAMBAH KONTEKS LOKAL ---
def tambah_konteks_lokal(title, body_html):
    konteks = [
        f"<h2>Dampak di Indonesia</h2><p>Peristiwa ini juga menjadi sorotan di Indonesia. Masyarakat diharapkan tetap memantau perkembangan resmi dari pemerintah.</p>",
        f"<h2>Tanggapan Publik</h2><p>Di media sosial, isu ini memicu beragam komentar dari warganet. PULNEW akan terus update informasi terbarunya.</p>",
        f"<h2>Apa Kata Ahli?</h2><p>Menurut pengamat, kejadian ini perlu disikapi dengan bijak agar tidak menimbulkan kepanikan.</p>"
    ]
    return body_html + random.choice(konteks) # <--- Tambah 1 paragraf opini/konteks

# --- FUNGSI BARU: BIKIN FAQ OTOMATIS ---
def tambah_faq(title):
    return f"""
    <h2>FAQ</h2>
    <p><b>T: Apa yang terjadi terkait {title}?</b><br>
    J: Ringkasnya, peristiwa tersebut sedang menjadi perhatian publik dan masih terus berkembang.</p>
    <p><b>T: Dari mana sumber informasi ini?</b><br>
    J: Informasi dihimpun dari berbagai media nasional dan diolah ulang oleh Tim Redaksi PULNEW.</p>
    """

def get_nama_media(url):
    try:
        domain = urlparse(url).netloc.replace('www.', '')
        if 'kompas' in domain: return 'Kompas'
        if 'republika' in domain: return 'Republika'
        if 'sindonews' in domain: return 'Sindonews'
        return domain.split('.')[0].capitalize()
    except:
        return "Media Nasional"

def format_ke_html(teks):
    teks = str(teks).strip()
    if '<p>' in teks:
        return teks
    paragraf = [p.strip() for p in re.split(r'\n\n+', teks) if p.strip()]
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
                    posts[data['slug']] = data
                except: pass
    return posts

# --- PROMPT UPGRADE: LEBIH PANJANG + STRUKTUR ---
def prompt_rewrite_adsense(title, konten_asli, media):
    return f"""
    Kamu adalah Editor Senior PULNEW.com dan Jurnalis Profesional.
    Tugasmu: Tulis ulang berita ini menjadi artikel ORIGINAL 500-600 kata yang lolos Google Adsense.

    ATURAN KETAT:
    1. Bahasa Indonesia formal, padat, netral, kredibel. Gaya penulisan manusia.
    2. Struktur WAJIB: Paragraf Pembuka 3 kalimat. Lalu <h2>Subjudul 1</h2> 2 paragraf. <h2>Subjudul 2</h2> 2 paragraf. Lalu <h2>Kesimpulan</h2> 1 paragraf.
    3. Parafrase 100%. Jangan copy 1 kalimat pun. Gunakan sinonim dan ubah struktur.
    4. Tambahkan 1-2 kalimat analisis/konteks di setiap paragraf. Jangan hanya fakta.
    5. Gunakan tag HTML: <p> untuk paragraf dan <h2> untuk subjudul.
    6. JANGAN TULIS "Sumber:..." di dalam body. Kita taruh di metadata.

    JUDUL ASLI: {title}
    KONTEN ASLI DARI {media}: {konten_asli[:4000]}
    """

def buat_slug(judul):
    slug = re.sub(r'[^\w\s-]', '', judul.lower()).strip()
    slug = re.sub(r'\s+', '-', slug)
    return slug.strip('-')[:80] if slug else f"berita-{int(time.time())}"

def save_berita(data):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    nama_file = f"{data['slug']}.json"
    path_file = os.path.join(OUTPUT_FOLDER, nama_file)
    with open(path_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Disimpan: {nama_file} | {len(data['body'].split())} kata")

def update_posts_js(all_posts):
    urls = [f"/posts/{slug}.json" for slug in all_posts.keys()]
    urls.sort(key=lambda x: all_posts[x.split('/')[-1].replace('.json','')].get('date',''), reverse=True)
    with open(POSTS_JS_PATH, 'w', encoding='utf-8') as f:
        json.dump(urls, f)

def ambil_konten_berita(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for s in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "comment"]):
                s.decompose()
            target = soup.find('article') or soup.find('div', class_=re.compile('content|body|detail|post'))
            text = target.get_text(separator='\n\n', strip=True) if target else ""
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

def rewrite_with_groq(title, link, media):
    konten_asli, soup = ambil_konten_berita(link)
    if not GROQ_API_KEY or not konten_asli or len(konten_asli) < 200:
        return "<p>Konten gagal dimuat. Silakan kunjungi sumber asli.</p>", soup

    try:
        prompt = prompt_rewrite_adsense(title, konten_asli, media)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8, # <--- Agak kreatif biar gak kaku
            max_tokens=1200 # <--- Naikin biar bisa 600 kata
        )
        hasil = completion.choices[0].message.content

        # BERSIHIN OUTPUT AI
        hasil = hasil.replace('**', '').replace('###', '<h2>').replace('##', '<h2>')

        # TAMBAH NILAI: KONTEKS + FAQ
        hasil_final = tambah_konteks_lokal(title, hasil)
        hasil_final = hasil_final + tambah_faq(title)

        return hasil_final, soup
    except Exception as e:
        print(f"Error Groq: {e}")
        return f"<p>{konten_asli[:500]}...</p>", soup

# --- EKSEKUSI UTAMA ---
def main():
    semua_post = get_existing_posts()
    jumlah_baru = 0
    BATAS_BERITA_BARU = 5 # <--- MAX 5 BERITA BARU PER HARI. Biar keliatan natural

    print(f"Target: Maks {BATAS_BERITA_BARU} berita baru per run")

    for sumber in sumber_rss:
        print(f"Mengakses {sumber['media']}...")
        try:
            response = requests.get(sumber['url'], headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.content, 'xml')

            for item in soup.find_all('item')[:2]: # <--- Ambil 2 aja per media
                if jumlah_baru >= BATAS_BERITA_BARU: break

                title = item.find('title').get_text(strip=True)
                link = item.find('link').get_text(strip=True)
                slug = buat_slug(title)

                if slug in semua_post:
                    print(f" -> Skip: Sudah ada. {title}")
                    continue

                body, soup_artikel = rewrite_with_groq(title, link, sumber['media'])
                img_url = ambil_gambar_asli(soup_artikel)
                word_count = len(re.sub('<[^<]+?>', '', body).split())

                if word_count < MIN_WORDS: # <--- CEK PANJANG
                    print(f" -> Skip: Artikel terlalu pendek {word_count} kata. {title}")
                    continue

                berita_data = {
                    "title": title,
                    "slug": slug,
                    "kategori": "Berita Nasional", # <--- KATEGORI SPESIFIK
                    "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                    "image": img_url,
                    "body": body,
                    "author": AUTHOR_NAME, # <--- TAMBAH AUTHOR
                    "source_name": get_nama_media(link),
                    "source_url": link,
                    "word_count": word_count # <--- BUAT TRACKING
                }

                jumlah_baru += 1
                print(f" -> Baru: {title} [{word_count} kata]")
                semua_post[slug] = berita_data
                save_berita(berita_data)
                time.sleep(random.randint(20, 40)) # <--- JEDA ACAK 20-40 detik biar natural

        except Exception as e:
            print(f"Error di {sumber['media']}: {e}")

    update_posts_js(semua_post)
    print(f"Selesai! Berita Baru: {jumlah_baru}")

if __name__ == "__main__":
    main()

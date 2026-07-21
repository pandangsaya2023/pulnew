import os
import json
import re
import time
import requests
from datetime import datetime
from urllib.parse import urlparse # <--- TAMBAH INI
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
    {"media": "Antara", "url": "https://www.antaranews.com/rss/tekno"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
    {"media": "Okezone", "url": "https://sindonews.com/rss"}
]

# --- FUNGSI BARU: AMBIL NAMA MEDIA DARI URL ---
def get_nama_media(url):
    try:
        domain = urlparse(url).netloc.replace('www.', '')
        nama = domain.split('.')[0].capitalize()
        if 'kompas' in domain: return 'Kompas'
        if 'antara' in domain: return 'Antara'
        if 'republika' in domain: return 'Republika'  
        if 'sindonews' in domain: return 'Sindonews'
        return nama
    except:
        return "Media"

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

# --- PROMPT GAYA PULNEW ---
def prompt_rewrite_umum(title, konten_asli, link):
    # HAPUS {media} dan {link} dari prompt biar AI gak nulis sumber
    return f"""
    Kamu adalah Editor Senior PULNEW.com. Tugasmu: Tulis ulang berita ini jadi artikel 350-400 kata.
    ATURAN:
    1. Bahasa Indonesia formal, padat, kredibel.
    2. Buat 3 paragraf.
    3. Gunakan tag <p> untuk paragrap dan juga untuk 2 subjudul.
    2. Parafrase 100%. Jangan copy paste.
    3. JANGAN TULIS SUMBER ATAU LINK DI AKHIR.
    JUDUL ASLI: {title}
    KONTEN ASLI: {konten_asli[:3000]}
    """

# --- FUNGSI: BIKIN SLUG BERSIH ---
def buat_slug(judul):
    slug = re.sub(r'[^\w\s-]', '', judul.lower()).strip()
    slug = re.sub(r'\s+', '-', slug)
    slug = slug.strip('-')[:80]
    return slug if slug else f"berita-{int(time.time())}"

# --- FUNGSI: SIMPAN + TIMPA ---
def save_berita(data):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    nama_file = f"{data['slug']}.json"
    path_file = os.path.join(OUTPUT_FOLDER, nama_file)
    with open(path_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Disimpan/Ditimpa: {nama_file}")

# --- FUNGSI: UPDATE posts.js ---
def update_posts_js(all_posts):
    urls = [f"/posts/{slug}.json" for slug in all_posts.keys()]
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
            text = target.get_text(separator='\n\n', strip=True) if target else soup.get_text(separator='\n\n', strip=True)
            return text[:6000], soup
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
        return format_ke_html(f"Baca selengkapnya di {media}"), soup

    try:
        prompt = prompt_rewrite_umum(title, konten_asli, link)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=900
        )
        hasil = completion.choices[0].message.content

        # INI KUNCINYA: PISAHIN H2 DAN P BIAR GAK KEBUNGKUS
        blok = [b.strip() for b in hasil.split('\n\n') if b.strip()]
        hasil_html = ''
        for b in blok:
            b = b.replace('<p></p>', '')
            if b.startswith('<h2>'): # kalau udah h2 jangan dibungkus p lagi
                hasil_html += b
            else:
                hasil_html += f"<p>{b}</p>"

        return hasil_html, soup
    except Exception as e:
        print(f"Error Groq: {e}")
        return f"<p>{konten_asli[:500]}...</p>", soup

# --- EKSEKUSI UTAMA ---
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
                    "source_name": get_nama_media(link), # <--- TAMBAH
                    "source_url": link # <--- TAMBAH
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
    print(f"Selesai! Baru: {jumlah_baru}, Update: {jumlah_update}, Total diproses: {total_proses}")

#def repair_all_old_posts():
    #"""Paksa benerin semua file json lama TAPI SLUG TETAP"""
    #print("=== MULAI REPAIR SEMUA BERITA LAMA ===")
    #count = 0
    #if os.path.exists(OUTPUT_FOLDER):
        #for filename in os.listdir(OUTPUT_FOLDER):
            #if filename.endswith(".json"):
                #path = os.path.join(OUTPUT_FOLDER, filename)
                #try:
                    #with open(path, 'r', encoding='utf-8') as f:
                        #data = json.load(f)
                    
                    #slug_lama = data.get('slug') # SIMPAN SLUG LAMA

                    # Kalau belum ada <p> berarti masih rusak
                    #if '<p>' not in data.get('body',''):
                        #print(f" -> Repair: {data['title']}")
                        #data['body'] = format_ke_html(data['body'])
                        #data['slug'] = slug_lama # PAKSA BALIKIN SLUG LAMA
                        
                        #with open(path, 'w', encoding='utf-8') as f:
                            #json.dump(data, f, ensure_ascii=False, indent=2)
                        #$count += 1
                #except Exception as e:
                    #print(f"Gagal repair {filename}: {e}")
    #print(f"=== SELESAI REPAIR: {count} file dibenerin ===")

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
    # hapus_berita_lama()
    # repair_all_old_posts()
    main()

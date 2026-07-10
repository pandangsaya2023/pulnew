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
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

sumber_rss = [
    {"media": "Kompas", "url": "https://indeks.kompas.com/teknologi"},
    {"media": "Detik", "url": "https://rss.detik.com/index.php/detikinet"},
    {"media": "Antara", "url": "https://www.antaranews.com/rss/tekno"},
    {"media": "CNBC", "url": "https://www.cnbcindonesia.com/techno/rss"},
    {"media": "Pikiran Rakyat", "url": "https://www.pikiran-rakyat.com/rss/teknologi"},
    {"media": "Tribunnews", "url": "https://www.tribunnews.com/rss/techno"},
    {"media": "Okezone", "url": "https://techno.okezone.com/rss"}
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
    # if soup:
       # og_image = soup.find('meta', property='og:image')
        # if og_image and og_image.get('content'):
           # return og_image['content']
    return f"{BASE_URL}/images/og-default.jpg"

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

def bikin_html_statis(slug, title, img_url, deskripsi):
    folder_output = 'public/berita'
    os.makedirs(folder_output, exist_ok=True)
    link_statis = f"{BASE_URL}/berita/{slug}.html"
    img_url = img_url if img_url else f"{BASE_URL}/images/og-default.jpg"
    link_wa = f"https://wa.me/?text=Baca%20berita%20ini:%20{link_statis}"

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="description" content="{deskripsi}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{deskripsi}">
    <meta property="og:image" content="{img_url}">
    <meta property="og:url" content="{link_statis}">
    <meta property="og:type" content="article">
    <title>{title} - PULNEW.com</title>
</head>
<body style="font-family:sans-serif; text-align:center; padding:50px; background:#f4f4f4;">
    <div style="background:white; padding:30px; border-radius:15px; max-width:500px; margin:auto; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
        <h3 style="color:#333;">{title}</h3>
        <p style="color:#666;">{deskripsi}</p>
        <a href="{BASE_URL}/berita.html?slug={slug}" style="display:block; margin:20px 0; padding:15px; background:#d32f2f; color:white; text-decoration:none; border-radius:10px; font-weight:bold;">Baca Berita Lengkap</a>
        <a href="{link_wa}" style="display:block; margin:20px 0; padding:15px; background:#25D366; color:white; text-decoration:none; border-radius:10px; font-weight:bold;">📲 Share ke WhatsApp</a>
    </div>
</body>
</html>"""
    with open(f"{folder_output}/{slug}.html", "w", encoding="utf-8") as f:
        f.write(html)

# --- EKSEKUSI ---
os.makedirs('public/posts', exist_ok=True)
slug_tercatat = {f.replace('.json', '') for f in os.listdir('public/posts') if f.endswith('.json')}
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
                # img_url = img_url if img_url else f"{BASE_URL}/images/og-default.jpg"
                img_url = ambil_gambar_asli(soup_artikel, link)
                deskripsi = BeautifulSoup(body, 'html.parser').get_text()[:160] + "..."

                berita = {
                    "slug": slug,
                    "title": title,
                    "meta_description": deskripsi,
                    "content": deskripsi,
                    "body": body,
                    "image": "",
                    "kategori": "BERITA",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "source": sumber['media']
                }

                with open(f'public/posts/{slug}.json', 'w', encoding='utf-8') as f:
                    json.dump(berita, f, indent=2, ensure_ascii=False)

                bikin_html_statis(slug, title, img_url, deskripsi)
                slug_tercatat.add(slug)
                jumlah_baru += 1
                time.sleep(15)
            if jumlah_baru >= 10:
                break
    except Exception as e:
        print(f"Error: {e}")
    if jumlah_baru >= 10:
        break

print(f"Selesai! Nambah {jumlah_baru} Berita Baru")

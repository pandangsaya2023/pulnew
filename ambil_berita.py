import urllib.request
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import os
import random
import google.generativeai as genai

def rewrite_with_gemini(title, link):
    """Fungsi resmi menggunakan SDK Google Generative AI"""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("GEMINI_API_KEY belum diset di GitHub Secrets")
        return f"Baca selengkapnya di {link}"

    try:
        # Konfigurasi API Key secara resmi lewat SDK
        genai.configure(api_key=api_key)
        
        # Memanggil model gemini-1.5-flash standar
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""Buat artikel 300 kata bahasa Indonesia dengan judul: "{title}"
Tulis ulang pakai gaya jurnalistik, jangan copy.
Akhiri dengan: Berita selengkapnya bisa dibaca di {link}"""

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error SDK Gemini: {e}")
        return f"Baca selengkapnya di {link}"

# Database Media Nasional Campuran
sumber_rss = [
    {"media": "Detikcom", "url": "https://rss.detik.com/index.php/detikcom"},
    {"media": "Kompas", "url": "https://nasional.kompas.com/rss/index.xml"},
    {"media": "Tempo", "url": "https://rss.tempo.co/nasional"},
    {"media": "CNN Indonesia", "url": "https://www.cnnindonesia.com/nasional/rss"},
    {"media": "Liputan6", "url": "https://www.liputan6.com/rss"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
    {"media": "Okezone", "url": "https://sindonews.com/rss"},
    {"media": "Tribunnews", "url": "https://www.tribunnews.com/rss"},
    {"media": "Suara", "url": "https://www.suara.com/rss/news"},
    {"media": "Bisnis.com", "url": "https://www.bisnis.com/rss"}
]

# Jalur file utama website Anda
path_json = "posts.json"

def buat_slug(judul):
    judul = judul.lower()
    judul = re.sub(r'[^a-z0-9\s-]', '', judul)
    judul = re.sub(r'[\s-]+', '-', judul).strip('-')
    return judul[:60]

def deteksi_kategori_otomatis(judul):
    j = judul.lower()

    ekonomi_keywords = ['ekonomi', 'saham', 'rupiah', 'dolar', 'bisnis', 'keuangan', 'pasar', 'investasi', 'komoditas', 'umkm', 'anggaran', 'inflasi', 'pajak', 'tarif']
    teknologi_keywords = ['teknologi', 'gadget', 'hp', 'smartphone', 'ai', 'kecerdasan buatan', 'aplikasi', 'cyber', 'hacker', 'android', 'ios', 'internet', 'sains', 'robot']
    olahraga_keywords = ['olahraga', 'sepakbola', 'bola', 'timnas', 'liga', 'bulutangkis', 'badminton', 'motogp', 'f1', 'atlet', 'juara', 'bertanding', 'match', 'piala']
    hiburan_keywords = ['hiburan', 'artis', 'seleb', 'film', 'sinopsis', 'musik', 'konser', 'aktor', 'gosip', 'drama', 'budaya', 'wisata', 'kuliner', 'game', 'gaming']
    politik_keywords = ['politik', 'dpr', 'presiden', 'mentri', 'menteri', 'pilkada', 'pemilu', 'kpk', 'sidang', 'partai', 'gub', 'gubernur', 'bupati', 'walikota', 'korupsi', 'uu']

    if any(x in j for x in ekonomi_keywords):
        return "Ekonomi"
    elif any(x in j for x in teknologi_keywords):
        return "Teknologi"
    elif any(x in j for x in olahraga_keywords):
        return "Olahraga"
    elif any(x in j for x in hiburan_keywords):
        return "Hiburan"
    else:
        return "Politik"

# Memuat timbunan berita lama
if os.path.exists(path_json):
    try:
        with open(path_json, 'r', encoding='utf-8') as f:
            data_lama = json.load(f)
            if isinstance(data_lama, dict):
                daftar_berita = data_lama.get("posts", [])
            else:
                daftar_berita = data_lama
    except Exception:
        daftar_berita = []
else:
    daftar_berita = []

slug_tercatat = {b["slug"] for b in daftar_berita if "slug" in b}
berita_baru_semua_media = []

# Proses penarikan data RSS feed dari 10 portal berita
for sumber in sumber_rss:
    nama_media = sumber["media"]
    url = sumber["url"]
    print(f"Mengambil berita dari {nama_media}...")

    try:
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=15)
        xml_data = response.read()
        root = ET.fromstring(xml_data)

        hitung = 0
        for item in root.findall('.//item'):
            if hitung >= 3:
                break

            title_node = item.find('title')
            link_node = item.find('link')

            if title_node is None or link_node is None:
                continue

            title = title_node.text.strip()
            link = link_node.text.strip()
            slug = buat_slug(title)

            if slug in slug_tercatat:
                continue

            image_url = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600"
            enclosure = item.find('enclosure')
            if enclosure is not None and 'url' in enclosure.attrib:
                image_url = enclosure.attrib['url']
            else:
                media_content = item.find('{http://search.yahoo.com/mrss/}content')
                if media_content is not None and 'url' in media_content.attrib:
                    image_url = media_content.attrib['url']

            kategori_terpilih = deteksi_kategori_otomatis(title)

            print(f" -> Generate artikel pakai SDK Gemini: {title}")
            isi_artikel = rewrite_with_gemini(title, link)

            id_unik = int(datetime.now().strftime("%d%H%M%S")) + random.randint(10, 99)

            struktur_berita = {
                "id": id_unik,
                "title": title,
                "slug": slug,
                "category": kategori_terpilih,
                "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                "image": image_url,
                "body": isi_artikel
            }

            berita_baru_semua_media.append(struktur_berita)
            slug_tercatat.add(slug)
            hitung += 1

    except Exception as e:
        print(f"Media {nama_media} dilewati karena proteksi/Rss off. Detail: {e}")

if berita_baru_semua_media:
    random.shuffle(berita_baru_semua_media)
    daftar_berita = berita_baru_semua_media + daftar_berita
    daftar_berita = daftar_berita[:120]

    # Menjaga pembungkusan objek tetap bernama "posts" agar lolos validasi JavaScript frontend
    with open(path_json, 'w', encoding='utf-8') as f:
        json.dump({"posts": daftar_berita}, f, indent=2, ensure_ascii=False)
    print(f"Sukses! Berhasil menambahkan {len(berita_baru_semua_media)} berita nasional campuran secara proporsional.")
else:
    print("Tidak ada berita baru yang ditarik.")

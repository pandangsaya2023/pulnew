import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import urllib.request
import random
from openai import OpenAI

def rewrite_with_ai(title, link):
    """Fungsi resmi menggunakan OpenAI SDK sesuai standar dokumentasi Groq"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY belum diset di GitHub Secrets")
        return f"Baca selengkapnya di {link}"

    try:
        # Inisialisasi client Groq menggunakan SDK Resmi OpenAI sesuai dokumentasi
        client = OpenAI(
            api_key=api_key.strip(),
            base_url="https://api.groq.com/openai/v1",
        )

        prompt = f'Buat artikel berita sepanjang 300 kata dalam bahasa Indonesia berdasarkan judul ini: "{title}". Tulis ulang menggunakan gaya bahasa jurnalistik yang rapi, profesional, dan jangan menyalin teks asli. Akhiri artikel dengan kalimat persis: "Berita selengkapnya bisa dibaca di {link}"'

        # Pemanggilan model sesuai struktur standar Groq Cloud
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error Koneksi Groq SDK: {e}")
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

path_json = "posts.json"

def buat_slug(judul):
    judul = judul.lower()
    judul = re.sub(r'[^a-z0-9\s-]', '', judul)
    judul = re.sub(r'[\s-]+', '-', judul).strip('-')
    return judul[:60]

def deteksi_kategori_otomatis(judul):
    j = judul.lower()
    if any(x in j for x in ['ekonomi', 'saham', 'rupiah', 'bisnis', 'keuangan']): return "Ekonomi"
    elif any(x in j for x in ['teknologi', 'gadget', 'hp', 'ai', 'aplikasi']): return "Teknologi"
    elif any(x in j for x in ['olahraga', 'sepakbola', 'bola', 'timnas', 'liga']): return "Olahraga"
    elif any(x in j for x in ['hiburan', 'artis', 'film', 'musik', 'gosip']): return "Hiburan"
    else: return "Politik"

# Load database berita lama
if os.path.exists(path_json):
    try:
        with open(path_json, 'r', encoding='utf-8') as f:
            data_lama = json.load(f)
            daftar_berita = data_lama.get("posts", []) if isinstance(data_lama, dict) else data_lama
    except Exception: 
        daftar_berita = []
else: 
    daftar_berita = []

slug_tercatat = {b["slug"] for b in daftar_berita if "slug" in b}
berita_baru_semua_media = []

# Proses penarikan berita
for sumber in sumber_rss:
    nama_media = sumber["media"]
    url = sumber["url"]
    print(f"Mengambil berita dari {nama_media}...")

    try:
        headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            root = ET.fromstring(response.read())

        hitung = 0
        for item in root.findall('.//item'):
            if hitung >= 3: break
            title_node = item.find('title')
            link_node = item.find('link')
            if title_node is None or link_node is None: continue

            title = title_node.text.strip()
            link = link_node.text.strip()
            slug = buat_slug(title)

            if slug in slug_tercatat: continue

            image_url = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600"
            kategori_terpilih = deteksi_kategori_otomatis(title)

            print(f" -> Jalankan Pembuatan Berita AI Resmi SDK: {title}")
            isi_artikel = rewrite_with_ai(title, link)

            id_unik = int(datetime.now().strftime("%d%H%M%S")) + random.randint(10, 99)
            berita_baru_semua_media.append({
                "id": id_unik, 
                "title": title, 
                "slug": slug, 
                "category": kategori_terpilih,
                "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"), 
                "image": image_url, 
                "body": isi_artikel
            })
            slug_tercatat.add(slug)
            hitung += 1
    except Exception as e:
        print(f"Media {nama_media} dilewati. Detail: {e}")

if berita_baru_semua_media:
    random.shuffle(berita_baru_semua_media)
    daftar_berita = berita_baru_semua_media + daftar_berita
    with open(path_json, 'w', encoding='utf-8') as f:
        json.dump({"posts": daftar_berita[:120]}, f, indent=2, ensure_ascii=False)
    print("Sukses Besar Memperbarui Data Berita dengan SDK Resmi!")
else:
    print("Tidak ada berita baru saat ini.")

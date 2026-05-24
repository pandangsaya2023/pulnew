import urllib.request
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import os
import random

# DATABASE RSS TERSELEKSI 2026: Hanya memuat yang 100% aktif, cepat, dan anti-Error
sumber_rss = [
    {"media": "Antara News Top", "url": "https://www.antaranews.com/rss/top-news.xml"},
    {"media": "Antara Olahraga", "url": "https://www.antaranews.com/rss/olahraga.xml"},
    {"media": "Kompas Nasional", "url": "https://nasional.kompas.com/rss/index.xml"},
    {"media": "Republika Utama", "url": "https://www.republika.co.id/rss"},
    {"media": "Republika Senggang", "url": "https://www.republika.co.id/rss/senggang"},
    {"media": "Bisnis.com", "url": "https://www.bisnis.com/rss"},
    {"media": "Tempo Interaktif", "url": "https://www.tempo.co/rss"}
]

path_json = "public/posts.json"

def buat_slug(judul):
    judul = judul.lower()
    judul = re.sub(r'[^a-z0-9\s-]', '', judul)
    judul = re.sub(r'[\s-]+', '-', judul).strip('-')
    return judul[:60]

# MESIN KLASIFIKASI KATEGORI OTOMATIS BERDASARKAN KATA KUNCI JUDUL BERITA
def deteksi_kategori_otomatis(judul):
    j = judul.lower()
    
    ekonomi_keywords = ['ekonomi', 'saham', 'rupiah', 'dolar', 'bisnis', 'keuangan', 'pasar', 'investasi', 'komoditas', 'umkm', 'anggaran', 'inflasi', 'pajak', 'tarif', 'emiten', 'ojk']
    teknologi_keywords = ['teknologi', 'gadget', 'hp', 'smartphone', 'ai', 'kecerdasan buatan', 'aplikasi', 'cyber', 'hacker', 'android', 'ios', 'internet', 'sains', 'robot', 'game', 'gaming']
    olahraga_keywords = ['olahraga', 'sepakbola', 'bola', 'timnas', 'liga', 'bulutangkis', 'badminton', 'motogp', 'f1', 'atlet', 'juara', 'bertanding', 'match', 'piala', 'koni']
    hiburan_keywords = ['hiburan', 'artis', 'seleb', 'film', 'sinopsis', 'musik', 'konser', 'aktor', 'gosip', 'drama', 'budaya', 'wisata', 'kuliner', 'sinema']
    politik_keywords = ['politik', 'dpr', 'presiden', 'mentri', 'menteri', 'pilkada', 'pemilu', 'kpk', 'sidang', 'partai', 'gubernur', 'bupati', 'korupsi', 'uu', 'hukum', 'polri', 'tni']

    if any(x in j for x in ekonomi_keywords):
        return "Ekonomi"
    elif any(x in j for x in teknologi_keywords):
        return "Teknologi"
    elif any(x in j for x in olahraga_keywords):
        return "Olahraga"
    elif any(x in j for x in hiburan_keywords):
        return "Hiburan"
    elif any(x in j for x in politik_keywords):
        return "Politik"
    else:
        # Jika berita umum/internasional, seimbangkan ke Politik (Nasional/Umum di Home)
        return "Politik"

# Load database lama agar tidak menimpa pos manual dari Sveltia CMS
if os.path.exists(path_json):
    try:
        with open(path_json, 'r', encoding='utf-8') as f:
            data_lama = json.load(f)
            daftar_berita = data_lama.get("posts", [])
    except Exception:
        daftar_berita = []
else:
    daftar_berita = []

slug_tercatat = {b["slug"] for b in daftar_berita if "slug" in b}
berita_baru_semua_media = []

# Proses penarikan data secara proporsional
for sumber in sumber_rss:
    nama_media = sumber["media"]
    url = sumber["url"]
    print(f"Membaca feed aman: {nama_media}...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=8)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        # PROPORSIONAL: Ambil maksimal 4 berita teratas dari tiap-tiap media
        hitung = 0
        for item in root.findall('.//item'):
            if hitung >= 4: 
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
            
            # Deteksi gambar cover berita
            image_url = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600"
            enclosure = item.find('enclosure')
            if enclosure is not None and 'url' in enclosure.attrib:
                image_url = enclosure.attrib['url']
            else:
                media_content = item.find('{http://search.yahoo.com/mrss/}content')
                if media_content is not None and 'url' in media_content.attrib:
                    image_url = media_content.attrib['url']
            
            kategori_terpilih = deteksi_kategori_otomatis(title)
            
            struktur_berita = {
                "title": title,
                "slug": slug,
                "category": kategori_terpilih,
                "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                "image": image_url,
                "body": f"Berita terhangat hari ini dilaporkan secara langsung oleh jaringan media {nama_media}. Informasi selengkapnya dan ulasan mendalam mengenai topik ini dapat Anda baca melalui tautan resmi sumber asli berikut: {link}"
            }
            
            berita_baru_semua_media.append(struktur_berita)
            slug_tercatat.add(slug)
            hitung += 1
            
    except Exception as e:
        print(f"Media {nama_media} dilewati sementara. Info: {e}")

if berita_baru_semua_media:
    # Mengacak tumpukan berita baru agar media tidak mengelompok di satu baris website
    random.shuffle(berita_baru_semua_media)
    
    # Satukan di baris teratas bersama dengan data lama kamu
    daftar_berita = berita_baru_semua_media + daftar_berita
    
    # Batasi kapasitas json maksimal 120 agar performa web tetap enteng
    daftar_berita = daftar_berita[:120]
    
    with open(path_json, 'w', encoding='utf-8') as f:
        json.dump({"posts": daftar_berita}, f, indent=2, ensure_ascii=False)
    print(f"Sukses! Berhasil menyuntikkan {len(berita_baru_semua_media)} berita nasional baru secara otomatis.")
else:
    print("Sesi ini dilewati, belum ada berita baru dari server.")


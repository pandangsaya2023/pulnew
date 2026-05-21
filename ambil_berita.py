import urllib.request
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import os

# 1. Daftar RSS Feed Media Daerah (Menggunakan Antara News)
sumber_rss = {
    "Sumatera": "https://www.antaranews.com/rss/sumatra-utara.xml",
    "Jawa": "https://www.antaranews.com/rss/jakarta.xml",
    "Kalimantan": "https://www.antaranews.com/rss/kalimantan-barat.xml",
    "Sulawesi": "https://www.antaranews.com/rss/sulawesi-selatan.xml"
}

path_json = "public/posts.json"

# 2. Fungsi membuat Slug aman dari Judul
def buat_slug(judul):
    judul = judul.lower()
    judul = re.sub(r'[^a-z0-9\s-]', '', judul)
    judul = re.sub(r'[\s-]+', '-', judul).strip('-')
    return judul[:60]

# 3. Ambil data posts.json yang sudah ada agar tidak terhapus
if os.path.exists(path_json):
    try:
        with open(path_json, 'r', encoding='utf-8') as f:
            data_lama = json.load(f)
            daftar_berita = data_lama.get("posts", [])
    except Exception:
        daftar_berita = []
else:
    daftar_berita = []

# Ambil semua slug yang sudah ada agar tidak terjadi duplikasi berita
slug_tercatat = {b["slug"] for b in daftar_berita if "slug" in b}

berita_baru_total = []

# 4. Mulai Scraping dari RSS
for wilayah, url in sumber_rss.items():
    print(f"Mengambil berita untuk wilayah: {wilayah}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=15)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        hitung = 0
        for item in root.findall('.//item'):
            if hitung >= 2: # Ambil 2 berita saja per wilayah
                break
                
            title = item.find('title').text
            link = item.find('link').text
            
            # Coba ambil gambar dari tag enclosure jika ada, kalau tidak pakai placeholder
            image_url = "https://picsum.photos/700/400"
            enclosure = item.find('enclosure')
            if enclosure is not None and 'url' in enclosure.attrib:
                image_url = enclosure.attrib['url']
            
            slug = buat_slug(title)
            
            # Cek jika berita sudah pernah diambil sebelumnya, lewati
            if slug in slug_tercatat:
                continue
                
            # Susun format sesuai struktur Sveltia CMS kamu
            struktur_berita = {
                "title": f"[{wilayah}] {title}",
                "slug": slug,
                "category": "Politik", # Default masuk ke Politik, bisa diedit nanti di admin
                "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                "image": image_url,
                "body": f"Berita seputar {wilayah}. Baca selengkapnya di sumber asli: {link}"
            }
            
            berita_baru_total.append(struktur_berita)
            slug_tercatat.add(slug)
            hitung += 1
            
    except Exception as e:
        print(f"Gagal mengambil data dari wilayah {wilayah}: {e}")

# 5. Gabungkan berita baru di posisi paling atas (terbaru)
if berita_baru_total:
    daftar_berita = berita_baru_total + daftar_berita
    # Batasi total berita di JSON agar tidak terlalu berat (misal maksimal 50 berita)
    daftar_berita = daftar_berita[:50]
    
    # Simpan kembali ke public/posts.json
    with open(path_json, 'w', encoding='utf-8') as f:
        json.dump({"posts": daftar_berita}, f, indent=2, ensure_ascii=False)
    print(f"Berhasil menambahkan {len(berita_baru_total)} berita baru otomatis!")
else:
    print("Tidak ada berita baru yang unik saat ini.")


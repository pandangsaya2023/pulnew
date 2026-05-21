import urllib.request
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import os

# Menggunakan link Republika sepenuhnya yang terbukti lolos sensor server & aktif
sumber_rss = {
    "Sumatera": "https://www.republika.co.id/rss/nusantara/sumatera",
    "Jawa": "https://www.republika.co.id/rss/nusantara/jawa-barat-diy-jateng-jatim",
    "Kalimantan": "https://www.republika.co.id/rss/nusantara/kalimantan",
    "Sulawesi": "https://www.republika.co.id/rss/nusantara/sulawesi"
}

path_json = "public/posts.json"

def buat_slug(judul):
    judul = judul.lower()
    judul = re.sub(r'[^a-z0-9\s-]', '', judul)
    judul = re.sub(r'[\s-]+', '-', judul).strip('-')
    return judul[:60]

# Ambil data lama agar tidak hilang
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
berita_baru_total = []

kategori_list = ["Politik", "Ekonomi", "Hiburan"]
index_kat = 0

for wilayah, url in sumber_rss.items():
    print(f"Mengambil berita {wilayah} dari {url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=15)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        hitung = 0
        for item in root.findall('.//item'):
            if hitung >= 2: 
                break
                
            title_node = item.find('title')
            link_node = item.find('link')
            
            if title_node is None or link_node is None:
                continue
                
            title = title_node.text
            link = link_node.text
            
            # Gambar default berita elegan
            image_url = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600"
            
            # Ambil media gambar jika disediakan oleh Republika
            enclosure = item.find('enclosure')
            if enclosure is not None and 'url' in enclosure.attrib:
                image_url = enclosure.attrib['url']
            
            slug = buat_slug(title)
            
            if slug in slug_tercatat:
                continue
            
            kategori_pilihan = kategori_list[index_kat % len(kategori_list)]
            index_kat += 1
                
            struktur_berita = {
                "title": f"[{wilayah}] {title}",
                "slug": slug,
                "category": kategori_pilihan,
                "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                "image": image_url,
                "body": f"Berita seputar wilayah {wilayah}. Informasi selengkapnya mengenai topik ini dapat Anda baca langsung melalui tautan resmi sumber asli penyedia media berita berikut: {link}"
            }
            
            berita_baru_total.append(struktur_berita)
            slug_tercatat.add(slug)
            hitung += 1
            
    except Exception as e:
        print(f"Abaikan error kecil di {wilayah}, lanjut terus! Detail: {e}")

# KUNCI UTAMA: Biarpun ada wilayah yang gagal, berita dari wilayah yang sukses HARUS tetap disimpan!
if berita_baru_total:
    daftar_berita = berita_baru_total + daftar_berita
    daftar_berita = daftar_berita[:50]
    
    with open(path_json, 'w', encoding='utf-8') as f:
        json.dump({"posts": daftar_berita}, f, indent=2, ensure_ascii=False)
    print(f"Sukses mengumpulkan {len(berita_baru_total)} berita baru ke JSON!")
else:
    print("Tidak ada data berita baru yang berhasil dimuat.")

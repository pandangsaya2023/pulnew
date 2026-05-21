import urllib.request
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import os
import random

# Kolaborasi RSS Feed Media Nasional Terbesar & Terstabil
sumber_rss = {
    "Nasional": "https://www.antaranews.com/rss/top-news.xml",
    "Ekonomi": "https://www.cnbcindonesia.com/news/rss",
    "Teknologi": "https://www.cnnindonesia.com/teknologi/rss",
    "Hiburan": "https://www.republika.co.id/rss/senggang",
    "Olahraga": "https://www.antaranews.com/rss/olahraga.xml",
    "Otomotif": "https://www.otomotifnet.com/rss"
}

path_json = "public/posts.json"

def buat_slug(judul):
    judul = judul.lower()
    judul = re.sub(r'[^a-z0-9\s-]', '', judul)
    judul = re.sub(r'[\s-]+', '-', judul).strip('-')
    return judul[:60]

# Ambil data lama agar tidak hilang saat ditimpa
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

# Mapping Kategori agar sesuai dengan menu navigasi HTML kamu
# Jika HTML kamu hanya membaca (Politik, Ekonomi, Hiburan), kita sesuaikan ke yang terdekat
def petakan_kategori(nama_sumber):
    if nama_sumber in ["Nasional", "Olahraga"]:
        return "Politik"  # Dimasukkan ke tab Politik/Umum
    elif nama_sumber in ["Ekonomi", "Teknologi", "Otomotif"]:
        return "Ekonomi"  # Dimasukkan ke tab Ekonomi/Bisnis
    else:
        return "Hiburan"  # Dimasukkan ke tab Hiburan

for kategori_asal, url in sumber_rss.items():
    print(f"Mengambil berita kategori {kategori_asal}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=15)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        # Mengambil 5 berita per kategori supaya halaman langsung padat!
        hitung = 0
        for item in root.findall('.//item'):
            if hitung >= 5: 
                break
                
            title_node = item.find('title')
            link_node = item.find('link')
            
            if title_node is None or link_node is None:
                continue
                
            title = title_node.text.strip()
            link = link_node.text.strip()
            
            # Gambar default berita elegan
            image_url = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600"
            
            # Cari gambar asli dari RSS feed
            enclosure = item.find('enclosure')
            if enclosure is not None and 'url' in enclosure.attrib:
                image_url = enclosure.attrib['url']
            else:
                media_content = item.find('{http://search.yahoo.com/mrss/}content')
                if media_content is not None and 'url' in media_content.attrib:
                    image_url = media_content.attrib['url']
            
            slug = buat_slug(title)
            
            if slug in slug_tercatat:
                continue
                
            kategori_web = petakan_kategori(kategori_asal)
                
            struktur_berita = {
                "title": title,
                "slug": slug,
                "category": kategori_web,
                "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                "image": image_url,
                "body": f"Berita terkini mengenai topik {kategori_asal}. Informasi selengkapnya mengenai berita ini dapat Anda baca langsung melalui tautan resmi sumber asli penyedia media berikut: {link}"
            }
            
            berita_baru_total.append(struktur_berita)
            slug_tercatat.add(slug)
            hitung += 1
            
    except Exception as e:
        print(f"Abaikan error di {kategori_asal}, lanjut! Detail: {e}")

if berita_baru_total:
    # Acak urutan berita baru agar feed beritanya bervariasi (tidak menumpuk satu kategori)
    random.shuffle(berita_baru_total)
    
    # Gabungkan dengan berita lama, batasi maksimal menampung 100 berita di file JSON
    daftar_berita = berita_baru_total + daftar_berita
    daftar_berita = daftar_berita[:100]
    
    with open(path_json, 'w', encoding='utf-8') as f:
        json.dump({"posts": daftar_berita}, f, indent=2, ensure_ascii=False)
    print(f"Sukses! Berhasil menambahkan {len(berita_baru_total)} berita nasional baru.")
else:
    print("Tidak ada berita baru saat ini.")


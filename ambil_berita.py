import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import urllib.request
import random
from openai import OpenAI
from bs4 import BeautifulSoup

def ambil_konten_berita(url):
    """Fungsi untuk mengambil teks asli dari link agar AI punya bahan tulisan"""
    try:
        headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')
            # Mengambil semua teks dari tag <p> sebagai bahan berita
            paragraphs = [p.get_text() for p in soup.find_all('p')]
            full_text = " ".join(paragraphs)
            return full_text[:4000] # Batasi 4000 karakter agar tidak error di AI
    except Exception as e:
        print(f"Gagal scrape {url}: {e}")
        return ""

def rewrite_with_ai(title, link):
    """Fungsi AI untuk menulis ulang berita menjadi artikel panjang"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return f"Baca selengkapnya di {link}"

    konten_asli = ambil_konten_berita(link)
    
    try:
        client = OpenAI(
            api_key=api_key.strip(),
            base_url="https://api.groq.com/openai/v1",
        )

        prompt = f"""
        Anda adalah seorang jurnalis senior Indonesia yang ahli menulis berita unik, mendalam, dan kaya kosakata. 
        Tugas Anda adalah mengembangkan berita berikut menjadi artikel berita utuh yang terdiri dari 3 sampai 4 paragraf.
        
        Judul Berita: {title}
        Isi Berita Asli: {konten_asli}
        
        Ketentuan Penulisan:
        1. Jangan sekadar meringkas, kembangkan menjadi artikel yang enak dibaca.
        2. Gunakan variasi kalimat yang kreatif dan tidak monoton.
        3. Di akhir paragraf wajib tambahkan kalimat: "Berita selengkapnya bisa dibaca di {link}"
        """

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Anda adalah jurnalis profesional."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error AI: {e}")
        return f"Baca selengkapnya di {link}"

# --- KONFIGURASI SUMBER BERITA ---
sumber_rss = [
    {"media": "Detikcom", "url": "https://rss.detik.com/index.php/detikcom"},
    {"media": "Kompas", "url": "https://nasional.kompas.com/rss/index.xml"},
    {"media": "Tempo", "url": "https://rss.tempo.co/nasional"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
    {"media": "Okezone", "url": "https://sindonews.com/rss"}
]

path_json = "posts.json"

def buat_slug(judul):
    judul = judul.lower()
    judul = re.sub(r'[^a-z0-9\s-]', '', judul)
    judul = re.sub(r'[\s-]+', '-', judul).strip('-')
    return judul[:60]

def deteksi_kategori(judul):
    j = judul.lower()
    if any(x in j for x in ['ekonomi', 'rupiah', 'bisnis']): return "Ekonomi"
    elif any(x in j for x in ['teknologi', 'hp', 'ai']): return "Teknologi"
    elif any(x in j for x in ['olahraga', 'bola', 'timnas']): return "Olahraga"
    return "Politik"

# --- PROSES UTAMA ---
if os.path.exists(path_json):
    with open(path_json, 'r', encoding='utf-8') as f:
        data_lama = json.load(f)
        daftar_berita = data_lama.get("posts", []) if isinstance(data_lama, dict) else data_lama
else:
    daftar_berita = []

slug_tercatat = {b["slug"] for b in daftar_berita if "slug" in b}
berita_baru = []

for sumber in sumber_rss:
    try:
        req = urllib.request.Request(sumber["url"], headers={'User-Agent': "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            root = ET.fromstring(response.read())
            for item in root.findall('.//item'):
                title = item.find('title').text.strip()
                link = item.find('link').text.strip()
                slug = buat_slug(title)
                
                if slug in slug_tercatat: continue
                
                print(f"Menulis ulang: {title}")
                isi_artikel = rewrite_with_ai(title, link)
                
                berita_baru.append({
                    "id": int(datetime.now().strftime("%H%M%S")) + random.randint(100,999),
                    "title": title,
                    "slug": slug,
                    "category": deteksi_kategori(title),
                    "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                    "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600",
                    "body": isi_artikel
                })
                slug_tercatat.add(slug)
                if len(berita_baru) >= 3: break
    except Exception as e:
        print(f"Error {sumber['media']}: {e}")

if berita_baru:
    daftar_berita = berita_baru + daftar_berita
    with open(path_json, 'w', encoding='utf-8') as f:
        json.dump({"posts": daftar_berita[:100]}, f, indent=2, ensure_ascii=False)
    print("Update Selesai!")

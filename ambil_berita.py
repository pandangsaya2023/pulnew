import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import urllib.request
import time
import random
from openai import OpenAI
from bs4 import BeautifulSoup

# --- 1. FUNGSI UNTUK MENGAMBIL ISI BERITA DARI WEB ---
def ambil_konten_berita(url):
    try:
        # Meniru perilaku browser asli agar tidak kena blokir 403 Forbidden
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            soup = BeautifulSoup(response.read(), 'html.parser')
            # Mengambil teks dari tag <p> sebagai bahan mentah
            paragraphs = [p.get_text() for p in soup.find_all('p')]
            return " ".join(paragraphs)[:4000] # Batasi agar tidak overload
    except Exception as e:
        print(f"Gagal mengambil isi {url}: {e}")
        return ""

# --- 2. FUNGSI AI UNTUK MENULIS ULANG BERITA ---
def rewrite_with_ai(title, link):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return f"Baca selengkapnya di {link}"

    konten_asli = ambil_konten_berita(link)
    
    try:
        client = OpenAI(api_key=api_key.strip(), base_url="https://api.groq.com/openai/v1")
        prompt = f"""
        Anda adalah jurnalis senior. Kembangkan judul dan konten berita berikut menjadi artikel berita utuh yang profesional, unik, dan informatif.
        Judul: {title}
        Konten Mentah: {konten_asli}
        
        Instruksi:
        1. Tulis dalam 3-4 paragraf yang mengalir (jangan gunakan format daftar/poin).
        2. Jangan menyalin teks asli, lakukan penulisan ulang (paraphrase) yang kreatif.
        3. Wajib gunakan bahasa Indonesia yang baku dan menarik.
        4. Di paragraf paling akhir, wajib tambahkan kalimat: "Berita selengkapnya bisa dibaca di {link}"
        """

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error AI: {e}")
        return f"Baca selengkapnya di {link}"

# --- 3. PROSES UTAMA ---
sumber_rss = [
    {"media": "Detikcom", "url": "https://rss.detik.com/index.php/detikcom"},
    {"media": "Kompas", "url": "https://nasional.kompas.com/rss/index.xml"},
    {"media": "Tempo", "url": "https://rss.tempo.co/nasional"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
    {"media": "Okezone", "url": "https://sindonews.com/rss"}
]

path_json = "posts.json"

# Load Data Lama
daftar_berita = []
if os.path.exists(path_json):
    with open(path_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
        daftar_berita = data.get("posts", []) if isinstance(data, dict) else data

slug_tercatat = {b["slug"] for b in daftar_berita if "slug" in b}
berita_baru = []

for sumber in sumber_rss:
    print(f"Memproses {sumber['media']}...")
    try:
        req = urllib.request.Request(sumber["url"], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            root = ET.fromstring(response.read())
            for item in root.findall('.//item'):
                title = item.find('title').text.strip()
                link = item.find('link').text.strip()
                slug = re.sub(r'[^a-z0-9]', '-', title.lower())[:60]
                
                if slug in slug_tercatat: continue
                
                print(f" - Menulis: {title}")
                body = rewrite_with_ai(title, link)
                
                berita_baru.append({
                    "id": int(datetime.now().strftime("%H%M%S")) + random.randint(100,999),
                    "title": title,
                    "slug": slug,
                    "category": "Politik", # Bisa disesuaikan lagi
                    "date": datetime.now().isoformat(),
                    "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600",
                    "body": body
                })
                slug_tercatat.add(slug)
                time.sleep(2) # Jeda agar tidak terkena rate-limit
                if len(berita_baru) >= 3: break
    except Exception as e:
        print(f"Gagal memproses {sumber['media']}: {e}")

if berita_baru:
    daftar_berita = berita_baru + daftar_berita
    with open(path_json, 'w', encoding='utf-8') as f:
        json.dump({"posts": daftar_berita[:100]}, f, indent=2, ensure_ascii=False)
    print("Sukses Update Berita!")


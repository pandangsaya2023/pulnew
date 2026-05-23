import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import time
import random
import requests
from openai import OpenAI
from bs4 import BeautifulSoup

# --- 1. FUNGSI SCRAPING YANG LEBIH TANGGUH ---
def ambil_konten_berita(url):
    """Mengambil teks dengan header browser yang menyamar sebagai manusia"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Referer': 'https://www.google.com/'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Ambil semua teks dari tag <p>
            paragraphs = [p.get_text() for p in soup.find_all('p')]
            return " ".join(paragraphs)[:4000] # Maksimal 4000 karakter
        else:
            print(f"  -> Gagal akses (Status {response.status_code}): {url}")
            return ""
    except Exception as e:
        print(f"  -> Error Scraping: {e}")
        return ""

# --- 2. FUNGSI AI DENGAN PROMPT PROFESIONAL ---
def rewrite_with_ai(title, link):
    api_key = os.getenv("GROQ_API_KEY")
    konten_asli = ambil_konten_berita(link)
    
    if not konten_asli:
        return f"Berita selengkapnya dapat dibaca di {link}"

    try:
        client = OpenAI(api_key=api_key.strip(), base_url="https://api.groq.com/openai/v1")
        prompt = f"""
        Anda adalah jurnalis profesional. Tulis ulang berita berikut menjadi artikel yang menarik dan mendalam.
        Judul: {title}
        Konten Mentah: {konten_asli}
        
        Instruksi:
        1. Buatlah artikel sepanjang minimal 3 paragraf.
        2. Gunakan gaya bahasa jurnalistik yang mengalir dan unik (paraphrase).
        3. Dilarang menyalin teks mentah, tulis ulang dengan struktur kalimat yang baru.
        4. Wajib akhiri dengan kalimat: "Berita selengkapnya bisa dibaca di {link}"
        """
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"  -> Error AI: {e}")
        return f"Berita selengkapnya bisa dibaca di {link}"

# --- 3. PROSES UTAMA ---
sumber_rss = [
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
    {"media": "Okezone", "url": "https://sindonews.com/rss"},
    {"media": "Antara Nasional", "url": "https://www.antaranews.com/rss/nasional"},
    {"media": "VOA Indonesia", "url": "https://www.voaindonesia.com/api/z$yqepviqpq"},
    {"media": "DW Indonesia", "url": "https://rss.dw.com/rdf/rss-id-indonesia"},
    {"media": "Pikiran Rakyat", "url": "https://www.pikiran-rakyat.com/feed"},
    {"media": "Jawa Pos", "url": "https://www.jawapos.com/feed"}
]

]

path_json = "posts.json"
if os.path.exists(path_json):
    with open(path_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
        daftar_berita = data.get("posts", []) if isinstance(data, dict) else data
else:
    daftar_berita = []

slug_tercatat = {b["slug"] for b in daftar_berita if "slug" in b}
berita_baru = []

for sumber in sumber_rss:
    print(f"Memproses {sumber['media']}...")
    try:
        response = requests.get(sumber['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        root = ET.fromstring(response.content)
        
        for item in root.findall('.//item'):
            title = item.find('title').text.strip()
            link = item.find('link').text.strip()
            slug = re.sub(r'[^a-z0-9]', '-', title.lower())[:60]
            
            if slug in slug_tercatat: continue
            
            print(f" -> Menulis: {title}")
            body = rewrite_with_ai(title, link)
            
            berita_baru.append({
                "id": int(datetime.now().strftime("%H%M%S")) + random.randint(100,999),
                "title": title,
                "slug": slug,
                "category": "Politik",
                "date": datetime.now().isoformat(),
                "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600",
                "body": body
            })
            slug_tercatat.add(slug)
            time.sleep(5) # JEDA 5 DETIK AGAR TIDAK DIBLOKIR
            if len(berita_baru) >= 3: break
    except Exception as e:
        print(f"Gagal memproses {sumber['media']}: {e}")

if berita_baru:
    daftar_berita = berita_baru + daftar_berita
    with open(path_json, 'w', encoding='utf-8') as f:
        json.dump({"posts": daftar_berita[:100]}, f, indent=2, ensure_ascii=False)
    print("Update Berita Selesai!")


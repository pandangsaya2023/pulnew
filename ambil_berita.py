import os
import json
import re
import time
import requests
from datetime import datetime
from openai import OpenAI
from bs4 import BeautifulSoup

# --- 1. FUNGSI SCRAPING AGRESIV (MENGAMBIL ISI BERITA) ---
def ambil_konten_berita(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Hapus elemen pengganggu
            for s in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
                s.decompose()
            
            # Cari elemen yang kemungkinan besar berisi artikel
            target = soup.find('article') or soup.find('div', class_=re.compile('content|body|article|entry-content'))
            
            if target:
                text = target.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)
                
            return text[:8000] # Ambil lebih banyak data agar AI punya konteks luas
        return ""
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

# --- 2. FUNGSI AI (PENULISAN ARTIKEL PANJANG) ---
def rewrite_with_ai(title, link):
    api_key = os.getenv("GROQ_API_KEY")
    konten_asli = ambil_konten_berita(link)
    
    # Jika gagal scraping, kembalikan teks singkat
    if not konten_asli or len(konten_asli) < 100:
        return f"Berita selengkapnya bisa dibaca di {link}"
    
    try:
        client = OpenAI(api_key=api_key.strip(), base_url="https://api.groq.com/openai/v1")
        prompt = f"""
        Anda adalah seorang jurnalis profesional. Tugas Anda adalah mengubah bahan mentah berita berikut menjadi artikel yang MENDALAM, INFORMATIF, dan PANJANG (minimal 5 paragraf).
        
        JUDUL BERITA: {title}
        BAHAN KONTEN: {konten_asli}
        
        INSTRUKSI KHUSUS:
        1. Jangan membuat ringkasan. Uraikan fakta-fakta yang ada secara detail.
        2. Gunakan gaya bahasa jurnalistik yang mengalir dan menarik (storytelling).
        3. Jika ada kutipan atau data, masukkan ke dalam artikel agar lebih kredibel.
        4. Artikel harus panjang dan berbobot.
        5. Wajib akhiri artikel dengan kalimat: "Berita selengkapnya bisa dibaca di {link}"
        """
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2500
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error AI: {e}")
        return f"Berita selengkapnya bisa dibaca di {link}"

# --- 3. PROSES UTAMA ---
sumber_rss = [
    {"media": "Antara", "url": "https://www.antaranews.com/rss/nasional"},
    {"media": "Pikiran Rakyat", "url": "https://www.pikiran-rakyat.com/feed"},
    {"media": "Tribunnews", "url": "https://www.tribunnews.com/rss"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
    {"media": "Okezone", "url": "https://sindonews.com/rss"},
    # {"media": "VOA Indonesia", "url": "https://www.voaindonesia.com/api/z$yqepviqpq"},
    {"media": "DW Indonesia", "url": "https://rss.dw.com/rdf/rss-id-indonesia"},
    # {"media": "Pikiran Rakyat", "url": "https://www.pikiran-rakyat.com/feed"},
    {"media": "Jawa Pos", "url": "https://www.jawapos.com/feed"}
]
]

path_json = "posts.json"
daftar_berita = []
if os.path.exists(path_json):
    with open(path_json, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            daftar_berita = data.get("posts", []) if isinstance(data, dict) else data
        except:
            daftar_berita = []

slug_tercatat = {b["slug"] for b in daftar_berita if "slug" in b}
berita_baru = []

for sumber in sumber_rss:
    print(f"Mengakses {sumber['media']}...")
    try:
        response = requests.get(sumber['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(response.content, 'xml')
        
        for item in soup.find_all('item'):
            title = item.find('title').get_text(strip=True)
            link = item.find('link').get_text(strip=True)
            slug = re.sub(r'[^a-z0-9]', '-', title.lower())[:60]
            
            if slug not in slug_tercatat:
                print(f" -> Menulis: {title}")
                body = rewrite_with_ai(title, link)
                berita_baru.append({
                    "id": int(time.time()),
                    "title": title, 
                    "slug": slug, 
                    "category": "Politik",
                    "date": datetime.now().isoformat(),
                    "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600",
                    "body": body
                })
                slug_tercatat.add(slug)
                time.sleep(8) # Jeda lebih lama agar semakin sulit dideteksi bot
            if len(berita_baru) >= 2: break # Hanya ambil 2 berita per sumber agar tidak kena limit
    except Exception as e:
        print(f"Error pada {sumber['media']}: {e}")

if berita_baru:
    daftar_berita = berita_baru + daftar_berita
    with open(path_json, 'w', encoding='utf-8') as f:
        json.dump({"posts": daftar_berita[:50]}, f, indent=2, ensure_ascii=False)
    print("Selesai Update!")

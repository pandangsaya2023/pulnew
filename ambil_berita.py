import os
import json
import re
import time
import requests
from datetime import datetime
from openai import OpenAI
from bs4 import BeautifulSoup

def ambil_konten_berita(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for s in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
                s.decompose()
            target = soup.find('article') or soup.find('div', class_=re.compile('content|body|article|entry-content'))
            text = target.get_text(separator=' ', strip=True) if target else soup.get_text(separator=' ', strip=True)
            return text[:8000]
        return ""
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def rewrite_with_ai(title, link):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY kosong")
        return f"Berita selengkapnya bisa dibaca di {link}"

    konten_asli = ambil_konten_berita(link)
    if not konten_asli or len(konten_asli) < 100:
        return f"Berita selengkapnya bisa dibaca di {link}"

    try:
        client = OpenAI(api_key=api_key.strip(), base_url="https://api.groq.com/openai/v1")
        prompt = f"""
Anda adalah jurnalis profesional. Ubah bahan mentah ini jadi artikel MENDALAM minimal 5 paragraf dengan gaya jurnalistik.
JUDUL: {title}
BAHAN: {konten_asli}
Wajib akhiri dengan: "Berita selengkapnya bisa dibaca di {link}"
"""
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1200
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error AI: {e}")
        return konten_asli [:1500] + f"... Berita selengkapnya bisa dibaca di {link}"

# Sumber RSS
sumber_rss = [
    {"media": "Antara", "url": "https://www.antaranews.com/rss/nasional"},
    {"media": "Pikiran Rakyat", "url": "https://www.pikiran-rakyat.com/feed"},
    {"media": "Tribunnews", "url": "https://www.tribunnews.com/rss"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
    {"media": "Okezone", "url": "https://sindonews.com/rss"},
    {"media": "DW Indonesia", "url": "https://rss.dw.com/rdf/rss-id-indonesia"},
    {"media": "Jawa Pos", "url": "https://www.jawapos.com/feed"}
]

# Bikin folder public/posts kalau belum ada
os.makedirs('public/posts', exist_ok=True)

# Baca slug yang udah ada biar gak dobel
slug_tercatat = set()
for f in os.listdir('public/posts'):
    if f.endswith('.json'):
        try:
            with open(f'public/posts/{f}', 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                slug_tercatat.add(data.get('slug'))
        except:
            pass

jumlah_baru = 0
for sumber in sumber_rss:
    print(f"Mengakses {sumber['media']}...")
    try:
        response = requests.get(sumber['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(response.content, 'xml')

        for item in soup.find_all('item')[:3]:
            title = item.find('title').get_text(strip=True)
            link = item.find('link').get_text(strip=True)

            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]
            if not slug:
                slug = f"berita-{int(time.time() * 1000)}"

            if slug not in slug_tercatat:
                print(f" -> Menulis: {title}")
                body = rewrite_with_ai(title, link)

                berita = {
                    "slug": slug,
                    "title": title,
                    "content": body[:200] + "...", # preview buat index.html
                    "body": body, # artikel lengkap buat halaman detail
                    "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600",
                    "kategori": "BERITA",
                    "date": datetime.now().isoformat()
                }

                # Simpan per file: public/posts/slug.json
                with open(f'public/posts/{slug}.json', 'w', encoding='utf-8') as f:
                    json.dump(berita, f, indent=2, ensure_ascii=False)

                slug_tercatat.add(slug)
                jumlah_baru += 1
                time.sleep(15) # jeda 15 detik biar gak diblokir

            if jumlah_baru >= 5: # max 5 berita per run
                break
    except Exception as e:
        print(f"Error pada {sumber['media']}: {e}")

print(f"Selesai! Nambah {jumlah_baru} berita baru")

import os
import json
import re
import time
import requests
from datetime import datetime
from openai import OpenAI
from bs4 import BeautifulSoup

# --- KONFIGURASI ---
BASE_URL = "https://pulnew.pages.dev"
sumber_rss = [
    {"media": "Antara", "url": "https://www.antaranews.com/rss/nasional"},
    {"media": "Pikiran Rakyat", "url": "https://www.pikiran-rakyat.com/feed"},
    {"media": "Tribunnews", "url": "https://www.tribunnews.com/rss"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
    {"media": "Okezone", "url": "https://sindonews.com/rss"},
    {"media": "DW Indonesia", "url": "https://rss.dw.com/rdf/rss-id-indonesia"},
    {"media": "Jawa Pos", "url": "https://www.jawapos.com/feed"}
]

# --- FUNGSI ---
def ambil_konten_berita(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for s in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
                s.decompose()
            target = soup.find('article') or soup.find('div', class_=re.compile('content|body'))
            text = target.get_text(separator=' ', strip=True) if target else soup.get_text(separator=' ', strip=True)
            return text[:8000], soup
        return "", None
    except: return "", None

def ambil_gambar_asli(soup, url):
    # Selalu menggunakan gambar default Anda sendiri
    return f"{BASE_URL}/images/og-default.jpg"

def rewrite_with_ai(title, link):
    api_key = os.getenv("GROQ_API_KEY")
    konten_asli, soup = ambil_konten_berita(link)
    if not api_key or not konten_asli or len(konten_asli) < 100:
        return f"Berita selengkapnya bisa dibaca di {link}", soup
    try:
        client = OpenAI(api_key=api_key.strip(), base_url="https://api.groq.com/openai/v1")
        prompt = f"Tulis ulang berita ini jadi 5 paragraf profesional. JUDUL: {title}. KONTEN: {konten_asli}. Akhiri dengan: 'Berita selengkapnya bisa dibaca di {link}'"
        completion = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1200)
        return completion.choices[0].message.content, soup
    except: return konten_asli[:500] + "...", soup

def bikin_html_statis(slug, title, img_url):
    folder_output = 'public/berita'
    os.makedirs(folder_output, exist_ok=True)
    link_statis = f"{BASE_URL}/berita/{slug}.html"
    link_wa = f"https://wa.me/?text=Baca%20berita%20ini:%20{link_statis}"
    
    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta property="og:title" content="{title}">
    <meta property="og:image" content="{img_url}">
    <meta property="og:url" content="{link_statis}">
    <meta property="og:type" content="article">
    <title>{title}</title>
</head>
<body style="font-family:sans-serif; text-align:center; padding:50px; background:#f4f4f4;">
    <div style="background:white; padding:30px; border-radius:15px; max-width:500px; margin:auto; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
        <h3 style="color:#333;">{title}</h3>
        <a href="{BASE_URL}/berita.html?slug={slug}" style="display:block; margin:20px 0; padding:15px; background:#007bff; color:white; text-decoration:none; border-radius:10px; font-weight:bold;">Baca Berita Lengkap</a>
        <a href="{link_wa}" style="display:block; margin:20px 0; padding:15px; background:#25D366; color:white; text-decoration:none; border-radius:10px; font-weight:bold;">📲 Share ke WhatsApp</a>
    </div>
</body>
</html>"""
    with open(f"{folder_output}/{slug}.html", "w", encoding="utf-8") as f:
        f.write(html)

# --- EKSEKUSI ---
os.makedirs('public/posts', exist_ok=True)
slug_tercatat = {f.replace('.json', '') for f in os.listdir('public/posts') if f.endswith('.json')}
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
            if not slug: slug = f"berita-{int(time.time() * 1000)}"
            if slug not in slug_tercatat:
                body, soup_artikel = rewrite_with_ai(title, link)
                img_url = ambil_gambar_asli(soup_artikel, link)
                berita = {"slug": slug, "title": title, "content": body[:200] + "...", "body": body, "image": img_url, "kategori": "BERITA", "date": datetime.now().isoformat()}
                
                with open(f'public/posts/{slug}.json', 'w', encoding='utf-8') as f:
                    json.dump(berita, f, indent=2, ensure_ascii=False)
                
                bikin_html_statis(slug, title, img_url)
                slug_tercatat.add(slug)
                jumlah_baru += 1
                time.sleep(10)
            if jumlah_baru >= 5: break
    except Exception as e: print(f"Error: {e}")
print(f"Selesai! Nambah {jumlah_baru} berita baru")


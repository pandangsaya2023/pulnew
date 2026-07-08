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
    {"media": "Okezone", "url": "https://sindonews.com/rss"}
]

def ambil_konten_berita(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            target = soup.find('article') or soup.find('div', class_=re.compile('content|body'))
            text = target.get_text(separator=' ', strip=True) if target else soup.get_text(separator=' ', strip=True)
            return text[:8000], soup
        return "", None
    except: return "", None

def rewrite_with_ai(title, link):
    api_key = os.getenv("GROQ_API_KEY")
    konten_asli, soup = ambil_konten_berita(link)
    if not api_key or not konten_asli: return f"Baca selengkapnya di {link}", None
    try:
        client = OpenAI(api_key=api_key.strip(), base_url="https://api.groq.com/openai/v1")
        prompt = f"Tulis ulang: {title}. Konten: {konten_asli[:2000]}. Akhiri dengan: 'Baca selengkapnya di {link}'"
        completion = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}], max_tokens=1000)
        return completion.choices[0].message.content, None
    except: return konten_asli[:500] + "...", None

def bikin_html_statis(slug, title):
    folder_output = 'public/berita'
    os.makedirs(folder_output, exist_ok=True)
    link_statis = f"{BASE_URL}/berita/{slug}.html"
    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta property="og:title" content="{title}">
    <meta property="og:image" content="{BASE_URL}/media/og-default.jpg">
    <meta property="og:url" content="{link_statis}">
    <meta property="og:type" content="article">
    <title>{title}</title>
    <script>window.location.href = "{BASE_URL}/berita.html?slug={slug}";</script>
</head>
<body><p>Mengalihkan...</p></body>
</html>"""
    with open(f"{folder_output}/{slug}.html", "w", encoding="utf-8") as f: f.write(html)

# --- EKSEKUSI ---
os.makedirs('public/posts', exist_ok=True)
slug_tercatat = {f.replace('.json', '') for f in os.listdir('public/posts') if f.endswith('.json')}

for sumber in sumber_rss:
    try:
        soup = BeautifulSoup(requests.get(sumber['url'], timeout=15).content, 'xml')
        for item in soup.find_all('item')[:3]:
            title = item.find('title').get_text(strip=True)
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]
            if slug not in slug_tercatat:
                link = item.find('link').get_text(strip=True)
                body, _ = rewrite_with_ai(title, link)
                berita = {"slug": slug, "title": title, "body": body, "image": f"{BASE_URL}/media/og-default.jpg", "date": datetime.now().isoformat()}
                with open(f'public/posts/{slug}.json', 'w', encoding='utf-8') as f: json.dump(berita, f, indent=2, ensure_ascii=False)
                bikin_html_statis(slug, title)
                slug_tercatat.add(slug)
                time.sleep(5)
    except: continue

# UPDATE INDEKS (posts.json)
daftar = []
for f_json in os.listdir('public/posts'):
    if f_json.endswith('.json'):
        with open(f'public/posts/{f_json}', 'r', encoding='utf-8') as f: daftar.append(json.load(f))
with open('public/posts.json', 'w', encoding='utf-8') as f: json.dump(sorted(daftar, key=lambda x: x['date'], reverse=True), f, indent=2, ensure_ascii=False)


import os, json, re, time, requests
from datetime import datetime
from openai import OpenAI
from bs4 import BeautifulSoup

BASE_URL = "https://pulnew.pages.dev"
sumber_rss = [
    {"media": "Antara", "url": "https://www.antaranews.com/rss/nasional"},
    {"media": "Pikiran Rakyat", "url": "https://www.pikiran-rakyat.com/feed"}
    {"media": "Tribunnews", "url": "https://www.tribunnews.com/rss"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
    {"media": "Okezone", "url": "https://sindonews.com/rss"},
    {"media": "DW Indonesia", "url": "https://rss.dw.com/rdf/rss-id-indonesia"},
    {"media": "Jawa Pos", "url": "https://www.jawapos.com/feed"}
]

# Fungsi untuk membuat file HTML perantara agar WhatsApp bisa menampilkan preview
def bikin_html_statis(slug, title, image_url):
    folder_output = 'public/berita'
    os.makedirs(folder_output, exist_ok=True)
    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta property="og:title" content="{title}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:url" content="{BASE_URL}/berita/{slug}.html">
    <meta property="og:type" content="article">
    <meta http-equiv="refresh" content="0; url={BASE_URL}/berita.html?slug={slug}">
    <title>{title}</title>
</head>
<body><script>window.location.href = "{BASE_URL}/berita.html?slug={slug}";</script></body>
</html>"""
    with open(f"{folder_output}/{slug}.html", "w", encoding="utf-8") as f: f.write(html)

def rewrite_with_ai(title, link):
    api_key = os.getenv("GROQ_API_KEY")
    try:
        client = OpenAI(api_key=api_key.strip(), base_url="https://api.groq.com/openai/v1")
        prompt = f"Rangkum berita ini: {title}. Berikan ringkasan yang informatif. Akhiri dengan: 'Baca selengkapnya di {link}'"
        completion = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}], max_tokens=600)
        return completion.choices[0].message.content
    except: return f"Berita terkini: {title}. Baca selengkapnya di {link}"

# EKSEKUSI
os.makedirs('public/posts', exist_ok=True)
slug_tercatat = {f.replace('.json', '') for f in os.listdir('public/posts') if f.endswith('.json')}

for sumber in sumber_rss:
    try:
        soup = BeautifulSoup(requests.get(sumber['url'], timeout=15).content, 'xml')
        for item in soup.find_all('item')[:3]:
            title = item.find('title').get_text(strip=True)
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]
            if slug not in slug_tercatat:
                body = rewrite_with_ai(title, item.find('link').get_text())
                image_url = f"{BASE_URL}/media/og-default.jpg"
                
                berita = {
                    "slug": slug, "title": title, "body": body, 
                    "image": image_url, 
                    "date": datetime.now().isoformat()
                }
                # Simpan JSON
                with open(f'public/posts/{slug}.json', 'w', encoding='utf-8') as f: json.dump(berita, f, indent=2, ensure_ascii=False)
                # Buat file HTML perantara untuk WhatsApp
                bikin_html_statis(slug, title, image_url)
                
                slug_tercatat.add(slug)
                time.sleep(2)
    except: continue

# UPDATE INDEKS (posts.json)
daftar = [json.load(open(f'public/posts/{f}', 'r', encoding='utf-8')) for f in os.listdir('public/posts') if f.endswith('.json')]
with open('public/posts.json', 'w', encoding='utf-8') as f: json.dump(sorted(daftar, key=lambda x: x['date'], reverse=True), f, indent=2, ensure_ascii=False)


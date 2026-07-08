9import os, json, re, time, requests
from datetime import datetime
from openai import OpenAI
from bs4 import BeautifulSoup

BASE_URL = "https://pulnew.pages.dev"
# Gunakan User-Agent agar tidak diblokir website berita
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

sumber_rss = [
    {"media": "Antara", "url": "https://www.antaranews.com/rss/nasional"},
    {"media": "Pikiran Rakyat", "url": "https://www.pikiran-rakyat.com/feed"},
    {"media": "Tribunnews", "url": "https://www.tribunnews.com/rss"},
    {"media": "Republika", "url": "https://www.republika.co.id/rss"},
    {"media": "Okezone", "url": "https://sindonews.com/rss"},
    {"media": "DW Indonesia", "url": "https://rss.dw.com/rdf/rss-id-indonesia"}
    # Tambahkan yang lain satu per satu untuk mengetes mana yang aktif
]

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
        # Menambahkan headers agar tidak dianggap bot jahat
        response = requests.get(sumber['url'], headers=HEADERS, timeout=20)
        soup = BeautifulSoup(response.content, 'xml')
        
        # Cari 'item' atau 'entry' (untuk RSS yang beda format)
        items = soup.find_all('item') if soup.find_all('item') else soup.find_all('entry')
        
        for item in items[:3]:
            title_tag = item.find('title')
            link_tag = item.find('link')
            
            # Ambil link dengan cara yang aman
            link = link_tag.get('href') if link_tag and link_tag.has_attr('href') else link_tag.get_text()
            title = title_tag.get_text(strip=True)
            
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]
            
            if slug not in slug_tercatat:
                body = rewrite_with_ai(title, link)
                image_url = f"{BASE_URL}/media/og-default.jpg"
                
                berita = {
                    "slug": slug, "title": title, "body": body, 
                    "image": image_url, 
                    "date": datetime.now().isoformat()
                }
                with open(f'public/posts/{slug}.json', 'w', encoding='utf-8') as f: json.dump(berita, f, indent=2, ensure_ascii=False)
                bikin_html_statis(slug, title, image_url)
                slug_tercatat.add(slug)
                time.sleep(3) # Jeda lebih lama agar tidak kena rate limit
    except Exception as e:
        print(f"Gagal memuat {sumber['media']}: {e}")
        continue

# UPDATE INDEKS
daftar = [json.load(open(f'public/posts/{f}', 'r', encoding='utf-8')) for f in os.listdir('public/posts') if f.endswith('.json')]
with open('public/posts.json', 'w', encoding='utf-8') as f: json.dump(sorted(daftar, key=lambda x: x['date'], reverse=True), f, indent=2, ensure_ascii=False)

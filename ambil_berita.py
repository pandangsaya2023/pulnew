import os
import json
import re
import time
import requests
from datetime import datetime
from openai import OpenAI
from bs4 import BeautifulSoup

BASE_URL = "https://pulnew.pages.dev"

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
            return text[:8000], soup
        return "", None
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return "", None

def rewrite_with_ai(title, link):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY kosong")
        return f"Berita selengkapnya bisa dibaca di {link}", None

    konten_asli, soup = ambil_konten_berita(link)
    if not konten_asli or len(konten_asli) < 100:
        return f"Berita selengkapnya bisa dibaca di {link}", soup

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
        return completion.choices[0].message.content, soup
    except Exception as e:
        print(f"Error AI: {e}")
        return konten_asli[:400] + "...", soup

def ambil_gambar(soup, url, slug):
    try:
        img_url = ""
        if soup:
            img = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'twitter:image'})
            if img:
                img_url = img.get('content', '')
            if not img_url:
                img_tag = soup.find('img')
                if img_tag:
                    img_url = img_tag.get('src', '')

        if img_url and img_url.startswith('//'):
            img_url = 'https:' + img_url
        if img_url and img_url.startswith('/'):
            img_url = url.rsplit('/', 1)[0] + img_url

        if img_url:
            ext = os.path.splitext(img_url.split('?')[0])[1]
            if not ext or len(ext) > 5:
                ext = '.jpg'
            filename = f"{slug}{ext}"
            filepath = os.path.join('images', filename)
            os.makedirs('images', exist_ok=True)
            r = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                return f"{BASE_URL}/images/{filename}"
    except Exception as e:
        print(f"Error download gambar: {e}")
    return f"{BASE_URL}/images/og-default.jpg"

def bikin_html_statis(slug, title, body, img_url, link_asli):
    summary = body[:160].replace('"', '&quot;')
    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - PULNEW</title>
<meta name="description" content="{summary}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{summary}">
<meta property="og:image" content="{img_url}">
<meta property="og:url" content="{BASE_URL}/berita/{slug}.html">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image">
<style>
body{{font-family:sans-serif;max-width:700px;margin:20px auto;padding:15px;line-height:1.7}}
h1{{font-size:24px;color:#1a237e}}
img{{width:100%;border-radius:8px;margin:15px 0}}
.btn{{display:inline-block;padding:10px 20px;background:#25D366;color:white;text-decoration:none;border-radius:6px;margin-top:15px}}
.btn-back{{background:#1565c0}}
</style>
</head>
<body>
<h1>{title}</h1>
<img src="{img_url}" alt="{title}">
<div>{body}</div>
<a class="btn" href="https://wa.me/?text=Baca%20di%20PULNEW:%20{BASE_URL}/berita/{slug}.html" target="_blank">Share ke WhatsApp</a>
<a class="btn btn-back" href="{BASE_URL}/">← Kembali ke Beranda</a>
</body>
</html>"""
    os.makedirs('berita', exist_ok=True)
    with open(f"berita/{slug}.html", "w", encoding="utf-8") as f:
        f.write(html)

# Sumber RSS - KODE LAMA LU GAK DIHAPUS
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
os.makedirs('images', exist_ok=True)

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
                body, soup_artikel = rewrite_with_ai(title, link)
                img_url = ambil_gambar(soup_artikel, link, slug)

                berita = {
                    "slug": slug,
                    "title": title,
                    "content": body[:200] + "...",
                    "body": body,
                    "image": img_url,
                    "kategori": "BERITA",
                    "date": datetime.now().isoformat()
                }

                # Simpan per file: public/posts/slug.json - KODE LAMA
                with open(f'public/posts/{slug}.json', 'w', encoding='utf-8') as f:
                    json.dump(berita, f, indent=2, ensure_ascii=False)

                # TAMBAHAN BARU: bikin file HTML statis buat WA
                bikin_html_statis(slug, title, body, img_url, link)

                slug_tercatat.add(slug)
                jumlah_baru += 1
                time.sleep(15)

            if jumlah_baru >= 5:
                break
    except Exception as e:
        print(f"Error pada {sumber['media']}: {e}")

print(f"Selesai! Nambah {jumlah_baru} berita baru")

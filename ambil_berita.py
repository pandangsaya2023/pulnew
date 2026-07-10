import os
import json
import re
import time
import requests
from datetime import datetime
from openai import OpenAI
from bs4 import BeautifulSoup

# --- KONFIGURASI ---
FILE_JSON = "posts.json" # BUAT WEBSITE
FOLDER_SVELTIA = "content/berita" # BUAT SVELTIA CMS
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
def baca_posts_lama():
    if os.path.exists(FILE_JSON):
        try:
            with open(FILE_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("posts", [])
        except:
            return []
    return []

def simpan_posts(daftar_berita):
    data = {"posts": daftar_berita}
    with open(FILE_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def bikin_file_sveltia(berita):
    """INI FUNGSI BARU BUAT SVELTIA"""
    os.makedirs(FOLDER_SVELTIA, exist_ok=True)
    file_path = f"{FOLDER_SVELTIA}/{berita['slug']}.md"

    frontmatter = f"""---
title: "{berita['title']}"
date: {berita['date']}
image: "{berita['image']}"
kategori: {berita['kategori']}
slug: {berita['slug']}
draft: false
---

{berita['body']}
"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    print(f" -> File Sveltia dibuat: {file_path}")

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
            return text[:5000], soup
        return "", None
    except: return "", None

def ambil_gambar_asli():
    return f"{BASE_URL}/media/og-default.png"

def rewrite_with_ai(title, link):
    api_key = os.getenv("GROQ_API_KEY")
    konten_asli, soup = ambil_konten_berita(link)

    if not api_key or not konten_asli or len(konten_asli) < 150:
        return f"Baca selengkapnya di sumber asli: {link}"

    try:
        client = OpenAI(api_key=api_key.strip(), base_url="https://api.groq.com/openai/v1")
        prompt = f"Paraphrase berita ini jadi 3 paragraf profesional bahasa Indonesia. Gaya jurnalistik. Jangan copy paste. Akhiri dengan 'Sumber: {link}'. JUDUL: {title}. ISI: {konten_asli[:3000]}"

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Gagal AI: {e}. Pake isi asli.")
        return konten_asli[:500] + f"... \n\nSumber: {link}"

def tentukan_kategori(title):
    title = title.lower()
    if any(x in title for x in ['politik', 'dpr', 'presiden', 'menteri']): return "POLITIK"
    if any(x in title for x in ['ekonomi', 'saham', 'rupiah', 'bisnis']): return "EKONOMI"
    if any(x in title for x in ['teknologi', 'ai', 'gadget', 'internet']): return "TEKNOLOGI"
    if any(x in title for x in ['bola', 'sepak', 'olahraga', 'piala']): return "OLAHRAGA"
    return "NASIONAL"

# --- EKSEKUSI UTAMA ---
print("Mulai ambil berita...")
daftar_lama = baca_posts_lama()
slug_tercatat = {b['slug'] for b in daftar_lama}
daftar_baru = []
jumlah_baru = 0

for sumber in sumber_rss:
    print(f"\nMengakses {sumber['media']}...")
    try:
        response = requests.get(sumber['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(response.content, 'xml')
        for item in soup.find_all('item')[:3]:
            title = item.find('title').get_text(strip=True)
            link = item.find('link').get_text(strip=True)
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60]
            if not slug: slug = f"berita-{int(time.time())}"

            if slug not in slug_tercatat:
                print(f" -> Nemu baru: {title[:50]}...")

                body = rewrite_with_ai(title, link)
                img_url = ambil_gambar_asli()
                kategori = tentukan_kategori(title)

                berita = {
                    "slug": slug,
                    "title": title,
                    "body": body,
                    "image": img_url,
                    "kategori": kategori,
                    "date": datetime.now().isoformat()
                }

                daftar_baru.append(berita)
                bikin_file_sveltia(berita) # <-- INI KUNCINYA: BIKIN FILE BUAT SVELTIA
                slug_tercatat.add(slug)
                jumlah_baru += 1
                time.sleep(8)

            if jumlah_baru >= 5: break
    except Exception as e:
        print(f"Error di {sumber['media']}: {e}")

semua_berita = daftar_baru + daftar_lama
semua_berita.sort(key=lambda x: x['date'], reverse=True)
semua_berita = semua_berita[:100]

simpan_posts(semua_berita)
print(f"\nSELESAI! Nambah {jumlah_baru} berita baru.")
print(f"1. Data Website: {FILE_JSON}")
print(f"2. Data Sveltia: {FOLDER_SVELTIA}/")

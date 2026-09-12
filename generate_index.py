0import os
import json
import markdown
from datetime import datetime

BASE_URL = "https://pulnew.pages.dev"
OUTPUT_FOLDER = "public/posts"
INDEX_JSON_PATH = "public/posts/index.json"
POSTS_JS_PATH = "public/posts.js"

def get_existing_posts():
    posts = {}
    if os.path.exists(OUTPUT_FOLDER):
        for filename in os.listdir(OUTPUT_FOLDER):
            if filename.endswith(".json") and filename != 'index.json':
                try:
                    path = os.path.join(OUTPUT_FOLDER, filename)
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    posts[data['slug']] = data
                except Exception as e: 
                    print(f"Gagal baca {filename}: {e}")
    return posts

def update_index_json(all_posts):
    sorted_posts = sorted(all_posts.values(), key=lambda x: x.get('date',''), reverse=True)
    index_data = []
    for p in sorted_posts:
        index_data.append({
            "slug": p['slug'],
            "title": p['title'],
            "lead": p.get('lead',''),
            "image": p.get('image',''),
            "date": p['date'],
            "kategori": p.get('kategori','Berita') # <-- NGIKUT SVELTIA
        })
    with open(INDEX_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    print(f"✅ index.json diupdate: {len(index_data)} berita")

def generate_article_page(article):
    os.makedirs("public/berita", exist_ok=True)
    body_html = markdown.markdown(article.get('body', ''), extensions=['extra'])
    
    desc = article.get('lead', '') or body_html[:160].replace('<','').replace('>','') + '...'
    url_lengkap = f"{BASE_URL}/berita/{article['slug']}.html"
    image_lengkap = article.get('image','') 
    if image_lengkap.startswith('/'):
        image_lengkap = BASE_URL + image_lengkap

    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{article['title']} - PULNEW.com</title>

<meta property="og:title" content="{article['title']}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{image_lengkap}">
<meta property="og:url" content="{url_lengkap}">
<meta property="og:type" content="article">

<style>

/* INI CSS KAMU DARI INDEX.HTML KUTIP SINI */



</style>
</head>
<body>
<div class="container">
<h1>{article['title']}</h1>
<p class="meta">{article['date']} | {article['kategori']}</p>
<img src="{image_lengkap}" alt="{article['title']}" class="featured-img">
<div class="article-content">{body_html}</div>
<a href="/" style="display:inline-block;margin-top:20px;color:var(--warna-biru);">← Kembali ke Beranda</a>
</div>
</body>
</html>"""
    with open(f"public/berita/{article['slug']}.html", 'w', encoding='utf-8') as f:
        f.write(html_content)

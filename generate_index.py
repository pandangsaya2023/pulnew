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

:root { --jarak-utama: 8px; --warna-merah: #d32f2f; --warna-biru: #1a237e; --warna-bg: #f4f6f9; }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif; }
        html, body { background: var(--warna-bg); color: #333; min-height: 100vh; padding-bottom: 10px; }
        h1, h2, h3, h4,.logo-text { font-family: 'Poppins', sans-serif; }
.header-container { background: #ffffff; position: sticky; top: 0; z-index: 999; border-bottom: 2px solid var(--warna-merah); box-shadow: 0 2px 4px rgba(0,0,0,0.06); width: 100%; }
.logo-bar { max-width: 1100px; margin: 0 auto; padding: 7px 20px; display: flex; justify-content: space-between; align-items: center; }
.logo-bar > a { display: inline-flex; align-items: center; gap: 10px; text-decoration: none; -webkit-tap-highlight-color: transparent; user-select: none; outline: none; }
.logo-img-wrapper img { display: block; max-height: 45px; width: auto; vertical-align: middle; }
.logo-text { font-size: 24px; font-weight: 800; color: var(--warna-biru); line-height: 1; }
.logo-new { color: var(--warna-merah); }
.btn-beranda { background: #2e7d32; color: white; padding: 4px 12px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 12px; transition: 0.2s; }
.btn-beranda:hover { background: #256d27; }
  .content-wrapper { padding: 0; }
  .article-box { max-width: 100%; margin: 0; background: white; padding: 16px; border-radius: 0; box-shadow: none; }
  .article-title { font-size: 24px; font-weight: 800; margin-bottom: 10px; line-height: 1.3; text-align: left; }
  .article-meta { font-size: 12px; color: #666; margin-bottom: 15px; text-align: left; }
  .main-image { width: 100%; border-radius: 8px; margin-bottom: 10px; }
   .share-article { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
   .share-article a,.share-article button { font-size: 10px; padding: 8px 12px; border-radius: 8px; color: white; text-decoration: none; display: flex; align-items: center; gap: 6px; border: none; cursor: pointer; font-weight: 600; transition: 0.2s; }
   .share-article a:hover,.share-article button:hover { opacity: 0.9; transform: translateY(-1px); }
   .share-wa { background: #25D366; }
   .share-fb { background: #1877F2; }
   .share-x { background: #000; }
   .share-copy { background: #1a237e; }
  .article-body { font-size: 16px; line-height: 1.3; color: #333; text-align: left; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; white-space: pre-line; }
  .article-body p { margin-bottom: 0.3em; }
  .article-body h2 { font-size: 20px; font-weight: 700; line-height: 1.3!important; color: var(--warna-biru); margin-top: 15px!important; display: block!important; }
  .article-body img { max-width: 100%; height: auto; border-radius: 8px; margin: 15px 0; }
  .article-body a { color: var(--warna-merah); text-decoration: underline; }
  .source-box { margin: 15px 0 20px 0; padding: 0; border-top: none; font-size: 14px; color: #555; font-style: italic; }
  .source-box a { color: var(--warna-biru); text-decoration: none; font-weight: 600; }
  .source-box a:hover { text-decoration: underline; }
  .related-section { margin-top: 30px; padding-top: 20px; border-top: 2px solid #eee; }
  .section-title { font-size: 18px; font-weight: 800; color: var(--warna-biru); margin: 5px 0 12px 0; padding-left: 3px; border-left: 4px solid var(--warna-merah); text-align: left; }
  .related-item { display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f0f0f0; text-decoration: none; color: inherit; transition: 0.2s; }
  .related-item:hover { background: #f9f9f9; }
  .related-item img { width: 90px; height: 60px; object-fit: cover; border-radius: 6px; flex-shrink: 0; }
  .related-item h4 { font-size: 14px; font-weight: 700; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin: 0; text-align: left; }
  .footer-ticker { background: #d32f2f; color: white; padding: 8px 0; font-size: 13px; overflow: hidden; width: 100%; position: fixed; bottom: 0; left: 0; z-index: 999; height: 35px; display: flex; align-items: center; }
  .ticker-content { display: inline-block; white-space: nowrap; padding-left: 100%; animation: ticker 40s linear infinite; line-height: 35px; }
        @keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); }
  .loading,.error { text-align:center; padding:60px 20px; }
  .error { color: var(--warna-merah); }
    .sticky-video-wrapper { position: fixed!important; bottom: 100px!important; right: 20px!important; width: 320px!important; height: 180px!important; z-index: 998!important; background: #000; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 25px rgba(0,0,0,0.4); }
  .video-container { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; margin: 0 auto; }
  .video-container iframe,.video-container #youtube-player { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }
    #close-video { display: none; }
    @media (max-width: 767px) {
 .sticky-video-wrapper { position: relative!important; width: 95%!important; height: auto!important; margin: 25px auto!important; bottom: auto!important; right: auto!important; }
   #close-video { display: block; position: absolute; top: 5px; right: 8px; background: rgba(0,0,0,0.6); color: white; border: none; border-radius: 50%; width: 28px; height: 28px; cursor: pointer; z-index: 10; }
    }
    .article-box { padding-bottom: 50px!important; }
    @media (max-width: 767px) { .article-box { padding-bottom: 16px!important; } }

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

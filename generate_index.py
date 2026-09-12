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

:root { --jarak-utama: 12px; --warna-merah: #d32f2f; --warna-biru: #1a237e; --warna-bg: #f4f6f9; }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif; }
        html, body { background: var(--warna-bg); color: #333; min-height: 100vh; }
        h1, h2, h3, h4,.logo-text { font-family: 'Poppins', sans-serif; }
     .header-container { background: #ffffff; position: sticky; top: 0; z-index: 200; border-bottom: 2px solid var(--warna-merah); box-shadow: 0 2px 4px rgba(0,0,0,0.06); }
     .category-nav { display: flex; gap: 8px; overflow-x: auto; padding: 5px 10px; background: var(--warna-biru); border-bottom: 1px solid #eee; position: sticky; top: 55px; z-index: 100; scrollbar-width: none; }
     .category-nav::-webkit-scrollbar { display: none; }
     .category-nav a { padding: 4.5px 9px; background: #1a237e; border-radius: 10px; font-size: 10px; font-weight: 600; color: white; text-decoration: none; white-space: nowrap; transition: 0.2s; }
     .category-nav a:hover,.category-nav a.active { background: #d32f2f; color: white; }
     .logo-bar { max-width: 1100px; margin: 0 auto; padding: 7px 20px; display: flex; justify-content: space-between; align-items: center; }
     .logo-bar > a { display: inline-flex; align-items: center; gap: 10px; text-decoration: none; }
     .logo-img-wrapper img { display: block; max-height: 45px; width: auto; }
     .logo-text { font-size: 24px; font-weight: 800; color: var(--warna-biru); }
     .logo-new { color: var(--warna-merah); }
     .top-header {
            background: var(--warna-biru); color: white; padding: 6px 12px;
            display: flex; align-items: center; gap: 10px; font-size: 11px;
            position: sticky; top: 60px; z-index: 199;
        }
     .breaking-badge {
            background: var(--warna-biru); color: white; padding: 0 8px;
            border-radius: 8px; font-weight: 700; font-size: 10px; flex-shrink: 0;
        }
     .ticker-wrapper { overflow: hidden; width: 100%; }
     .ticker-content {
            display: inline-block; white-space: nowrap; padding-left: 100%;
            animation: ticker 120s linear infinite;
        }
     .ticker-item {
            display: inline-block; padding-right: 40px; font-weight: 500;
            color: white; text-decoration: none;
        }
        @keyframes ticker {
            0% { transform: translate3d(0, 0, 0); }
            100% { transform: translate3d(-100%, 0, 0); }
        }

     .container { max-width: 1100px; width: 100%; margin: 0 auto; padding: var(--jarak-utama) 10px; }

      /* === TAMBAHAN BARU: SEARCH BOX === */
     .search-box { margin: 10px 0 10px 0; }
     .search-box input { width:100%; padding:12px 16px; border:2px solid #ddd; border-radius:12px; font-size:14px; outline:none; transition:0.2s; }
     .search-box input:focus { border-color: var(--warna-biru); box-shadow: 0 0 0 3px rgba(26,35,126,0.1); }

      /* === TAMBAHAN BARU: PAGINASI === */
     .pagination { display:flex; justify-content:center; gap:8px; margin-bottom: 10px !important; margin-top: 20px; flex-wrap:wrap; }
     .pagination button { padding:8px 14px; border:1px solid #ddd; background:white; border-radius:8px; cursor:pointer; font-weight:600; font-size:13px; transition:0.2s; }
     .pagination button:hover { background:var(--warna-biru); color:white; border-color:var(--warna-biru); }
     .pagination button.active { background:var(--warna-merah); color:white; border-color:var(--warna-merah); }
     .pagination button:disabled { opacity:0.5; cursor:not-allowed; }

     .news-hero { position: relative; border-radius: 12px; overflow: hidden; margin-bottom: var(--jarak-utama); box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-decoration: none; display: block; }
     .news-hero img { width: 100%; height: 240px; object-fit: cover; display: block; }
     .hero-content { position: absolute; bottom: 0; left: 0; right: 0; padding: 20px 16px; background: linear-gradient(transparent, rgba(0,0,0,0.85)); color: white; }
     .news-hero h2 { font-size: 15px; font-weight: 700; line-height: 1.3; color: white; padding: 4px 0 8px 0; }
     .badge { display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-bottom: 10px; background: var(--warna-merah); color: white; }
     .news-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--jarak-utama); margin-bottom: var(--jarak-utama); }
     .news-card { background: white; display: flex; flex-direction: column; text-decoration: none; color: inherit; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); transition: transform 0.2s; }
     .news-card:hover { transform: translateY(-3px); }
     .news-card img { width: 100%; height: 180px; object-fit: cover; }
     .card-content { padding: 12px 14px 16px 14px; }
     .news-card h3 { font-size: 15px; font-weight: 700; line-height: 1.4; color: #111; padding: 2px 0 8px 0; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
     .section-title { font-size: 18px; font-weight: 800; color: var(--warna-biru); margin: 22px 0 15px 0; padding-left: 3px; border-left: 4px solid var(--warna-merah); }

      .latest-carousel { position: relative; margin: 1px 0px 1px 0px; overflow: hidden; }
     .carousel-scroll { display: flex; gap: 12px; overflow-x: auto; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; padding-bottom: 8px; scrollbar-width: none; }
     .carousel-scroll::-webkit-scrollbar { display: none; }
     .carousel-item { flex: 0 0 80%; max-width: 500px; scroll-snap-align: start; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-decoration: none; color: inherit; display: flex; flex-direction: row; gap: 12px; padding: 10px; }
     .carousel-item img { width: 40%; height: 120px; object-fit: cover; flex-shrink: 0; border-radius: 8px; }
     .carousel-item.card-content { padding: 0px; display: flex; flex-direction: column; justify-content: center; flex: 1; gap: 6px; }
     .carousel-item h4 { font-size: 15px; font-weight: 700; line-height: 1.4; color: #111; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
       @media (min-width: 768px) {.news-hero img { height: 320px; }.news-hero h2 { font-size: 26px; }.carousel-item { flex: 0 0 60%; } }
        @media (max-width: 600px) {.news-grid { grid-template-columns: 1fr; } }
        footer { background: #101726; color: #b0b8c4; padding: 12px 20px 20px 20px; font-size: 13px; border-top: 4px solid var(--warna-biru); margin-top: 5px; }
     .footer-content { max-width: 1100px; margin: 0 auto; text-align: center; }
     .footer-logo { font-size: 20px; font-weight: 800; color: white; margin-bottom: 4px; }
     .footer-logo span { color: var(--warna-merah); }
     .footer-bottom { border-top: 1px solid #1e293b; padding-top: 8px; margin-top: 10px; font-size: 11px; color: #64748b; }
     .footer-link { color: #64748b; font-size: 10.5px; text-decoration: none; margin: 0 4px; }
     .ad-slot { margin: 10px auto; padding: 0; text-align: center; }
     .ad-slot img { width: 100%; height: auto; display: block; border-radius: 8px; }
     .ad-slot.ad-banner-bottom { margin: 5px auto 0px auto!important; padding: 0px!important; max-width: 768px; }
     .ad-slot.ad-banner-bottom img { width: 100%; height: auto; aspect-ratio: 768 / 180; object-fit: contain; display: block; border-radius: 12px; background: #f0f0f0; }
     .ad-slot.ad-banner-bottom:has(img[src=""], img:not([src])) { display: none!important; margin: 0px!important; }
      footer { margin-top: 5px!important; }
     .ad-inarticle { max-width: 600px; }
        @media (max-width: 768px) {.ad-banner-top,.ad-banner-bottom { max-width: 100%; } }*/
    /* .video-container { position: sticky; /*relative;*/ padding-bottom: 56.25%; height: 0; /*overflow: hidden;*/ max-width: 100%; }*/
    /* .video-container iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }*/
        /* === FIX ISI BERITA === */
    .berita-body, .isi-berita, .content, .prose {
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
        line-height: 1.8;
        font-size: 16px;
     }
     .berita-body p, .isi-berita p, .content p, .prose p {
        margin-bottom: 1em;
     }
     .berita-body img, .isi-berita img, .content img {
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        margin: 10px 0;
     }
    .berita-body h2, .isi-berita h2 {
        font-size: 20px;
        margin: 20px 0 10px 0;
        color: var(--warna-biru);
     }

    .sticky-video-wrapper {
        position: sticky;
        top: 105px;
        z-index: 50;
        background: #000;
        transition: 0.3s;
        width: 100%;
        margin: 20px 0; /* kasih jarak atas bawah */
    }
    .sticky-video-wrapper.minimized {
        position: fixed !important;
        bottom: 20px !important;
        right: 20px !important;
        top: auto !important;
        max-width: 320px !important;
        width: 320px !important;
        height: 180px !important;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        z-index: 9999 !important;
        transition: all 0.3s ease;
    }
    /* ANTI BUG: KALAU ADA SCRIPT NAMBAH CLASS LAIN */
    .sticky-video-wrapper.minimized iframe {
        width: 100% !important;
        height: 100% !important;
    }

    /* RASIO 16:9 */
    .video-container { 
        position: relative; 
        padding-bottom: 56.25%;
        height: 0; 
        overflow: hidden; 
        max-width: 100%; 
        margin: 0 auto; /* biar di tengah */
    }
    .video-container iframe, .video-container #youtube-player { 
        position: absolute; 
        top: 0; 
        left: 0;
        width: 100%; 
        height: 100%; 
        border: none; 
    }
    #close-video { display: none; } /* sembunyiin tombol X di desktop */


    /* ===== KHUSUS HP ===== */
    @media (max-width: 767px) {
   /* MATIIN MODE MINIMIZED DI HP */
   .sticky-video-wrapper.minimized {
        position: relative !important; /* jangan fixed lagi */
        bottom: auto !important;
        left: auto !important;
        width: 100% !important;
        max-width: 100% !important;
        aspect-ratio: 16/9;
        margin: 30px auto !important; /* kasih jarak */
        border-radius: 0;
        box-shadow: none;
   }
   
   /* POSISI PLAYER: TENGAH BAWAH SEBELUM FOOTER */
   .sticky-video-wrapper {
        width: 95%; /* jangan full biar ada margin */
        margin: 10px auto; /* auto = di tengah */
        position: relative !important;
        top: auto !important;
   }

   /* TAMPILIN TOMBOL CLOSE DI HP */
   #close-video { 
        display: block;
        position: absolute;
        top: 5px;
        right: 8px;
        background: rgba(0,0,0,0.6);
        color: white;
        border: none;
        border-radius: 50%;
        width: 28px;
        height: 28px;
        cursor: pointer;
        z-index: 10;
      }
     }

    /* IKLAN BERANDA */
    .iklan-beranda {
        max-width: 1200px;
        margin: 25px auto; /* Tengah + ada jarak atas bawah */
        padding: 0 15px;
        text-align: center;
        position: relative;
        z-index: 10;
    }

    .iklan-beranda .iklan-label {
        font-size: 11px;
        color: #777;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }

    .iklan-beranda img {
        width: 100%;
        max-width: 900px; /* Pas di desktop */
        height: auto;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15); /* Biar nimbul dikit */
        transition: transform 0.3s ease;
    }

    .iklan-beranda img:hover {
        transform: scale(1.02); /* Efek pas dihover */
    }

    /* VERSI HP */
    @media (max-width: 767px) {
        .iklan-beranda {
            margin: 20px 0;
            padding: 0 10px;
        }
        .iklan-beranda img {
            max-width: 100%;
            border-radius: 0; /* Full di HP */
        }
    }
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

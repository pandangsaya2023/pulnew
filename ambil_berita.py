import feedparser, requests, os, json, re, yaml
from datetime import datetime
from bs4 import BeautifulSoup
import markdown

CONFIG_FILE = 'config.yml'

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text

def update_posts_js():
    posts_dir = 'public/posts'
    posts = []
    for filename in sorted(os.listdir(posts_dir), reverse=True):
        if filename.endswith('.json'):
            with open(os.path.join(posts_dir, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['slug'] = filename.replace('.json', '')
                posts.append(data)
    with open('public/posts.js', 'w', encoding='utf-8') as f:
        f.write('const postsData = ' + json.dumps(posts, ensure_ascii=False, indent=2) + ';')

def generate_article_page(article):
    # INI KUNCINYA: convert markdown body jadi HTML
    body_html = markdown.markdown(article.get('body', ''), extensions=['extra'])
    
    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>{article['title']} - PULNEW</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<div class="container">
<h1>{article['title']}</h1>
<p class="meta">{article['date']} | {article['kategori']}</p>
<img src="{article.get('image','')}" alt="{article['title']}" class="featured-img">
<div class="article-content">
{body_html}
</div>
<p class="source">Sumber: <a href="{article.get('source_url','#')}">{article.get('source_name','')}</a></p>
</div>
</body>
</html>"""
    with open(f"public/berita/{article['slug']}.html", 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    config = load_config()
    # ... bagian ambil RSS tetap sama ...
    
    # TAMBAHKAN INI DI AKHIR, SETELAH SIMPAN JSON
    update_posts_js()
    
    # GENERATE ULANG SEMUA HALAMAN BERITA DARI JSON
    for filename in os.listdir('public/posts'):
        if filename.endswith('.json'):
            with open(f"public/posts/{filename}", 'r', encoding='utf-8') as f:
                article = json.load(f)
                article['slug'] = filename.replace('.json','')
                generate_article_page(article)
    print("Selesai generate semua halaman")

if __name__ == "__main__":
    main()

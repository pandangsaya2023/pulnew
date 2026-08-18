import feedparser
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
import json
import re
from datetime import datetime

# 1. KONEK KE GEMINI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY tidak ditemukan")
    
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. SUMBER RSS
RSS_URLS = [
    "https://www.republika.co.id/rss",
    "https://www.kompas.com/rss"
]

def ambil_konten(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, timeout=15, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        paragraf = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 80]
        return "\n".join(paragraf[:6])
    except Exception as e:
        print(f"Gagal ambil konten: {e}")
        return ""

def rewrite_dengan_gemini(judul, konten):
    prompt = f"""
    Kamu adalah jurnalis dan SEO writer untuk pulnew.pages.dev
    Tulis ulang berita di bawah ini 100% dengan kata2 baru. Jangan plagiat.
    Buat judul baru yg clickbait tapi tetap fakta. Isi 300-400 kata.
    Gunakan gaya bahasa santai, mudah dipahami. Akhiri dengan kesimpulan.

    JUDUL ASLI: {judul}
    ISI ASLI: {konten}

    Balas HANYA dalam format JSON valid:
    {{"judul_baru": "...", "isi_baru": "..."}}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"Error Gemini: {e}")
        return None # INI PENTING: KALAU ERROR MAKA SKIP

def main():
    semua_berita = []
    for rss in RSS_URLS:
        feed = feedparser.parse(rss)
        for entry in feed.entries[:8]: # Ambil 8 berita terbaru
            print(f"Memproses: {entry.title}")
            konten = ambil_konten(entry.link)
            if len(konten) < 200: continue
            
            hasil_ai = rewrite_dengan_gemini(entry.title, konten)
            
            if hasil_ai: # HANYA SIMPAN KALAU AI SUKSES
                semua_berita.append({
                    "id": re.sub(r'\W+', '-', entry.title.lower())[:50],
                    "judul": hasil_ai["judul_baru"],
                    "isi": hasil_ai["isi_baru"],
                    "sumber": entry.link,
                    "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                print("Skip berita ini karena AI error")
    
    # 3. SIMPAN KE posts.js
    output = "const posts = " + json.dumps(semua_berita, ensure_ascii=False, indent=2) + ";"
    with open("public/posts.js", "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Selesai! {len(semua_berita)} berita baru berhasil dibuat.")

if __name__ == "__main__":
    main()

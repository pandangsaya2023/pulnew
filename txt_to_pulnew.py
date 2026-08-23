import json
from datetime import datetime

# 1. GANTI INI SESUAI FILE KAMU
file_txt = "My Love(MP3_128K).mp3.txt"
file_output = "my-love-oscar.json"

# 2. GANTI INI SESUAI BERITA KAMU
judul = "Lirik Lagu You Are My Love - Oscar Harris"
slug = "lirik-lagu-you-are-my-love-oscar-harris"
kategori = "MUSIK"
gambar = "/media/my-love-oscar.jpg"
source_name = "Transkrip Whisper AI"
source_url = ""

# Baca file txt hasil whisper
with open(file_txt, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Bersihin: hapus timestamp, [music], baris kosong
teks_bersih = []
for line in lines:
    line = line.strip()
    # Hapus baris timestamp [00:00:21.000 --> 00:00:23.000]
    if line.startswith("[") and "-->" in line:
        line = line.split("] ", 1)[-1]
    if line and "[music]" not in line.lower() and "[BLANK_AUDIO]" not in line:
        teks_bersih.append(line)

# Gabung jadi 1 untuk "teks" dan "body"
teks_full = "\n".join(teks_bersih)
body_html = f"<strong>PULNEW.COM</strong> - Berikut lirik lagu 'You Are My Love' dari Oscar Harris yang berhasil ditranskrip dari audio.<br><br>" + teks_full.replace("\n", "<br>")

# Bikin format JSON sesuai web pulnew
data = {
    "title": judul,
    "slug": slug,
    "kategori": kategori,
    "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
    "image": gambar,
    "body": body_html,
    "source_name": source_name,
    "source_url": source_url,
    "teks": teks_full
}

# Simpan ke file json
with open(file_output, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Selesai! File {file_output} sudah dibuat")
print(f"Tinggal copy ke ~/pulnew/posts/ terus git push")

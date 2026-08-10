import json
import os

FOLDER_POSTS = "public/posts"
jumlah = 0

print("Mulai bersihin sumber dari semua .json...")

for filename in os.listdir(FOLDER_POSTS):
    if filename.endswith(".json"):
        path_file = os.path.join(FOLDER_POSTS, filename)
        
        try:
            # 1. Buka dan baca file
            with open(path_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 2. Hapus kuncinya kalau ada
            if 'source_name' in data:
                del data['source_name']
            if 'source_url' in data:
                del data['source_url']
            
            # 3. Simpan lagi, timpa file lama
            with open(path_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            jumlah += 1
            print(f"✅ Bersih: {filename}")

        except Exception as e:
            print(f"❌ Gagal {filename}: {e}")

print(f"\nSelesai! Total {jumlah} file sudah dibersihkan.")

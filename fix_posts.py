import json

with open("posts.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for post in data["posts"]:
    if "body" not in post and "content" in post:
        post["body"] = post["content"]

with open("posts.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Selesai. Semua post sekarang punya field body.")

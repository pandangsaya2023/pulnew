export async function onRequest(context) {
  const { env } = context;
  
  // Ambil semua file .json dari folder public/posts
  const assets = await env.ASSETS.fetch(new Request('https://dummy.com/public/posts/'));
  // Cara gampang: kalau repo public, kita pakai GitHub API
  const res = await fetch('https://api.github.com/repos/pandangsaya2023/pulnew/contents/public/posts', {
    headers: { 'User-Agent': 'pulnew' }
  });
  
  const files = await res.json();
  
  // Ambil isi semua file .json
  const posts = [];
  for (const file of files) {
    if (file.name.endsWith('.json')) {
      const fileRes = await fetch(file.download_url);
      const data = await fileRes.json();
      posts.push(data);
    }
  }
  
  // Urut dari terbaru
  posts.sort((a, b) => new Date(b.date) - new Date(a.date));
  
  return new Response(JSON.stringify({ posts }), {
    headers: { 'Content-Type': 'application/json' }
  });
}

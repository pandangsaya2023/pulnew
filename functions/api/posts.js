export async function onRequest() {
  try {
    // Ambil daftar file dari GitHub API
    const githubRes = await fetch(
      'https://api.github.com/repos/pandangsaya2023/pulnew/contents/public/posts',
      { headers: { 'User-Agent': 'pulnew-site' } }
    );
    
    if (!githubRes.ok) throw new Error('Gagal ambil daftar file');
    
    const files = await githubRes.json();
    
    const posts = [];
    
    for (const file of files) {
      if (file.name.endsWith('.json')) {
        const fileRes = await fetch(file.download_url);
        if (fileRes.ok) {
          const data = await fileRes.json();
          posts.push(data);
        }
      }
    }
    
    // Urut dari terbaru
    posts.sort((a, b) => new Date(b.date) - new Date(a.date));
    
    return new Response(JSON.stringify({ posts }), {
      headers: { 
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache' 
      }
    });
    
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message, posts: [] }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

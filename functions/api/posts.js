export async function onRequest() {
  try {
    // Ambil daftar file JSON dari GitHub
    const githubRes = await fetch(
      'https://api.github.com/repos/pandangsaya2023/pulnew/contents/public/posts',
      { 
        headers: { 
          'User-Agent': 'pulnew-site',
          'Accept': 'application/vnd.github.v3+json'
        },
        // Suruh Cloudflare cache hasil ini 60 detik biar gak nembak GitHub terus
        cf: { 
          cacheTtl: 60, 
          cacheEverything: true 
        }
      }
    );
    
    // Kalau GitHub balikin error 403 rate limit atau 404, jangan crash
    if (!githubRes.ok) {
      console.error('GitHub API error:', githubRes.status, githubRes.statusText);
      return new Response(JSON.stringify({ 
        urls: [], 
        error: `GitHub ${githubRes.status}` 
      }), {
        status: 200, // PENTING: jangan 500 biar frontend gak merah
        headers: { 
          'Content-Type': 'application/json',
          'Cache-Control': 'public, max-age=60' // cache 1 menit
        }
      });
    }
    
    const files = await githubRes.json();
    
    // Filter cuma file .json dan ambil download_url nya
    const urls = Array.isArray(files) 
      ? files
          .filter(f => f.name && f.name.endsWith('.json'))
          .map(f => f.download_url)
          .slice(0, 50) // batasi 50 berita terbaru biar ringan
      : [];

    return new Response(JSON.stringify({ urls }), {
      status: 200,
      headers: { 
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=60' // browser + CF cache 1 menit
      }
    });
    
  } catch (err) {
    console.error('Function error:', err);
    // Kalau error apapun, balikin 200 + urls kosong, jangan 500
    return new Response(JSON.stringify({ 
      urls: [], 
      error: err.message 
    }), {
      status: 200,
      headers: { 
        'Content-Type': 'application/json', 
        'Cache-Control': 'public, max-age=60' 
      }
    });
  }
}

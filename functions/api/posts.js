export async function onRequest() {
  try {
    // KUNCI: Tambahin ?t=timestamp biar gak kena cache github
    const apiUrl = `https://api.github.com/repos/pandangsaya2023/pulnew/contents/public/posts?t=${Date.now()}`;
    
    const githubRes = await fetch(apiUrl, {
      headers: {
        'User-Agent': 'pulnew-site',
        'Accept': 'application/vnd.github.v3+json',
        'Cache-Control': 'no-cache' // paksa gak cache
      },
      cf: {
        cacheTtl: 0, // JANGAN DI CACHE CLOUDFLARE
        cacheEverything: false
      }
    });

    if (!githubRes.ok) {
      return new Response(JSON.stringify({ urls: [] }), { status: 200 });
    }

    const files = await githubRes.json();
    const urls = Array.isArray(files)
      ? files.filter(f => f.name && f.name.endsWith('.json'))
             .map(f => `/posts/${f.name}`) // langsung bikin url lokal, jangan download_url
             .slice(0, 50)
      : [];

    return new Response(JSON.stringify({ urls }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store, max-age=0' // paksa browser gak cache
      }
    });
  } catch (err) {
    return new Response(JSON.stringify({ urls: [] }), { status: 200 });
  }
}

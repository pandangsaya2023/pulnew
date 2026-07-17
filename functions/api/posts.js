export async function onRequest() {
  try {
    const timestamp = Date.now();
    const githubRes = await fetch(
      `https://api.github.com/repos/pandangsaya2023/pulnew/contents/public/posts?ref=main&ts=${timestamp}`,
      {
        headers: {
          'User-Agent': 'pulnew-site',
          'Accept': 'application/vnd.github.v3+json'
        },
        cf: { cacheTtl: 0, cacheEverything: false }
      }
    );

    if (!githubRes.ok) return new Response(JSON.stringify({urls: []}), {status: 200});

    const files = await githubRes.json();
    const urls = Array.isArray(files)
      ? files.filter(f => f.name.endsWith('.json'))
             .map(f => `/posts/${f.name}`)
             .sort().reverse() // urutin dari terbaru
      : []; // INI UDAH GAK PAKE .slice(0, 50) LAGI

    return new Response(JSON.stringify({urls}), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  } catch {
    return new Response(JSON.stringify({urls: []}), {status: 200});
  }
}

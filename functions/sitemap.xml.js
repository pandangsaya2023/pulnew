export async function onRequest(context) {
  const baseUrl = 'https://pulnew.pages.dev';

  // LANGSUNG PANGGIL GITHUB API DI SINI. GAK PAKE FETCH /api/posts LAGI
  const githubApiUrl = 'https://api.github.com/pandangsaya2023/pulnew/public/posts';

  try {
    const res = await fetch(githubApiUrl, {
      headers: { 'User-Agent': 'Cloudflare-Pages' }
    });
    const files = await res.json();

    // Ambil nama file.json doang
    const posts = files
     .filter(file => file.name.endsWith('.json'))
     .map(file => file.name.replace('.json', ''));

    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>${baseUrl}/</loc><priority>1.0</priority></url>
  ${posts.map(slug => `
  <url>
    <loc>${baseUrl}/berita/${slug}</loc>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
    <priority>0.8</priority>
  </url>`).join('')}
</urlset>`;

    return new Response(xml, { headers: { 'Content-Type': 'application/xml' } });

  } catch (e) {
    return new Response('Error: ' + e.message, { status: 500 });
  }
}

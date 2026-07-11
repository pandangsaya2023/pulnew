export async function onRequest(context) {
  const baseUrl = 'https://pulnew.pages.dev';

  // 1. Panggil API posts.js yg udah ada
  const res = await fetch(new URL('/api/posts', baseUrl));
  const downloadUrls = await res.json(); // isinya array url

  // 2. Ubah jadi slug
  const posts = downloadUrls.map(url => {
    const slug = url.split('/').pop().replace('.json', '');
    return { slug };
  });

  // 3. Buat XML
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>${baseUrl}/</loc><priority>1.0</priority></url>
  ${posts.map(p => `
  <url>
    <loc>${baseUrl}/berita/${p.slug}</loc>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>`).join('')}
</urlset>`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml',
      'Cache-Control': 'public, max-age=3600'
    }
  });
}

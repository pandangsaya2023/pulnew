export async function onRequest() {
  const baseUrl = 'https://pulnew.pages.dev';

  // 1. Ambil data dari API posts.js yg udah kamu buat
  const res = await fetch(baseUrl + '/api/posts');
  const data = await res.json(); // isinya array download_url

  // 2. Ubah download_url jadi slug + date
  const posts = data.map(url => {
    const slug = url.split('/').pop().replace('.json', '');
    return { slug: slug, date: new Date().toISOString().split('T')[0] };
  });

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>${baseUrl}/</loc><priority>1.0</priority></url>
  ${posts.map(p => `
  <url>
    <loc>${baseUrl}/berita/${p.slug}</loc>
    <lastmod>${p.date}</lastmod>
    <priority>0.8</priority>
  </url>`).join('')}
</urlset>`;

  return new Response(xml, { headers: { 'Content-Type': 'application/xml' } });
}

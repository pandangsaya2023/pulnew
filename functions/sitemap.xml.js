export async function onRequest(context) {
  const baseUrl = 'https://pulnew.pages.dev';
  const { env } = context;

  // Ambil list file dari folder /public/posts/
  const postsDir = await env.ASSETS.fetch(new Request(baseUrl + '/posts/'));
  const files = await postsDir.text();

  // Ambil semua nama file.json dari hasil HTML folder
  const slugs = [...files.matchAll(/href="(.+?)\.json"/g)].map(m => m[1]);

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>${baseUrl}/</loc><priority>1.0</priority></url>
  ${slugs.map(slug => `
  <url>
    <loc>${baseUrl}/berita/${slug}</loc>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
    <priority>0.8</priority>
  </url>`).join('')}
</urlset>`;

  return new Response(xml, { headers: { 'Content-Type': 'application/xml' } });
}

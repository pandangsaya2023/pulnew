export async function onRequest() {
  try {
    // Ambil daftar URL berita dari API lu
    const res = await fetch('https://pulnew.pages.dev/api/posts');
    const data = await res.json();
    const urls = Array.isArray(data) ? data : data.urls || [];

    // Ambil data lengkap 50 berita terbaru
    const posts = await Promise.all(
      urls.slice(0, 50).map(url => fetch(url).then(r => r.json()))
    );

    // Urutkan dari yang terbaru
    posts.sort((a, b) => new Date(b.date || b.created_at) - new Date(a.date || a.created_at));

    // Generate XML
    let xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://pulnew.pages.dev/</loc>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>`;

    posts.forEach(post => {
      const lastmod = new Date(post.date || post.created_at).toISOString().split('T')[0];
      xml += `
  <url>
    <loc>https://pulnew.pages.dev/berita.html?slug=${post.slug}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>`;
    });

    xml += '\n</urlset>';

    return new Response(xml, {
      headers: {
        'Content-Type': 'application/xml',
        'Cache-Control': 'no-cache'
      }
    });

  } catch (err) {
    return new Response('<?xml version="1.0"?><urlset></urlset>', {
      headers: { 'Content-Type': 'application/xml' }
    });
  }
}

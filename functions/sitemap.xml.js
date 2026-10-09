export async function onRequest(context) {
  const baseUrl = 'https://pulnew.pages.dev';
  const githubApiUrl = 'https://api.github.com/repos/pandangsaya2023/pulnew/contents/public/posts';
  
  // Mengambil token dari Environment Variables Cloudflare
  const token = context.env.GITHUB_TOKEN;

  try {
    const headers = { 
      'User-Agent': 'Cloudflare-Pages'
    };

    // Menyertakan token ke header jika tersedia
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(githubApiUrl, { headers });

    if (!res.ok) {
      throw new Error(`GitHub API error: ${res.status}`);
    }

    const files = await res.json();

    // PENTING: Pastikan dia array dulu
    if (!Array.isArray(files)) {
      throw new Error('GitHub did not return an array');
    }

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
    // Kalau error, kasih sitemap minimal biar Google gak marah
    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>${baseUrl}/</loc></url>
</urlset>`;
    return new Response(xml, { headers: { 'Content-Type': 'application/xml' } });
  }
}


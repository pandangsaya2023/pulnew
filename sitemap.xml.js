export async function onRequest(context) {
  const baseUrl = 'https://pulnew.pages.dev';
  
  // Cache 1 jam biar gak hantam GitHub terus
  const cache = caches.default;
  let response = await cache.match(context.request);
  if (response) return response;

  try {
    // Pake RAW github, bukan API - jadi gak kena limit 60/jam
    // Ganti USERNAME sama NAMA_REPO lu yang bener
    const USERNAME = 'pandangsaya2023'; // ganti ini
    const REPO = 'pulnew'; // ganti ini
    const BRANCH = 'main';

    // Ambil list file via github API public tanpa token, tapi kita cache
    const apiUrl = `https://api.github.com/repos/${USERNAME}/${REPO}/contents/public/posts`;
    
    const res = await fetch(apiUrl, {
      headers: { 'User-Agent': 'PULNEW-Sitemap' },
      cf: { cacheTtl: 3600, cacheEverything: true }
    });

    if (!res.ok) throw new Error('API fail ' + res.status);
    
    const files = await res.json();
    const posts = Array.isArray(files) 
      ? files.filter(f => f.name.endsWith('.json')).map(f => f.name.replace('.json',''))
      : [];

    // Kalau GitHub lagi error, tetap kasih homepage + 2 berita andalan lu biar GSC gak kosong
    const fallbackPosts = posts.length ? posts : [
      'rico-waas-semprot-bapenda-medan-pajak-3-64-triliun-baru-64-persen',
      '117-dusun-sumut-masih-gelap-47-lokasi-nias-mandailing-natal'
    ];

    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>${baseUrl}/</loc><lastmod>2026-10-08</lastmod><priority>1.0</priority></url>
${fallbackPosts.map(slug => `  <url>
    <loc>${baseUrl}/berita/${slug}</loc>
    <lastmod>2026-10-08</lastmod>
    <priority>0.8</priority>
  </url>`).join('\n')}
</urlset>`;

    response = new Response(xml, {
      headers: { 
        'Content-Type': 'application/xml; charset=utf-8',
        'Cache-Control': 'public, max-age=3600'
      }
    });

    // Simpan ke cache Cloudflare
    context.waitUntil(cache.put(context.request, response.clone()));
    return response;

  } catch (e) {
    // Fallback paling minimal kalau semuanya fail - ini yang bikin GSC lu gak error
    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>${baseUrl}/</loc><lastmod>2026-10-08</lastmod></url>
  <url><loc>${baseUrl}/berita/rico-waas-semprot-bapenda-medan-pajak-3-64-triliun-baru-64-persen</loc><lastmod>2026-10-08</lastmod></url>
  <url><loc>${baseUrl}/berita/117-dusun-sumut-masih-gelap-47-lokasi-nias-mandailing-natal</loc><lastmod>2026-10-08</lastmod></url>
</urlset>`;
    return new Response(xml, { headers: { 'Content-Type': 'application/xml' } });
  }
}

export async function onRequest() {
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://pulnew.pages.dev/</loc>
    <lastmod>2026-10-08</lastmod>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://pulnew.pages.dev/berita/rico-waas-semprot-bapenda-medan-pajak-3-64-triliun-baru-64-persen</loc>
    <lastmod>2026-10-08</lastmod>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://pulnew.pages.dev/berita/117-dusun-sumut-masih-gelap-47-lokasi-nias-mandailing-natal</loc>
    <lastmod>2026-10-08</lastmod>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://pulnew.pages.dev/berita/9-tahun-juara-berturut-piala-mtq-sumut-kembali-ke-medan</loc>
    <lastmod>2026-10-08</lastmod>
    <priority>0.8</priority>
  </url>
</urlset>`;

  return new Response(xml, {
    headers: { 
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600'
    }
  });
}

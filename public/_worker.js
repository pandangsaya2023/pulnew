export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // 1. CUMA PROSES KALO URL NYA /berita?slug=xxx
    if (url.pathname === '/berita' && url.searchParams.has('slug')) {
      const slug = url.searchParams.get('slug');
      
      try {
        // 2. AMBIL LIST URL BERITA DARI API
        const listRes = await fetch('https://pulnew.pages.dev/api/posts?t=' + Date.now(), {
          cf: { cacheTtl: 60 } // cache 1 menit biar gak berat
        });
        const listData = await listRes.json();
        const urls = Array.isArray(listData) ? listData : listData.urls || [];
        
        // 3. CARI URL BERITA YG SESUAI SLUG
        const postUrl = urls.find(u => u.toLowerCase().includes(slug.toLowerCase()));
        if (!postUrl) return fetch(request); // kalo gak ketemu, lempar normal

        // 4. AMBIL DETAIL BERITA
        const postRes = await fetch(postUrl + '?t=' + Date.now());
        if (!postRes.ok) return fetch(request);
        const post = await postRes.json();

        // 5. AMBIL FILE HTML ASLI berita.html
        const htmlRes = await fetch('https://pulnew.pages.dev/berita.html');
        let html = await htmlRes.text();

        // 6. SIAPIN DATA UNTUK META
        const title = post.title || 'PULNEW - Portal Info Terkini';
        const image = post.image || post.thumbnail || 'https://pulnew.pages.dev/media/og-default.jpg';
        const desc = (post.body || post.content || '').substring(0, 160).replace(/<[^>]*>/g, '').replace(/"/g, '&quot;') + '...';
        const fullUrl = `https://pulnew.pages.dev/berita?slug=${slug}`;
        const kategori = (post.kategori || post.category || 'BERITA').toUpperCase();

        // 7. SUNTIK META TAG LANGSUNG DI SERVER
        // Biar bot WA/FB baca yg ini, bukan yg dari JS
        html = html.replace(/<title>.*?<\/title>/, `<title>${title} - PULNEW</title>`);
        html = html.replace(/<meta property="og:title" content=".*?">/, `<meta property="og:title" content="${title}">`);
        html = html.replace(/<meta property="og:description" content=".*?">/, `<meta property="og:description" content="${desc}">`);
        html = html.replace(/<meta property="og:image" content=".*?">/, `<meta property="og:image" content="${image}">`);
        html = html.replace(/<meta property="og:image:width" content=".*?">/, `<meta property="og:image:width" content="1200">`);
        html = html.replace(/<meta property="og:image:height" content=".*?">/, `<meta property="og:image:height" content="630">`);
        html = html.replace(/<meta property="og:url" content=".*?">/, `<meta property="og:url" content="${fullUrl}">`);
        html = html.replace(/<meta name="twitter:title" content=".*?">/, `<meta name="twitter:title" content="${title}">`);
        html = html.replace(/<meta name="twitter:description" content=".*?">/, `<meta name="twitter:description" content="${desc}">`);
        html = html.replace(/<meta name="twitter:image" content=".*?">/, `<meta name="twitter:image" content="${image}">`);
        
        // TAMBAHAN: Biar pas dibuka manusia, judul di <h1> juga langsung ada
        // Ini opsional, biar gak kedip pas load
        html = html.replace('<div class="loading">Memuat berita...</div>', `
            <h1 class="article-title">${title}</h1>
            <div class="article-meta">${new Date(post.date || post.created_at).toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })} WIB | ${kategori}</div>
            <img src="${image}" class="main-image" alt="${title}" loading="lazy">
            <div style="display:none" id="preloaded-data"></div>
        `);

        // 8. KIRIM HASILNYA
        return new Response(html, {
          headers: {
            'Content-Type': 'text/html;charset=UTF-8',
            'Cache-Control': 'public, max-age=300' // cache 5 menit
          }
        });

      } catch (e) {
        console.error(e);
        return fetch(request); // kalau error, balik ke normal
      }
    }

    // KALO BUKAN /berita, LANJUT NORMAL
    return fetch(request);
  }
}

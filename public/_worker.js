export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Cek jika halaman yang dibuka adalah berita.html dan memiliki parameter slug
    if (url.pathname === '/berita.html' && url.searchParams.has('slug')) {
      const slug = url.searchParams.get('slug');
      
      // Ambil file HTML asli dari Cloudflare Pages Anda
      const response = await env.ASSETS.fetch(request);
      
      try {
        // Ambil data JSON berita terkait di latar belakang server
        const jsonUrl = `${url.origin}/posts/${slug}.json?t=${Date.now()}`;
        const jsonRes = await fetch(jsonUrl);
        
        if (jsonRes.ok) {
          const post = await jsonRes.json();
          
          const title = post.title ? `${post.title} - PULNEW.com` : "PULNEW.COM";
          const rawBody = post.body || post.content || "";
          const desc = rawBody.replace(/<[^>]*>/g, '').substring(0, 150) + "...";
          const image = post.image || post.thumbnail || `${url.origin}/media/og-default.jpg`;
          
          // Susun tag meta baru yang bersih dan dipaksa menggunakan tanda kutip penuh
          const metaTagsInject = `
            <title>${title}</title>
            <meta property="og:title" content="${post.title || 'PULNEW.COM'}" />
            <meta property="og:description" content="${desc}" />
            <meta property="og:image" content="${image}" />
            <meta property="og:url" content="${url.href}" />
            <meta property="og:type" content="article" />
            <meta name="twitter:card" content="summary_large_image" />
          `;
          
          // LANGSUNG SUNTIKKAN TEPAT DI BAWAH <head> & HAPUS TAG LAMA AGAR TIDAK BENTROK
          return new HTMLRewriter()
            .on('head', {
              element(el) {
                // Taruh tag meta baru paling atas di dalam HEAD
                el.prepend(metaTagsInject, { html: true });
              }
            })
            .on('title', {
              element(el) { el.remove(); } // Hapus title bawaan agar tidak ganda
            })
            .on('meta[property^="og:"]', {
              element(el) { el.remove(); } // Bersihkan semua meta og bawaan html
            })
            .on('meta[name^="twitter:"]', {
              element(el) { el.remove(); } // Bersihkan meta twitter bawaan html
            })
            .transform(response);
        }
      } catch (e) {
        console.error("Gagal melakukan manipulasi tag:", e);
      }
      
      return response;
    }
    
    return env.ASSETS.fetch(request);
  }
};

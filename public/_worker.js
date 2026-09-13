export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // 1. Cek apakah yang dibuka adalah halaman berita dan memiliki parameter slug
    if (url.pathname === '/berita.html' && url.searchParams.has('slug')) {
      const slug = url.searchParams.get('slug');
      
      // Ambil file HTML asli dari Cloudflare Pages Anda
      const response = await env.ASSETS.fetch(request);
      
      try {
        // Ambil data JSON berita terkait di latar belakang server
        const jsonUrl = `${url.origin}/posts/${slug}.json`;
        const jsonRes = await fetch(jsonUrl);
        
        if (jsonRes.ok) {
          const post = await jsonRes.json();
          
          // Siapkan data pengganti untuk Meta Tag WhatsApp
          const title = post.title ? `${post.title} - PULNEW` : "PULNEW";
          const rawBody = post.body || post.content || "";
          const desc = rawBody.replace(/<[^>]*>/g, '').substring(0, 160) + "...";
          const image = post.image || post.thumbnail || `${url.origin}/media/og-default.jpg`;
          
          // Jalankan fitur HTML Rewriter untuk menyuntikkan tag secara realtime
          return new HTMLRewriter()
            .on('title', {
              element(el) { el.setInnerContent(title); }
            })
            .on('meta[property="og:title"]', {
              element(el) { el.setAttribute('content', post.title || ""); }
            })
            .on('meta[property="og:description"]', {
              element(el) { el.setAttribute('content', desc); }
            })
            .on('meta[property="og:image"]', {
              element(el) { el.setAttribute('content', image); }
            })
            .on('meta[property="og:url"]', {
              element(el) { el.setAttribute('content', url.href); }
            })
            .transform(response);
        }
      } catch (e) {
        console.error("Gagal menyuntikkan Meta Tag:", e);
      }
      
      return response;
    }
    
    // Jika bukan halaman berita, biarkan Cloudflare Pages memuat file seperti biasa
    return env.ASSETS.fetch(request);
  }
};


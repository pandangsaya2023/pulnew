export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    if ((url.pathname === '/berita' || url.pathname === '/berita.html') && url.searchParams.has('slug')) {
      const slug = url.searchParams.get('slug');
      const response = await env.ASSETS.fetch(request);
      
      try {
        const jsonUrl = `${url.origin}/posts/${slug}.json?t=${Date.now()}`;
        const jsonRes = await fetch(jsonUrl);
        
        if (jsonRes.ok) {
          const post = await jsonRes.json();
          
          const title = post.title ? `${post.title} - PULNEW` : "PULNEW";
          const rawBody = post.body || post.content || "";
          const desc = post.meta_description || rawBody.replace(/<[^>]*>/g, '').substring(0, 150) + "...";
          
          // --- PERBAIKAN OTOMATIS URL GAMBAR ---
          let rawImage = post.image || post.thumbnail || "/media/og-default.jpg";
          let image = rawImage;
          
          // Jika alamat gambar di JSON belum diawali http/https, otomatis tambahkan domain Anda
          if (!rawImage.startsWith('http://') && !rawImage.startsWith('https://')) {
            // Pastikan format garis miring miringnya benar
            if (rawImage.startsWith('/')) {
              image = `${url.origin}${rawImage}`;
            } else {
              image = `${url.origin}/${rawImage}`;
            }
          }
          // -------------------------------------
          
          const metaTagsInject = `
            <title>${title}</title>
            <meta property="og:title" content="${post.title || 'PULNEW'}" />
            <meta property="og:description" content="${desc}" />
            <meta property="og:image" content="${image}" />
            <meta property="og:url" content="${url.href}" />
            <meta property="og:type" content="article" />
            <meta name="twitter:card" content="summary_large_image" />
          `;
          
          return new HTMLRewriter()
            .on('head', {
              element(el) { el.prepend(metaTagsInject, { html: true }); }
            })
            .on('title', {
              element(el) { el.remove(); }
            })
            .on('meta[property^="og:"]', {
              element(el) { el.remove(); }
            })
            .on('meta[name^="twitter:"]', {
              element(el) { el.remove(); }
            })
            .transform(response);
        }
      } catch (e) {
        console.error("Gagal manipulasi:", e);
      }
      
      return response;
    }
    
    return env.ASSETS.fetch(request);
  }
};


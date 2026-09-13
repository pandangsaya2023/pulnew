export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // PERBAIKAN: Mengenali /berita maupun /berita.html
    if ((url.pathname === '/berita' || url.pathname === '/berita.html') && url.searchParams.has('slug')) {
      const slug = url.searchParams.get('slug');
      
      // Ambil file asli dari server
      const response = await env.ASSETS.fetch(request);
      
      try {
        // Ambil data JSON berita terkait
        const jsonUrl = `${url.origin}/posts/${slug}.json?t=${Date.now()}`;
        const jsonRes = await fetch(jsonUrl);
        
        if (jsonRes.ok) {
          const post = await jsonRes.json();
          
          const title = post.title ? `${post.title} - PULNEW.com` : "PULNEW.COM";
          const rawBody = post.body || post.content || "";
          const desc = rawBody.replace(/<[^>]*>/g, '').substring(0, 150) + "...";
          const image = post.image || post.thumbnail || `${url.origin}/media/og-default.jpg`;
          
          const metaTagsInject = `
            <title>${title}</title>
            <meta property="og:title" content="${post.title || 'PULNEW.COM'}" />
            <meta property="og:description" content="${desc}" />
            <meta property="og:image" content="${image}" />
            <meta property="og:url" content="${url.href}" />
            <meta property="og:type" content="article" />
            <meta name="twitter:card" content="summary_large_image" />
          `;
          
          return new HTMLRewriter()
            .on('head', {
              element(el) {
                el.prepend(metaTagsInject, { html: true });
              }
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

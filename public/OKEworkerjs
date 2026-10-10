export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // 1. JANGAN DI-INTERCEPT - biarin file statis lolos langsung (ini fix robots.txt 186 error)
    if (
      url.pathname === '/robots.txt' ||
      url.pathname === '/sitemap.xml' ||
      url.pathname === '/llms.txt' ||
      url.pathname === '/favicon.ico' ||
      url.pathname.startsWith('/posts/') ||
      url.pathname.startsWith('/media/') ||
      url.pathname.startsWith('/_headers')
    ) {
      return env.ASSETS.fetch(request);
    }

    // 2. KHUSUS HALAMAN BERITA - inject SEO tapi pakai cache (hapus Date.now)
    if ((url.pathname === '/berita' || url.pathname === '/berita.html') && url.searchParams.has('slug')) {
      const slug = url.searchParams.get('slug');
      const response = await env.ASSETS.fetch(request);

      try {
        // FIX: HAPUS ?t=Date.now() biar ke-cache
        const jsonUrl = `${url.origin}/posts/${slug}.json`;
        const jsonRes = await fetch(jsonUrl, { cf: { cacheTtl: 3600, cacheEverything: true } });

        if (jsonRes.ok) {
          const post = await jsonRes.json();
          const judulSeo = post.seo_title || post.title;
          const title = judulSeo ? `${judulSeo} - PULNEW` : 'PULNEW';
          const rawBody = post.body || post.content || "";
          const cleanBody = rawBody.replace(/(<([^>]+)>)/ig, "").replace(/"/g, '&quot;');
          const desc = (post.description || post.excerpt || (cleanBody ? cleanBody.substring(0, 150) + "..." : "")).replace(/"/g, '&quot;');

          let rawImage = post.image || post.thumbnail || "/media/og-image.webp";
          let image = rawImage;
          if (!rawImage.startsWith('http')) {
            image = rawImage.startsWith('/') ? `${url.origin}${rawImage}` : `${url.origin}/${rawImage}`;
          }

          const metaTagsInjct = `
            <title>${title}</title>
            <meta name="description" content="${desc}" />
            <link rel="icon" href="${url.origin}/favicon.ico" />
            <meta property="og:title" content="${(post.title || 'PULNEW').replace(/"/g, '&quot;')}" />
            <meta property="og:description" content="${desc}" />
            <meta property="og:image" content="${image}" />
            <meta property="og:url" content="${url.href}" />
            <meta property="og:type" content="article" />
            <meta name="twitter:card" content="summary_large_image" />
          `;

          return new HTMLRewriter()
            .on('head', { element(el) { el.prepend(metaTagsInjct, { html: true }); } })
            .on('title', { element(el) { el.remove(); } })
            .on('link[rel*="icon"]', { element(el) { el.remove(); } })
            .on('meta[property^="og:"]', { element(el) { el.remove(); } })
            .on('meta[name^="twitter:"]', { element(el) { el.remove(); } })
            .on('meta[name="description"]', { element(el) { el.remove(); } })
            .transform(response);
        }
      } catch (e) {
        console.error("Gagal manipulasi:", e);
      }
      return response;
    }

    // 3. UNTUK YANG LAIN (index.html) - tambahin cache header biar PageSpeed ijo
    const res = await env.ASSETS.fetch(request);
    const newRes = new Response(res.body, res);
    if (url.pathname === '/' || url.pathname.endsWith('.html')) {
      newRes.headers.set('Cache-Control', 'public, max-age=0, must-revalidate');
    }
    if (url.pathname.match(/\.(png|jpg|jpeg|webp|ico|css|js)$/)) {
      newRes.headers.set('Cache-Control', 'public, max-age=31536000, immutable');
    }
    return newRes;
  }
};

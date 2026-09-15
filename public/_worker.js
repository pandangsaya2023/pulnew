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

          const title = post.title ? `${post.title} - PULNEW` : 'PULNEW';
          
          const rawBody = post.body || post.content || "";
          const cleanBody = rawBody.replace(/(<([^>]+)>)/ig, "");
          const desc = post.description || post.excerpt || (cleanBody ? cleanBody.substring(0, 150) + "..." : "");

          // --- PERBAIKAN OTOMATIS URL GAMBAR ---
          let rawImage = post.image || post.thumbnail || "/media/og-default.jpg";
          let image = rawImage;

          if (!rawImage.startsWith('http://') && !rawImage.startsWith('https://')) {
            if (rawImage.startsWith('/')) {
              image = `${url.origin}${rawImage}`;
            } else {
              image = `${url.origin}/${rawImage}`;
            }
          }
          // ------------------------------------

          const metaTagsInjct = `
            <title>${title}</title>
            <meta name="description" content="${desc}" />
            <link rel="icon" type="image/png" href="${url.origin}/logopulnew7.png" />
            <link rel="apple-touch-icon" href="${url.origin}/logopulnew7.png" />
            <meta property="og:title" content="${post.title || 'PULNEW'}" />
            <meta property="og:description" content="${desc}" />
            <meta property="og:image" content="${image}" />
            <meta property="og:url" content="${url.href}" />
            <meta property="og:type" content="article" />
            <meta name="twitter:card" content="summary_large_image" />
          `;

          return new HTMLRewriter()
            .on('head', {
              element(el) { el.prepend(metaTagsInjct, { html: true }); }
            })
            .on('title', {
              element(el) { el.remove(); }
            })
            .on('link[rel*="icon"]', {
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

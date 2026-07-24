export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    if (url.pathname.startsWith('/berita')) {
      const slug = url.searchParams.get('slug');
      if (!slug) return env.ASSETS.fetch(request);
      
      try {
        const listRes = await fetch('https://pulnew.pages.dev/api/posts');
        const listData = await listRes.json();
        const urls = Array.isArray(listData) ? listData : listData.urls || [];
        const postUrl = urls.find(u => u.toLowerCase().includes(slug.toLowerCase()));
        if (!postUrl) return env.ASSETS.fetch(request);

        const [postRes, htmlRes] = await Promise.all([
          fetch(postUrl),
          env.ASSETS.fetch(new Request('https://pulnew.pages.dev/berita.html'))
        ]);
        
        const post = await postRes.json();
        let html = await htmlRes.text();

        const title = post.title || 'PULNEW';
        const image = post.image || post.thumbnail || 'https://pulnew.pages.dev/media/og-default.jpg';
        const desc = (post.body || post.content || '').substring(0, 160).replace(/<[^>]*>/g, '') + '...';
        const fullUrl = request.url;

        // HAPUS META LAMA DULU, BARU SUNTIK BARU
        html = html.replace(/<meta property="og:.*?" content=".*?">/g, '');
        html = html.replace(/<meta name="twitter:.*?" content=".*?">/g, '');
        html = html.replace(/<title>.*?<\/title>/, '');

        const newMeta = `
        <title>${title} - PULNEW</title>
        <meta property="og:title" content="${title}">
        <meta property="og:description" content="${desc}">
        <meta property="og:image" content="${image}">
        <meta property="og:image:width" content="1200">
        <meta property="og:image:height" content="630">
        <meta property="og:url" content="${fullUrl}">
        <meta property="og:type" content="article">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="${title}">
        <meta name="twitter:description" content="${desc}">
        <meta name="twitter:image" content="${image}">
        `;
        html = html.replace('</head>', newMeta + '</head>');

        return new Response(html, { headers: { 'Content-Type': 'text/html;charset=UTF-8' } });

      } catch (e) {
        return env.ASSETS.fetch(request);
      }
    }
    return env.ASSETS.fetch(request);
  }
}

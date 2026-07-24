export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    if (url.pathname === '/berita' && url.searchParams.has('slug')) {
      const slug = url.searchParams.get('slug');
      
      try {
        // JANGAN FETCH DARI DOMAIN SENDIRI. PAKE REQUEST.ASSET
        const listRes = await env.ASSETS.fetch(new Request('https://pulnew.pages.dev/api/posts'));
        const listData = await listRes.json();
        const urls = Array.isArray(listData) ? listData : listData.urls || [];
        
        const postUrl = urls.find(u => u.toLowerCase().includes(slug.toLowerCase()));
        if (!postUrl) return env.ASSETS.fetch(request);

        const postRes = await fetch(postUrl);
        if (!postRes.ok) return env.ASSETS.fetch(request);
        const post = await postRes.json();

        const htmlRes = await env.ASSETS.fetch(new Request('https://pulnew.pages.dev/berita.html'));
        let html = await htmlRes.text();

        const title = post.title || 'PULNEW';
        const image = post.image || post.thumbnail || 'https://pulnew.pages.dev/media/og-default.jpg';
        const desc = (post.body || post.content || '').substring(0, 160).replace(/<[^>]*>/g, '').replace(/"/g, '&quot;') + '...';
        const fullUrl = `https://pulnew.pages.dev/berita?slug=${slug}`;

        // REPLACE AMAN
        html = html.replace(/<title>.*?<\/title>/s, `<title>${title} - PULNEW</title>`);
        html = html.replace(/<meta property="og:title" content=".*?">/s, `<meta property="og:title" content="${title}">`);
        html = html.replace(/<meta property="og:description" content=".*?">/s, `<meta property="og:description" content="${desc}">`);
        html = html.replace(/<meta property="og:image" content=".*?">/s, `<meta property="og:image" content="${image}">`);
        html = html.replace(/<meta property="og:url" content=".*?">/s, `<meta property="og:url" content="${fullUrl}">`);

        return new Response(html, {
          headers: { 'Content-Type': 'text/html;charset=UTF-8' }
        });

      } catch (e) {
        return new Response('Error: ' + e.message, { status: 500 });
      }
    }
    
    // Default: kasih file static biasa
    return env.ASSETS.fetch(request);
  }
}

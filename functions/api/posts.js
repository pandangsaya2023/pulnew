export async function onRequest() {
  const owner = 'NappuDev';
  const repo = 'news-pulnew';
  const path = 'posts.js';

  const apiUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;

  try {
    const res = await fetch(apiUrl, {
      headers: {
        'Accept': 'application/vnd.github.v3.raw',
        'Cache-Control': 'no-cache'
      }
    });

    if (!res.ok) {
      return new Response(JSON.stringify([]), { 
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store, max-age=0'
        }
      });
    }

    const text = await res.text();
    const urls = text.match(/https?:\/\/[^\s'"]+/g) || [];

    return new Response(JSON.stringify(urls), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store, max-age=0, must-revalidate'
      }
    });

  } catch (err) {
    return new Response(JSON.stringify([]), { 
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store, max-age=0'
      }
    });
  }
}

export async function onRequest() {
  try {
    const githubRes = await fetch(
      'https://api.github.com/repos/pandangsaya2023/pulnew/contents/public/posts',
      { headers: { 'User-Agent': 'pulnew-site' } }
    );
    
    const files = await githubRes.json();
    
    // Balikin cuma URL download, jangan fetch isinya di server
    const urls = files
      .filter(f => f.name.endsWith('.json'))
      .map(f => f.download_url);
    
    return new Response(JSON.stringify({ urls }), {
      headers: { 
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache' 
      }
    });
    
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message, urls: [] }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

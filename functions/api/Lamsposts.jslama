export async function onRequest(context) {
  const { env } = context;
  
  try {
    const { results } = await env.MY_BUCKET.list({ prefix: 'posts/' });
    
    const urls = results
      .filter(obj => obj.key.endsWith('.json'))
      .map(obj => `https://pandangsaya2023.github.io/pulnew/${obj.key}`);
    
    return new Response(JSON.stringify(urls), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'no-cache'
      }
    });
    
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

export async function onRequest(context) {
  return await proxy(context);
}

async function proxy({ request, env }) {
  const url = new URL(request.url);
  const target = `https://github.com${url.pathname.replace('/api/auth', '')}${url.search}`;
  
  const newRequest = new Request(target, {
    method: request.method,
    headers: request.headers,
    body: request.body
  });

  return fetch(newRequest);
}

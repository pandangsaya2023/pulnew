// functions/api/callback.js
export async function onRequest(context) {
  const url = new URL(context.request.url);
  const code = url.searchParams.get("code");

  if (!code) {
    return new Response("Missing code parameter", { status: 400 });
  }

  // Menukarkan kode sementara dari GitHub dengan Access Token
  const response = await fetch("https://github.com", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      client_id: context.env.GITHUB_CLIENT_ID,
      client_secret: context.env.GITHUB_CLIENT_SECRET,
      code: code,
    }),
  });

  const data = await response.json();

  if (data.error) {
    return new Response(JSON.stringify(data), { status: 400 });
  }

  // Format pesan skrip wajib agar Decap CMS dapat membaca token tersebut
  const script = `
    <script>
      const receiveMessage = (message) => {
        if (message.origin !== window.origin) return;
        window.opener.postMessage(
          'authorization:github:success:${JSON.stringify({ token: data.access_token, provider: 'github' })}',
          message.origin
        );
        window.removeEventListener('message', receiveMessage, false);
      }
      window.addEventListener('message', receiveMessage, false);
      window.opener.postMessage('authorizing:github', window.origin);
    </script>
  `;

  return new Response(script, {
    headers: { "Content-Type": "text/html" },
  });
}


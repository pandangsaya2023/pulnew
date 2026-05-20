// functions/api/auth.js
export async function onRequest(context) {
  const clientId = context.env.GITHUB_CLIENT_ID;
  const redirectUri = new URL(context.request.url).origin + "/api/callback";
  
  // Mengarahkan pengguna ke halaman login GitHub dengan akses repositori
  const githubAuthUrl = `https://github.com{clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=repo,user`;
  
  return Response.redirect(githubAuthUrl, 302);
}

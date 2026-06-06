#!/usr/bin/env node
/**
 * Local helper to generate a Google Ads API refresh token.
 * Usage: GOOGLE_ADS_CLIENT_ID=... GOOGLE_ADS_CLIENT_SECRET=... node scripts/generate-refresh-token.js
 */
const http = require('http');
const { URL } = require('url');
const { OAuth2Client } = require('google-auth-library');

const clientId = process.env.GOOGLE_ADS_CLIENT_ID;
const clientSecret = process.env.GOOGLE_ADS_CLIENT_SECRET;

if (!clientId || !clientSecret) {
  console.error('Set GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET');
  process.exit(1);
}

let redirectUri;

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');

  if (url.pathname !== '/oauth2callback') {
    res.writeHead(404);
    return res.end('Not found');
  }

  const code = url.searchParams.get('code');
  if (!code) {
    res.writeHead(400);
    return res.end('Missing code');
  }

  try {
    const client = new OAuth2Client(clientId, clientSecret, redirectUri);
    const { tokens } = await client.getToken(code);
    res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end(`Refresh token:\n${tokens.refresh_token}\n`);
    console.log('\nRefresh token:', tokens.refresh_token);
    server.close();
    process.exit(0);
  } catch (error) {
    res.writeHead(500);
    res.end(error.message);
  }
});

server.listen(0, '127.0.0.1', () => {
  const { port } = server.address();
  redirectUri = `http://127.0.0.1:${port}/oauth2callback`;
  const client = new OAuth2Client(clientId, clientSecret, redirectUri);
  const authUrl = client.generateAuthUrl({
    access_type: 'offline',
    prompt: 'consent',
    scope: ['https://www.googleapis.com/auth/adwords'],
  });

  console.log('Open this URL in your browser:\n');
  console.log(authUrl);
  console.log(`\nWaiting for callback on ${redirectUri}`);
});

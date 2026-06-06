const { OAuth2Client } = require('google-auth-library');
const { getConfig } = require('./config');

const ADWORDS_SCOPE = 'https://www.googleapis.com/auth/adwords';
const USERINFO_SCOPE = 'https://www.googleapis.com/auth/userinfo.email';

function createOAuthClient() {
  const config = getConfig();
  if (!config.clientId || !config.clientSecret) {
    throw new Error('OAuth client credentials are not configured');
  }

  return new OAuth2Client(
    config.clientId,
    config.clientSecret,
    `${config.appUrl}/api/auth/callback`
  );
}

function getLoginUrl() {
  const client = createOAuthClient();
  return client.generateAuthUrl({
    access_type: 'offline',
    prompt: 'consent',
    scope: [ADWORDS_SCOPE, USERINFO_SCOPE],
    include_granted_scopes: true,
  });
}

async function exchangeCode(code) {
  const client = createOAuthClient();
  const { tokens } = await client.getToken(code);
  client.setCredentials(tokens);

  let email = null;
  if (tokens.access_token) {
    const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: { Authorization: `Bearer ${tokens.access_token}` },
    });
    if (response.ok) {
      const profile = await response.json();
      email = profile.email || null;
    }
  }

  return {
    refreshToken: tokens.refresh_token,
    email,
  };
}

function isEmailAllowed(email) {
  const allowed = getConfig().allowedEmails;
  if (!allowed.length) return true;
  return email && allowed.includes(email.toLowerCase());
}

module.exports = {
  getLoginUrl,
  exchangeCode,
  isEmailAllowed,
};

const { getConfig } = require('../../lib/config');
const { getSession } = require('../../lib/session');

module.exports = async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const config = getConfig();
  const session = getSession(req);

  return res.status(200).json({
    authenticated: Boolean(session?.refreshToken),
    email: session?.email || null,
    customerId: session?.customerId || config.customerId,
    configured: Boolean(
      config.clientId && config.clientSecret && config.developerToken
    ),
  });
};

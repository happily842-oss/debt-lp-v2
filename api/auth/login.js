const { getLoginUrl } = require('../../lib/auth');
const { getConfig } = require('../../lib/config');

module.exports = async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const config = getConfig();
    if (!config.clientId || !config.clientSecret) {
      return res.status(500).json({
        error: 'OAuth is not configured. Set GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET.',
      });
    }

    res.writeHead(302, { Location: getLoginUrl() });
    res.end();
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
};

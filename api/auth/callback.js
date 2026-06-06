const { exchangeCode, isEmailAllowed } = require('../../lib/auth');
const { getConfig } = require('../../lib/config');
const { listAccessibleCustomers } = require('../../lib/google-ads');
const { setSessionCookie } = require('../../lib/session');

module.exports = async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { code, error } = req.query;
  if (error) {
    res.writeHead(302, { Location: `/admin?error=${encodeURIComponent(error)}` });
    return res.end();
  }

  if (!code) {
    res.writeHead(302, { Location: '/admin?error=missing_code' });
    return res.end();
  }

  try {
    const { refreshToken, email } = await exchangeCode(code);

    if (!refreshToken) {
      res.writeHead(302, { Location: '/admin?error=no_refresh_token' });
      return res.end();
    }

    if (!isEmailAllowed(email)) {
      res.writeHead(302, { Location: '/admin?error=unauthorized_email' });
      return res.end();
    }

    const config = getConfig();
    let customerId = config.customerId;

    if (!customerId) {
      const customers = await listAccessibleCustomers(refreshToken);
      if (!customers.length) {
        res.writeHead(302, { Location: '/admin?error=no_accounts' });
        return res.end();
      }
      customerId = customers[0];
    }

    setSessionCookie(res, {
      refreshToken,
      email,
      customerId: String(customerId).replace(/-/g, ''),
    });

    res.writeHead(302, { Location: '/admin' });
    res.end();
  } catch (err) {
    res.writeHead(302, {
      Location: `/admin?error=${encodeURIComponent(err.message || 'auth_failed')}`,
    });
    res.end();
  }
};

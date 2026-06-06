const { clearSessionCookie } = require('../../lib/session');

module.exports = async function handler(req, res) {
  if (req.method !== 'POST' && req.method !== 'GET') {
    res.setHeader('Allow', 'GET, POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  clearSessionCookie(res);

  if (req.method === 'GET') {
    res.writeHead(302, { Location: '/admin' });
    return res.end();
  }

  return res.status(200).json({ ok: true });
};

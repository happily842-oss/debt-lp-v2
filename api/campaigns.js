const { getSession } = require('../lib/session');
const { fetchCampaigns, updateCampaignStatus } = require('../lib/google-ads');

module.exports = async function handler(req, res) {
  const session = getSession(req);
  if (!session?.refreshToken) {
    return res.status(401).json({ error: 'Not authenticated' });
  }

  const customerId = session.customerId;
  if (!customerId) {
    return res.status(400).json({ error: 'No Google Ads customer ID in session' });
  }

  try {
    if (req.method === 'GET') {
      const campaigns = await fetchCampaigns(session.refreshToken, customerId);
      return res.status(200).json({ campaigns, customerId });
    }

    if (req.method === 'PATCH') {
      const body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
      const { id, status } = body || {};

      if (!id || !['ENABLED', 'PAUSED'].includes(status)) {
        return res.status(400).json({ error: 'id and status (ENABLED|PAUSED) are required' });
      }

      const updated = await updateCampaignStatus(
        session.refreshToken,
        customerId,
        id,
        status
      );

      return res.status(200).json({ campaign: updated });
    }

    res.setHeader('Allow', 'GET, PATCH');
    return res.status(405).json({ error: 'Method not allowed' });
  } catch (error) {
    const message = error?.message || 'Google Ads API request failed';
    return res.status(500).json({ error: message });
  }
};

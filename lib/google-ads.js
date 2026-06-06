const { GoogleAdsApi, enums } = require('google-ads-api');
const { getConfig, assertAdsConfig } = require('./config');

function createClient() {
  const config = getConfig();
  assertAdsConfig(config);

  return new GoogleAdsApi({
    client_id: config.clientId,
    client_secret: config.clientSecret,
    developer_token: config.developerToken,
  });
}

function createCustomer(refreshToken, customerId, loginCustomerId) {
  const config = getConfig();
  const client = createClient();

  const options = {
    customer_id: String(customerId).replace(/-/g, ''),
    refresh_token: refreshToken,
  };

  const managerId = loginCustomerId || config.loginCustomerId;
  if (managerId) {
    options.login_customer_id = String(managerId).replace(/-/g, '');
  }

  return client.Customer(options);
}

async function listAccessibleCustomers(refreshToken) {
  const client = createClient();
  const resourceNames = await client.listAccessibleCustomers(refreshToken);
  return resourceNames.map((name) => name.replace('customers/', ''));
}

async function fetchCampaigns(refreshToken, customerId, loginCustomerId) {
  const customer = createCustomer(refreshToken, customerId, loginCustomerId);
  const rows = await customer.query(`
    SELECT
      campaign.id,
      campaign.name,
      campaign.status,
      campaign.advertising_channel_type,
      campaign_budget.amount_micros,
      metrics.cost_micros,
      metrics.clicks,
      metrics.impressions,
      metrics.conversions
    FROM campaign
    WHERE campaign.status != 'REMOVED'
    ORDER BY campaign.name
  `);

  return rows.map((row) => ({
    id: String(row.campaign.id),
    name: row.campaign.name,
    status: row.campaign.status,
    channelType: row.campaign.advertising_channel_type,
    budgetMicros: row.campaign_budget?.amount_micros || 0,
    costMicros: row.metrics?.cost_micros || 0,
    clicks: row.metrics?.clicks || 0,
    impressions: row.metrics?.impressions || 0,
    conversions: row.metrics?.conversions || 0,
  }));
}

async function updateCampaignStatus(refreshToken, customerId, campaignId, status, loginCustomerId) {
  const customer = createCustomer(refreshToken, customerId, loginCustomerId);
  const normalizedCustomerId = String(customerId).replace(/-/g, '');
  const statusEnum =
    status === 'ENABLED' ? enums.CampaignStatus.ENABLED : enums.CampaignStatus.PAUSED;

  await customer.campaigns.update([
    {
      resource_name: `customers/${normalizedCustomerId}/campaigns/${campaignId}`,
      status: statusEnum,
    },
  ]);

  return { id: String(campaignId), status };
}

function microsToYen(micros) {
  return Math.round(Number(micros || 0) / 1_000_000);
}

module.exports = {
  listAccessibleCustomers,
  fetchCampaigns,
  updateCampaignStatus,
  microsToYen,
};

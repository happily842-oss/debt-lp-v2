function required(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing environment variable: ${name}`);
  }
  return value;
}

function optional(name) {
  return process.env[name] || null;
}

function getConfig() {
  return {
    clientId: optional('GOOGLE_ADS_CLIENT_ID'),
    clientSecret: optional('GOOGLE_ADS_CLIENT_SECRET'),
    developerToken: optional('GOOGLE_ADS_DEVELOPER_TOKEN'),
    customerId: optional('GOOGLE_ADS_CUSTOMER_ID'),
    loginCustomerId: optional('GOOGLE_ADS_LOGIN_CUSTOMER_ID'),
    sessionSecret: optional('SESSION_SECRET') || 'change-me-in-production',
    allowedEmails: (optional('ADMIN_ALLOWED_EMAILS') || '')
      .split(',')
      .map((email) => email.trim().toLowerCase())
      .filter(Boolean),
    appUrl: optional('APP_URL') || 'http://localhost:3000',
  };
}

function assertAdsConfig(config) {
  if (!config.clientId || !config.clientSecret || !config.developerToken) {
    throw new Error('Google Ads API credentials are not configured');
  }
}

module.exports = {
  getConfig,
  assertAdsConfig,
  required,
};

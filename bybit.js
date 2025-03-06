const axios = require('axios');
const crypto = require('crypto');

class BybitAPI {
  constructor(apiKey, apiSecret, testnet = false) {
    this.apiKey = apiKey;
    this.apiSecret = apiSecret;
    this.baseUrl = testnet 
      ? 'https://api-testnet.bybit.com' 
      : 'https://api.bybit.com';
  }

  // 生成簽名
  generateSignature(params, timestamp) {
    const queryString = timestamp + this.apiKey + params;
    return crypto.createHmac('sha256', this.apiSecret)
      .update(queryString)
      .digest('hex');
  }

  // 創建訂單
  async createOrder({ symbol, side, quantity, price, stopLoss, takeProfit }) {
    try {
      const timestamp = Date.now().toString();
      const params = {
        symbol,
        side: side.toUpperCase(),
        order_type: price ? 'LIMIT' : 'MARKET',
        qty: quantity.toString(),
        time_in_force: 'GTC',
        reduce_only: false,
        close_on_trigger: false
      };

      // 如果提供了價格，則為限價單
      if (price) {
        params.price = price.toString();
      }

      // 如果提供了止損價格
      if (stopLoss) {
        params.stop_loss = stopLoss.toString();
      }

      // 如果提供了止盈價格
      if (takeProfit) {
        params.take_profit = takeProfit.toString();
      }

      const queryString = Object.keys(params)
        .sort()
        .map(key => `${key}=${params[key]}`)
        .join('&');

      const signature = this.generateSignature(queryString, timestamp);

      const response = await axios({
        method: 'POST',
        url: `${this.baseUrl}/v2/private/order/create`,
        headers: {
          'X-BAPI-API-KEY': this.apiKey,
          'X-BAPI-TIMESTAMP': timestamp,
          'X-BAPI-SIGN': signature
        },
        data: params
      });

      return response.data;
    } catch (error) {
      console.error('Bybit API Error:', error.response ? error.response.data : error.message);
      throw error;
    }
  }

  // 獲取帳戶餘額
  async getWalletBalance(coin = 'USDT') {
    try {
      const timestamp = Date.now().toString();
      const params = { coin };
      
      const queryString = Object.keys(params)
        .sort()
        .map(key => `${key}=${params[key]}`)
        .join('&');

      const signature = this.generateSignature(queryString, timestamp);

      const response = await axios({
        method: 'GET',
        url: `${this.baseUrl}/v2/private/wallet/balance`,
        headers: {
          'X-BAPI-API-KEY': this.apiKey,
          'X-BAPI-TIMESTAMP': timestamp,
          'X-BAPI-SIGN': signature
        },
        params
      });

      return response.data;
    } catch (error) {
      console.error('Bybit API Error:', error.response ? error.response.data : error.message);
      throw error;
    }
  }
}

// 從環境變數創建 Bybit API 實例
const bybitAPI = new BybitAPI(
  process.env.BYBIT_API_KEY,
  process.env.BYBIT_API_SECRET,
  process.env.BYBIT_TESTNET === 'true'
);

module.exports = { bybitAPI, BybitAPI }; 
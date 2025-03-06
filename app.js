const express = require('express');
const dotenv = require('dotenv');
const crypto = require('crypto');
const { createLogger, format, transports } = require('winston');
const { bybitAPI } = require('./bybit');

// 載入環境變數
dotenv.config();

// 設置日誌
const logger = createLogger({
  level: 'info',
  format: format.combine(
    format.timestamp(),
    format.json()
  ),
  transports: [
    new transports.File({ filename: 'error.log', level: 'error' }),
    new transports.File({ filename: 'combined.log' }),
    new transports.Console({ format: format.simple() })
  ]
});

const app = express();
app.use(express.json());

// 驗證 TradingView 請求的中間件
const authenticateWebhook = (req, res, next) => {
  const signature = req.headers['x-tradingview-signature'];
  const payload = JSON.stringify(req.body);
  const secret = process.env.TRADINGVIEW_SECRET;
  
  if (!signature) {
    logger.error('Missing signature header');
    return res.status(401).send('Unauthorized');
  }
  
  const hmac = crypto.createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  
  if (hmac !== signature) {
    logger.error('Invalid signature');
    return res.status(401).send('Unauthorized');
  }
  
  next();
};

// Webhook 端點
app.post('/webhook', authenticateWebhook, async (req, res) => {
  try {
    logger.info('Received webhook', { payload: req.body });
    
    const { symbol, side, quantity, price, stopLoss, takeProfit } = req.body;
    
    // 驗證必要參數
    if (!symbol || !side || !quantity) {
      logger.error('Missing required parameters');
      return res.status(400).send('Missing required parameters');
    }
    
    // 執行交易
    const orderResult = await bybitAPI.createOrder({
      symbol,
      side,
      quantity,
      price,
      stopLoss,
      takeProfit
    });
    
    logger.info('Order placed successfully', { order: orderResult });
    
    return res.status(200).json({
      success: true,
      message: 'Order placed successfully',
      data: orderResult
    });
  } catch (error) {
    logger.error('Error processing webhook', { error: error.message });
    return res.status(500).json({
      success: false,
      message: 'Error processing webhook',
      error: error.message
    });
  }
});

// 健康檢查端點
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  logger.info(`Server running on port ${PORT}`);
}); 
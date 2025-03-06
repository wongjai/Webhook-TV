const express = require('express');
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const dotenv = require('dotenv');
const { apiKeyAuth } = require('./middleware/auth');
const { processSignal } = require('./services/signalProcessor');

// 載入環境變量
dotenv.config();

// 初始化Express應用
const app = express();

// 中間件
app.use(bodyParser.json());

// 連接MongoDB
mongoose.connect(process.env.MONGODB_URI)
  .then(() => console.log('已連接到MongoDB'))
  .catch(err => console.error('MongoDB連接錯誤:', err));

// Webhook端點 - 接收TradingView訊號
app.post('/api/signals', apiKeyAuth, async (req, res) => {
  try {
    const signalData = req.body;
    const { signal, tradeResult } = await processSignal(signalData);
    
    const response = {
      success: true,
      message: '訊號已成功接收並處理',
      signal: {
        id: signal._id,
        symbol: signal.symbol,
        action: signal.action,
        price: signal.price,
        timestamp: signal.timestamp
      }
    };
    
    // 如果執行了交易，添加交易結果到響應
    if (tradeResult) {
      response.trade = {
        id: tradeResult.trade._id,
        orderId: tradeResult.trade.orderId,
        status: tradeResult.trade.status,
        side: tradeResult.trade.side,
        quantity: tradeResult.trade.quantity
      };
    }
    
    res.status(200).json(response);
  } catch (error) {
    console.error('處理webhook請求時出錯:', error);
    res.status(400).json({
      success: false,
      message: '處理訊號時出錯',
      error: error.message
    });
  }
});

// 健康檢查端點
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// 啟動服務器
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`服務器運行在端口 ${PORT}`);
});

module.exports = app; 
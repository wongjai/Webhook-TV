const { LinearClient } = require('bybit-api');
const Trade = require('../models/Trade');

// 初始化 Bybit API 客戶端
const bybitClient = new LinearClient(
  process.env.BYBIT_API_KEY,
  process.env.BYBIT_API_SECRET,
  process.env.BYBIT_TESTNET === 'true' // 是否使用測試網
);

/**
 * 根據交易訊號執行 Bybit 交易
 * @param {Object} signal - 交易訊號對象
 * @param {Object} options - 交易選項
 * @returns {Promise<Object>} - 交易結果
 */
async function executeTradeFromSignal(signal, options = {}) {
  try {
    // 默認交易選項
    const defaultOptions = {
      orderType: 'Market',
      leverage: 1,
      reduceOnly: false,
      closePosition: false,
      positionMode: 'OneWayMode'
    };
    
    const tradeOptions = { ...defaultOptions, ...options };
    
    // 將訊號動作轉換為 Bybit 交易方向
    let side;
    if (signal.action === 'buy') {
      side = 'Buy';
    } else if (signal.action === 'sell') {
      side = 'Sell';
    } else if (signal.action === 'close') {
      // 平倉邏輯 - 需要先獲取當前持倉方向
      const position = await bybitClient.getPosition({ symbol: signal.symbol });
      if (!position.result || position.result.size === 0) {
        throw new Error(`沒有找到 ${signal.symbol} 的持倉`);
      }
      
      const currentPosition = position.result[0];
      side = currentPosition.side === 'Buy' ? 'Sell' : 'Buy';
      tradeOptions.closePosition = true;
      tradeOptions.reduceOnly = true;
    } else {
      throw new Error(`不支持的交易動作: ${signal.action}`);
    }
    
    // 計算交易數量
    let quantity;
    if (tradeOptions.closePosition) {
      // 平倉時使用當前持倉數量
      const position = await bybitClient.getPosition({ symbol: signal.symbol });
      quantity = Math.abs(position.result[0].size);
    } else {
      // 使用配置的數量或計算數量
      quantity = tradeOptions.quantity || calculateQuantity(signal.symbol, signal.price);
    }
    
    // 創建交易記錄
    const trade = new Trade({
      signalId: signal._id,
      symbol: signal.symbol,
      side: side,
      orderType: tradeOptions.orderType,
      quantity: quantity,
      price: tradeOptions.orderType === 'Limit' ? signal.price : undefined,
      status: 'pending'
    });
    
    await trade.save();
    
    // 準備訂單參數
    const orderParams = {
      symbol: signal.symbol,
      side: side,
      order_type: tradeOptions.orderType,
      qty: quantity.toString(),
      time_in_force: 'GoodTillCancel',
      reduce_only: tradeOptions.reduceOnly,
      close_on_trigger: tradeOptions.closePosition
    };
    
    // 如果是限價單，添加價格
    if (tradeOptions.orderType === 'Limit') {
      orderParams.price = signal.price.toString();
    }
    
    // 執行訂單
    const orderResult = await bybitClient.placeActiveOrder(orderParams);
    
    if (!orderResult.ret_code === 0) {
      throw new Error(`Bybit API 錯誤: ${orderResult.ret_msg}`);
    }
    
    // 更新交易記錄
    trade.orderId = orderResult.result.order_id;
    trade.status = 'executed';
    trade.metadata = {
      bybitResponse: orderResult.result,
      options: tradeOptions
    };
    
    await trade.save();
    
    return {
      trade: trade,
      bybitResponse: orderResult.result
    };
  } catch (error) {
    console.error('執行 Bybit 交易時出錯:', error);
    
    // 如果已創建交易記錄，更新為失敗狀態
    if (trade && trade._id) {
      trade.status = 'failed';
      trade.error = error.message;
      await trade.save();
    }
    
    throw error;
  }
}

/**
 * 計算交易數量
 * @param {string} symbol - 交易對符號
 * @param {number} price - 當前價格
 * @returns {number} - 計算出的交易數量
 */
function calculateQuantity(symbol, price) {
  // 從環境變量獲取風險金額
  const riskAmount = parseFloat(process.env.TRADE_RISK_AMOUNT) || 100;
  
  // 根據不同交易對調整數量精度
  let precision = 3; // 默認精度
  
  if (symbol.includes('BTC')) {
    precision = 3;
  } else if (symbol.includes('ETH')) {
    precision = 2;
  } else if (symbol.includes('SOL')) {
    precision = 0;
  }
  
  // 計算數量 = 風險金額 / 價格
  const quantity = riskAmount / price;
  
  // 根據精度四捨五入
  return parseFloat(quantity.toFixed(precision));
}

module.exports = {
  executeTradeFromSignal,
  bybitClient
}; 
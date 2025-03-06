const Signal = require('../models/Signal');
const { executeTradeFromSignal } = require('./bybitTrader');

/**
 * 處理從TradingView接收的交易訊號
 * @param {Object} signalData - 從webhook接收的訊號數據
 * @returns {Promise<Object>} - 處理後的訊號對象和交易結果
 */
async function processSignal(signalData) {
  try {
    // 驗證必要欄位
    if (!signalData.symbol || !signalData.action || !signalData.price) {
      throw new Error('缺少必要的訊號欄位: symbol, action, price');
    }
    
    // 標準化數據
    const normalizedData = {
      symbol: signalData.symbol.toUpperCase(),
      action: signalData.action.toLowerCase(),
      price: parseFloat(signalData.price),
      strategy: signalData.strategy || 'unknown',
      timeframe: signalData.timeframe || 'unknown'
    };
    
    // 處理額外的元數據
    const metadata = { ...signalData };
    delete metadata.symbol;
    delete metadata.action;
    delete metadata.price;
    delete metadata.strategy;
    delete metadata.timeframe;
    
    if (Object.keys(metadata).length > 0) {
      normalizedData.metadata = metadata;
    }
    
    // 創建並保存訊號
    const signal = new Signal(normalizedData);
    await signal.save();
    
    // 檢查是否需要執行交易
    const shouldExecuteTrade = process.env.AUTO_EXECUTE_TRADES === 'true';
    
    let tradeResult = null;
    if (shouldExecuteTrade) {
      // 從訊號中提取交易選項
      const tradeOptions = {
        orderType: signalData.orderType || 'Market',
        quantity: signalData.quantity ? parseFloat(signalData.quantity) : undefined,
        leverage: signalData.leverage ? parseFloat(signalData.leverage) : 1,
        reduceOnly: signalData.reduceOnly === 'true',
        positionMode: signalData.positionMode || 'OneWayMode'
      };
      
      // 執行交易
      tradeResult = await executeTradeFromSignal(signal, tradeOptions);
    }
    
    return {
      signal,
      tradeResult
    };
  } catch (error) {
    console.error('處理訊號時出錯:', error);
    throw error;
  }
}

module.exports = {
  processSignal
}; 
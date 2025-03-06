/**
 * API密鑰認證中間件
 * 驗證請求中的API密鑰是否有效
 */
function apiKeyAuth(req, res, next) {
  const apiKey = req.headers['x-api-key'] || req.query.apiKey;
  
  // 檢查API密鑰是否存在
  if (!apiKey) {
    return res.status(401).json({ error: '缺少API密鑰' });
  }
  
  // 驗證API密鑰是否有效
  if (apiKey !== process.env.API_KEY) {
    return res.status(403).json({ error: 'API密鑰無效' });
  }
  
  // 認證通過，繼續處理請求
  next();
}

module.exports = {
  apiKeyAuth
}; 
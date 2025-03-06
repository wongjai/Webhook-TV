const mongoose = require('mongoose');

const tradeSchema = new mongoose.Schema({
  signalId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Signal',
    required: true
  },
  symbol: {
    type: String,
    required: true,
    trim: true
  },
  side: {
    type: String,
    required: true,
    enum: ['Buy', 'Sell'],
  },
  orderType: {
    type: String,
    required: true,
    enum: ['Market', 'Limit'],
    default: 'Market'
  },
  quantity: {
    type: Number,
    required: true
  },
  price: {
    type: Number,
    required: false
  },
  orderId: {
    type: String,
    required: false
  },
  status: {
    type: String,
    required: true,
    enum: ['pending', 'executed', 'failed', 'cancelled'],
    default: 'pending'
  },
  executedPrice: {
    type: Number,
    required: false
  },
  error: {
    type: String,
    required: false
  },
  metadata: {
    type: Map,
    of: mongoose.Schema.Types.Mixed,
    default: {}
  }
}, {
  timestamps: true
});

// 索引以提高查詢效率
tradeSchema.index({ signalId: 1 });
tradeSchema.index({ status: 1 });
tradeSchema.index({ symbol: 1, createdAt: -1 });

const Trade = mongoose.model('Trade', tradeSchema);

module.exports = Trade; 
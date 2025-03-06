const mongoose = require('mongoose');

const signalSchema = new mongoose.Schema({
  symbol: {
    type: String,
    required: true,
    trim: true
  },
  action: {
    type: String,
    required: true,
    enum: ['buy', 'sell', 'close', 'alert'],
    lowercase: true
  },
  price: {
    type: Number,
    required: true
  },
  timestamp: {
    type: Date,
    default: Date.now
  },
  strategy: {
    type: String,
    required: false,
    trim: true
  },
  timeframe: {
    type: String,
    required: false,
    trim: true
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
signalSchema.index({ symbol: 1, timestamp: -1 });
signalSchema.index({ action: 1 });

const Signal = mongoose.model('Signal', signalSchema);

module.exports = Signal; 
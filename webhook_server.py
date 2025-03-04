# webhook_server.py
from fastapi import FastAPI, Request, HTTPException, Depends
from bybit_trading import execute_trade, modify_trade, close_trade, get_account_details
from database import get_db, update_bot_config, get_bot_config, log_trade_mode_change, TradeHistory, get_open_trades, get_closed_trades
from config import TELEGRAM_CHAT_ID, TRADE_MODE
from sqlalchemy.orm import Session
import logging
import json
import asyncio

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/webhook/open_trade")
async def open_trade_webhook(request: Request, db: Session = Depends(get_db)):
    """Handles opening a new trade based on a TradingView alert."""
    try:
        data = await request.json()
        logger.info(f"Received open_trade webhook: {data}")

        # --- Basic Validation ---
        #  (Add more robust validation based on your TradingView alert format)
        required_keys = ["symbol", "side", "quantity", "entry_price"]
        if not all(key in data for key in required_keys):
            raise HTTPException(status_code=400, detail="Invalid request data. Missing required keys.")

        if data["side"].lower() not in ["buy", "sell"]:
            raise HTTPException(status_code=400, detail="Invalid 'side' value. Must be 'buy' or 'sell'.")

        # Get current bot config
        config = get_bot_config(db)
        if config.trade_mode != "mainnet" and TRADE_MODE == "mainnet":
            return {"message":"Trade mode is not mainnet, not opening trade in mainnet"}

        # --- Execute Trade ---
        trade_id = execute_trade(
            symbol=data["symbol"],
            side=data["side"].capitalize(),  # "Buy" or "Sell"
            quantity=float(data["quantity"]),
            leverage=config.leverage,
            entry_price = float(data['entry_price'])
        )

        if trade_id:
            return {"message": f"Trade opened successfully. Trade ID: {trade_id}"}
        else:
            raise HTTPException(status_code=500, detail="Trade execution failed.")


    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format.")
    except Exception as e:
        logger.exception(f"An error occurred in open_trade_webhook: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/webhook/take_profit")
async def take_profit_webhook(request: Request, db: Session = Depends(get_db)):
    """Handles take profit events."""
    data = await request.json()
    logger.info(f"Received take_profit webhook: {data}")
    # Get current bot config
    config = get_bot_config(db)
    if config.trade_mode != "mainnet" and TRADE_MODE == "mainnet":
        return {"message":"Trade mode is not mainnet, not taking profit in mainnet"}

    # Assuming data includes: symbol, order_id, take_profit_price
    required_keys = ["symbol", "order_id", "take_profit_price"]
    if not all(key in data for key in required_keys):
      raise HTTPException(status_code=400, detail="Invalid request data. Missing required keys.")

    success = modify_trade(data['symbol'], data['order_id'], take_profit=float(data['take_profit_price']))
    if success:
      return {"message": "Take profit set successfully."}
    else:
      return {"message": "Failed to set take profit."}
@app.post("/webhook/stop_loss")
async def stop_loss_webhook(request: Request, db: Session = Depends(get_db)):
    """Handles stop loss events."""
    data = await request.json()
    logger.info(f"Received stop_loss webhook: {data}")
    # Get current bot config
    config = get_bot_config(db)
    if config.trade_mode != "mainnet" and TRADE_MODE == "mainnet":
        return {"message":"Trade mode is not mainnet, not setting stop loss in mainnet"}

    # Assuming data includes: symbol, order_id, stop_loss_price
    required_keys = ["symbol", "order_id", "stop_loss_price"]
    if not all(key in data for key in required_keys):
      raise HTTPException(status_code=400, detail="Invalid request data. Missing required keys.")

    success = modify_trade(data['symbol'], data['order_id'], stop_loss=float(data['stop_loss_price']))

    if success:
        return {"message": "Stop loss set successfully."}
    else:
        return {"message": "Failed to set stop loss."}
@app.post("/webhook/close_trade")
async def close_trade_webhook(request: Request, db: Session = Depends(get_db)):
    """Handles closing a trade."""
    data = await request.json()
    logger.info(f"Received close_trade webhook: {data}")

    # Get current bot config
    config = get_bot_config(db)
    if config.trade_mode != "mainnet" and TRADE_MODE == "mainnet":
        return {"message":"Trade mode is not mainnet, not closing trade in mainnet"}

    # Assuming data includes: symbol, order_id, exit_price
    required_keys = ["symbol", "order_id", "exit_price"]
    if not all(key in data for key in required_keys):
      raise HTTPException(status_code=400, detail="Invalid request data. Missing required keys.")


    success = close_trade(data['symbol'], data['order_id'], float(data['exit_price']))
    if success:
        return {"message": "Trade closed successfully."}
    else:
        return {"message": "Failed to close trade."}

@app.get("/")
async def root():
  return {"message": "Webhook server is running."}

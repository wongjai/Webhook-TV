# main.py (Corrected)
from fastapi import FastAPI, Request, HTTPException, Depends, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from bybit_trading import execute_trade, modify_trade, close_trade, get_account_details, get_trade_history
from database import get_db, update_bot_config, get_bot_config, log_trade_mode_change, TradeHistory, get_open_trades, get_closed_trades
from config import TELEGRAM_CHAT_ID, TRADE_MODE, TELEGRAM_BOT_TOKEN # Import TELEGRAM_BOT_TOKEN
from sqlalchemy.orm import Session
import logging
import json
import asyncio

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="templates")

# --- Helper Functions --- (Adapt from previous telegram_bot.py and webhook_server.py)

async def send_telegram_message(message: str):
    """Sends a message to Telegram (Placeholder - Adapt from your previous code)."""
    logger.DEBUG(f"Sending Telegram message: {message}")  # Keep logging
    #  You'll likely use the python-telegram-bot library here
    #  Example (requires installation: pip install python-telegram-bot):
    try:
        from telegram import Bot  # Import here to avoid errors if not installed
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except ImportError:
        logger.error("python-telegram-bot library not installed.  Install to send messages.")
    except Exception as e:
        logger.exception(f"Error sending Telegram message: {e}")

# --- Webhook Endpoints (Keep and adapt from webhook_server.py) ---

@app.post("/webhook/open_trade", include_in_schema=False)  # Hide from OpenAPI docs
async def open_trade_webhook(request: Request, db: Session = Depends(get_db)):
    """Handles opening a new trade based on a TradingView alert."""
    try:
        data = await request.json()
        logger.DEBUG(f"Received open_trade webhook: {data}")

        # --- Basic Validation ---
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
            await send_telegram_message(f"✅ Opened trade: {data['side']} {data['quantity']} {data['symbol']} @ {data['entry_price']}")
            return {"message": f"Trade opened successfully. Trade ID: {trade_id}"}
        else:
            raise HTTPException(status_code=500, detail="Trade execution failed.")


    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format.")
    except Exception as e:
        logger.exception(f"An error occurred in open_trade_webhook: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/webhook/take_profit", include_in_schema=False)
async def take_profit_webhook(request: Request, db: Session = Depends(get_db)):
    """Handles take profit events."""
    data = await request.json()
    logger.DEBUG(f"Received take_profit webhook: {data}")
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
      await send_telegram_message(f"⬆️ Take profit set for {data['symbol']} at {data['take_profit_price']}")
      return {"message": "Take profit set successfully."}
    else:
      return {"message": "Failed to set take profit."}

@app.post("/webhook/stop_loss", include_in_schema=False)
async def stop_loss_webhook(request: Request, db: Session = Depends(get_db)):
    """Handles stop loss events."""
    data = await request.json()
    logger.DEBUG(f"Received stop_loss webhook: {data}")
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
        await send_telegram_message(f"⬇️ Stop loss set for {data['symbol']} at {data['stop_loss_price']}")
        return {"message": "Stop loss set successfully."}
    else:
        return {"message": "Failed to set stop loss."}

@app.post("/webhook/close_trade", include_in_schema=False)
async def close_trade_webhook(request: Request, db: Session = Depends(get_db)):
    """Handles closing a trade."""
    data = await request.json()
    logger.DEBUG(f"Received close_trade webhook: {data}")

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
        await send_telegram_message(f"⛔ Closed trade: {data['symbol']} at {data['exit_price']}")
        return {"message": "Trade closed successfully."}
    else:
        return {"message": "Failed to close trade."}

# --- Dashboard Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    """Serves the main dashboard page."""
    config = get_bot_config(db)
    balances, open_positions = get_account_details()  # Get all balances
    if balances is None:
        balances = {}  # Handle potential errors

    return templates.TemplateResponse("index.html", {
        "request": request,
        "trade_mode": config.trade_mode,
        "risk_per_trade": config.risk_per_trade,
        "tp1": config.tp1,
        "tp2": config.tp2,
        "tp3": config.tp3,
        "tp4": config.tp4,
        "stop_loss": config.stop_loss,
        "leverage": config.leverage,
        "balances": balances,  # Pass the balances dictionary
        "open_positions": open_positions
    })

@app.post("/update_config")
async def update_config_route(
    db: Session = Depends(get_db),
    trade_mode: str = Form(...),
    risk_per_trade: float = Form(...),
    tp1: float = Form(...),
    tp2: float = Form(...),
    tp3: float = Form(...),
    tp4: float = Form(...),
    stop_loss: float = Form(...),
    leverage: int = Form(...),
):
    """Updates the bot configuration via a form submission."""
    # Basic validation
    if trade_mode not in ["testnet", "mainnet"]:
        raise HTTPException(status_code=400, detail="Invalid trade mode")
    if not all(0 < tp < 5 for tp in [tp1, tp2, tp3, tp4]): # Example validation
        raise HTTPException(status_code=400, detail="Invalid TP levels")
    # ... add more validation as needed ...

    update_bot_config(db, {
        "trade_mode": trade_mode,
        "risk_per_trade": risk_per_trade,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "tp4": tp4,
        "stop_loss": stop_loss,
        "leverage": leverage,
    })

    # Log trade mode change if it occurred
    current_config = get_bot_config(db)
    if current_config.trade_mode != trade_mode:
        log_trade_mode_change(db, trade_mode, "Web Dashboard")  # Log user as "Web Dashboard"

    return RedirectResponse("/", status_code=303)  # Redirect back to the main page

@app.get("/trade_history/{symbol}")
async def get_trade_history_route(symbol: str, db: Session = Depends(get_db)):
    """Returns trade history for a given symbol as JSON."""
    if symbol not in ["BTCUSDT", "ETHUSDT"]:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    trades = get_closed_trades(db, symbol=symbol)

    # Convert trade objects to dictionaries for JSON serialization
    trade_list = [
        {
            "id": trade.id,
            "symbol": trade.symbol,
            "side": trade.side,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "quantity": trade.quantity,
            "leverage": trade.leverage,
            "pnl": trade.pnl,
            "commission": trade.commission,
            "open_time": trade.open_time.isoformat() if trade.open_time else None,  # Format dates
            "close_time": trade.close_time.isoformat() if trade.close_time else None,
            "is_open": trade.is_open,
        }
        for trade in trades
    ]
    return trade_list

@app.post("/kill_switch")
async def kill_switch_route(db: Session = Depends(get_db)):
    """Activates the Kill Switch (forces Demo Mode)."""
    log_trade_mode_change(db, 'testnet', "Web Dashboard")
    update_bot_config(db, {'trade_mode': 'testnet'})
    await send_telegram_message("🚨 Kill Switch Activated via Web Dashboard! 🚨\nTrading is now in Demo Mode.")
    return {"message": "Kill Switch Activated"}

# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Bybit API Settings
TRADE_MODE = os.getenv("TRADE_MODE", "testnet")  # Default to testnet if not set

BYBIT_MAINNET_API_KEY = os.getenv("BYBIT_MAINNET_API_KEY")
BYBIT_MAINNET_SECRET_KEY = os.getenv("BYBIT_MAINNET_SECRET_KEY")
BYBIT_MAINNET_REST_URL = os.getenv("BYBIT_MAINNET_REST_URL")
BYBIT_MAINNET_WS_URL = os.getenv("BYBIT_MAINNET_WS_URL")

BYBIT_TESTNET_API_KEY = os.getenv("BYBIT_TESTNET_API_KEY")
BYBIT_TESTNET_SECRET_KEY = os.getenv("BYBIT_TESTNET_SECRET_KEY")
BYBIT_TESTNET_REST_URL = os.getenv("BYBIT_TESTNET_REST_URL")
BYBIT_TESTNET_WS_URL = os.getenv("BYBIT_TESTNET_WS_URL")

# Database Settings
DATABASE_URL = os.getenv("DATABASE_URL")

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Derived Settings (Conditional based on TRADE_MODE)
if TRADE_MODE == "mainnet":
    BYBIT_API_KEY = BYBIT_MAINNET_API_KEY
    BYBIT_SECRET_KEY = BYBIT_MAINNET_SECRET_KEY
    BYBIT_REST_URL = BYBIT_MAINNET_REST_URL
    BYBIT_WS_URL = BYBIT_MAINNET_WS_URL
elif TRADE_MODE == "testnet":
    BYBIT_API_KEY = BYBIT_TESTNET_API_KEY
    BYBIT_SECRET_KEY = BYBIT_TESTNET_SECRET_KEY
    BYBIT_REST_URL = BYBIT_TESTNET_REST_URL
    BYBIT_WS_URL = BYBIT_TESTNET_WS_URL
else:
    raise ValueError("Invalid TRADE_MODE. Must be 'mainnet' or 'testnet'.")

# Default Trading Settings (can be overridden by Telegram bot)
DEFAULT_RISK_PER_TRADE = 0.01  # 1%
DEFAULT_TAKE_PROFIT_LEVELS = [1.01, 1.02, 1.03, 1.04]  # Example TP levels
DEFAULT_STOP_LOSS_LEVEL = 0.99  # Example SL level
DEFAULT_LEVERAGE = 10

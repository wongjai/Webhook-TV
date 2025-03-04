# database.py
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class BotConfig(Base):
    __tablename__ = "bot_config"

    id = Column(Integer, primary_key=True)
    risk_per_trade = Column(Float, default=0.01)
    tp1 = Column(Float, default=1.01)
    tp2 = Column(Float, default=1.02)
    tp3 = Column(Float, default=1.03)
    tp4 = Column(Float, default=1.04)
    stop_loss = Column(Float, default=0.99)
    leverage = Column(Integer, default=10)
    trade_mode = Column(String, default="testnet")  # 'testnet' or 'mainnet'

class TradeHistory(Base):
    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True)
    symbol = Column(String)  # e.g., "BTCUSDT"
    side = Column(String)  # "Buy" or "Sell"
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float)
    leverage = Column(Integer)
    pnl = Column(Float, nullable=True)
    commission = Column(Float, nullable=True)
    open_time = Column(DateTime, default=datetime.datetime.utcnow)
    close_time = Column(DateTime, nullable=True)
    is_open = Column(Boolean, default=True) # Added to track open/closed status

class TradeModeLog(Base):
    __tablename__ = "trade_mode_log"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    trade_mode = Column(String)  # 'testnet' or 'mainnet'
    user_id = Column(String) # Telegram user ID who initiated the change.

# Create tables
Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_bot_config(db):
     # Get the latest bot config, or create a default one if none exists
    config = db.query(BotConfig).order_by(BotConfig.id.desc()).first()
    if not config:
        config = BotConfig() # Use default values
        db.add(config)
        db.commit()
        db.refresh(config) # Get the ID assigned
    return config

def update_bot_config(db, new_config: dict):
    config = get_bot_config(db)
    for key, value in new_config.items():
        if hasattr(config, key):  # Make sure the attribute exists
            setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config

def log_trade_mode_change(db, trade_mode: str, user_id: str):
    log_entry = TradeModeLog(trade_mode=trade_mode, user_id=user_id)
    db.add(log_entry)
    db.commit()

def add_trade_to_history(db, trade_data: dict):
    trade = TradeHistory(**trade_data)
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade

def update_trade_in_history(db, trade_id: int, update_data: dict):
    trade = db.query(TradeHistory).filter(TradeHistory.id == trade_id).first()
    if trade:
        for key, value in update_data.items():
            if hasattr(trade, key):
                setattr(trade, key, value)
        db.commit()
        db.refresh(trade)
    return trade

def get_open_trades(db, symbol:str = None):
    query = db.query(TradeHistory).filter(TradeHistory.is_open == True)
    if symbol:
        query = query.filter(TradeHistory.symbol == symbol)
    return query.all()

def get_closed_trades(db, symbol: str = None, limit: int = 50):
     query = db.query(TradeHistory).filter(TradeHistory.is_open == False).order_by(TradeHistory.close_time.desc())
     if symbol:
         query = query.filter(TradeHistory.symbol == symbol)
     return query.limit(limit).all()

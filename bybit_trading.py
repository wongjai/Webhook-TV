# bybit_trading.py
from pybit.unified_trading import HTTP
from config import BYBIT_API_KEY, BYBIT_SECRET_KEY, BYBIT_REST_URL
import logging
from database import add_trade_to_history, update_trade_in_history, get_db, get_open_trades
import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Bybit client
client = HTTP(
    testnet=BYBIT_REST_URL.startswith("https://api-testnet"),
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_SECRET_KEY,
)

def get_account_details():
    """Fetches account balances for ALL coins and open positions."""
    try:
        response = client.get_wallet_balance(accountType="UNIFIED")  # Remove coin=USDT
        logger.debug(f"Account details response: {response}")

        if response['retCode'] == 0:
            result_list = response.get('result', {}).get('list', [])
            if not result_list:
                logger.warning("No 'list' found in API response.")
                return None, None

            balances = {}  # Store balances as a dictionary: {coin: balance}
            for coin_data in result_list[0].get('coin', []):
                coin_symbol = coin_data.get('coin')
                if not coin_symbol:
                    continue  # Skip if no coin symbol

                # Prioritize availableToWithdraw, then free, then walletBalance
                balance = 0.0
                try:
                    available_to_withdraw = coin_data.get('availableToWithdraw')
                    if available_to_withdraw:
                        balance = float(available_to_withdraw)
                    else:
                        free_balance = coin_data.get('free')
                        if free_balance:
                            balance = float(free_balance)
                        else:
                            wallet_balance = coin_data.get('walletBalance')
                            if wallet_balance:
                                balance = float(wallet_balance)

                except (ValueError, TypeError):
                    logger.warning(f"Could not convert balance to float for {coin_symbol}: {coin_data}")
                    #  Don't set balance to 0 here, as it might overwrite a valid fallback

                balances[coin_symbol] = balance # Store the balance

            # Get open positions (same as before, but consider filtering by symbol)
            positions_response = client.get_positions(category="linear", settleCoin="USDT")  # Or filter by multiple coins
            open_positions = []
            if positions_response['retCode'] == 0:
                for pos in positions_response['result']['list']:
                    if float(pos['size']) > 0:
                        open_positions.append(pos)

            return balances, open_positions  # Return balances dictionary

        else:
            logger.error(f"Failed to get account details: {response}")
            return None, None

    except Exception as e:
        logger.exception(f"An error occurred while fetching account details: {e}")
        return None, None

def execute_trade(symbol: str, side: str, quantity: float, leverage: int, entry_price: float):
    """Places a market order on Bybit."""
    try:
        # Set leverage FIRST
        client.set_leverage(category="linear", symbol=symbol, buyLeverage=str(leverage), sellLeverage=str(leverage))

        response = client.place_order(
            category="linear",
            symbol=symbol,
            side=side,
            orderType="Market",
            qty=str(quantity),  # Bybit API expects strings for quantities
        )
        logger.DEBUG(f"Trade executed: {response}")

        # Check for success
        if response['retCode'] == 0:
            trade_id = response['result']['orderId']
            # Log to database
            db = next(get_db()) # Obtain a DB session
            trade_data = {
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'quantity': quantity,
                'leverage': leverage,
                'is_open': True
            }
            add_trade_to_history(db, trade_data)
            db.close()
            return trade_id
        else:
            logger.error(f"Trade execution failed: {response}")
            return None

    except Exception as e:
        logger.exception(f"An error occurred during trade execution: {e}")
        return None

def modify_trade(symbol: str, order_id: str, stop_loss: float = None, take_profit: float = None):
    """Modifies stop loss and take profit for an existing order."""
    try:
        # Construct the update data - only send if values are provided
        update_data = {}
        if stop_loss is not None:
          update_data["stopLoss"] = str(stop_loss)
        if take_profit is not None:
          update_data["takeProfit"] = str(take_profit)

        if update_data: # Only make the API call if we have something to update.
            response = client.amend_order(
                category="linear",
                symbol=symbol,
                orderId=order_id,
                **update_data
            )
            logger.DEBUG(f"Trade modified: {response}")

            if response['retCode'] == 0:
                return True
            else:
                logger.error(f"Trade modification failed: {response}")
                return False
        else:
            logger.DEBUG("No SL/TP values provided to modify_trade. Skipping.")
            return True # Consider it successful if nothing needed updating.

    except Exception as e:
        logger.exception(f"An error occurred during trade modification: {e}")
        return False

def close_trade(symbol: str, order_id:str, exit_price:float):
    """Closes an open position (market order)."""
    # 1. Get order details to determine side and quantity
    try:
        order_details = client.get_open_orders(category="linear", symbol=symbol, orderId=order_id)
        if order_details['retCode'] != 0 or not order_details['result']['list']:
            logger.error(f"Could not retrieve order details for {order_id}: {order_details}")
            return False

        order_DEBUG = order_details['result']['list'][0] # Assuming the first item is the relevant order
        side = order_DEBUG['side']
        qty = order_DEBUG['qty']
        close_side = "Sell" if side == "Buy" else "Buy"

        # 2.  Place a market order to close the position
        response = client.place_order(
            category="linear",
            symbol=symbol,
            side=close_side,
            orderType="Market",
            qty=qty,
            reduceOnly=True, # Important: Set reduceOnly to True for closing positions
        )
        logger.DEBUG(f"Trade close request sent: {response}")

        if response['retCode'] == 0:
            # 3. Update database
            db = next(get_db())  # Get a DB session
            trade = get_open_trades(db, symbol) # Find the open trade
            if trade:
              trade = trade[0]
              update_data = {
                  'exit_price': exit_price,
                  'close_time': datetime.datetime.utcnow(),
                  'is_open': False,
                  # You might calculate PnL and commission here, or in a separate function
              }
              update_trade_in_history(db, trade.id, update_data)
            db.close()
            return True
        else:
            logger.error(f"Trade close failed: {response}")
            return False

    except Exception as e:
        logger.exception(f"Error during close_trade: {e}")
        return False

def get_trade_history(symbol: str = None, limit: int = 50):
    """Retrieves trade history, optionally filtered by symbol."""
    try:
        # Note: Bybit's API for *execution* history is different from *order* history.
        # We want execution history to see actual fills.
        response = client.get_executions(category="linear", symbol=symbol, limit=limit)
        logger.debug(f"Trade history response: {response}")

        if response['retCode'] == 0:
            return response['result']['list']
        else:
            logger.error(f"Failed to get trade history: {response}")
            return []

    except Exception as e:
        logger.exception(f"An error occurred while fetching trade history: {e}")
        return []

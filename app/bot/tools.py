import pandas as pd
import yfinance as yf
from agents import function_tool
from loguru import logger

def calculate_rsi(data, period=14):
    try:
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except Exception as e:
        logger.error(f"Error calculating RSI: {str(e)}")
        return None

def calculate_macd(data, fast=12, slow=26, signal=9):
    try:
        ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    except Exception as e:
        logger.error(f"Error calculating MACD: {str(e)}")
        return None, None, None

@function_tool
def get_stock_context(ticker_symbol: str) -> dict | None:
    """Get technical and fundamental context for a stock ticker.

    Fetches stock data using yfinance and calculates technical indicators including RSI and MACD.
    Used to analyze stocks for swing trading opportunities.

    Args:
        ticker_symbol (str): The stock ticker symbol to analyze.

    Returns:
        dict: A dictionary containing:
            price (float): Current regular market price
            52w_high (float): 52-week high price
            52w_low (float): 52-week low price 
            volume (int): Current trading volume
            avg_volume (int): Average daily trading volume
            beta (float): Beta value relative to market
            market_cap (int): Market capitalization
            earnings_date (dict): Next earnings report date
            sector (str): Company sector classification
            industry (str): Company industry classification
            rsi (float): 14-period Relative Strength Index value
            macd (dict): Moving Average Convergence Divergence values
                macd (float): MACD line value (12,26)
                signal (float): Signal line value (9-period)
                hist (float): MACD histogram value

    Returns None if there is an error fetching or calculating the data.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        data = ticker.history(period="3mo", interval="1d")

        # Calculate RSI and MACD using pandas only
        data['RSI'] = calculate_rsi(data)
        macd, signal_line, hist = calculate_macd(data)
        data['MACD'] = macd
        data['MACD_signal'] = signal_line
        data['MACD_hist'] = hist

        return {
            "price": info.get("regularMarketPrice"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "volume": info.get("volume"),
            "avg_volume": info.get("averageVolume"),
            "beta": info.get("beta"),
            "market_cap": info.get("marketCap"),
            "earnings_date": ticker.calendar,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "rsi": data['RSI'].iloc[-1] if not data['RSI'].empty else None,
            "macd": {
                "macd": data['MACD'].iloc[-1] if not data['MACD'].empty else None,
                "signal": data['MACD_signal'].iloc[-1] if not data['MACD_signal'].empty else None,
                "hist": data['MACD_hist'].iloc[-1] if not data['MACD_hist'].empty else None,
            }
        }
    except Exception as e:
        logger.error(f"Error getting stock context for {ticker_symbol}: {str(e)}")
        return None
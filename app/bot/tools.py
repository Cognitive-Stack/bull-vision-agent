from vnstock import Vnstock
import pandas as pd
from agents import function_tool
from loguru import logger

def calculate_rsi(data, period=14):
    try:
        delta = data['close'].diff()
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
        ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    except Exception as e:
        logger.error(f"Error calculating MACD: {str(e)}")
        return None, None, None

@function_tool
def get_stock_context(symbol: str):
    """Get technical and fundamental context for a stock ticker.

    Fetches stock data using vnstock and calculates technical indicators including RSI and MACD.
    Used to analyze stocks for swing trading opportunities.

    Args:
        symbol (str): The stock ticker symbol to analyze.

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
        # Fetch historical daily data for the last 3 months
        if not symbol:
            raise ValueError("Symbol is required")
        logger.info(f"Symbol: {symbol}")
        stock = Vnstock().stock(symbol=symbol, source='TCBS')
        logger.info(f"Stock: {stock}")
        start_date = str((pd.Timestamp.now() - pd.Timedelta(days=90)).date())
        end_date = str(pd.Timestamp.now().date())
        logger.info(f"Start date: {start_date}, End date: {end_date}")
        df = stock.quote.history(interval='1D', start=start_date, end=end_date)
        logger.info(f"DF: {df}")
        df = df.rename(columns=str.lower)

        # Calculate indicators
        df['RSI'] = calculate_rsi(df)
        macd, signal, hist = calculate_macd(df)
        df['MACD'] = macd
        df['MACD_signal'] = signal
        df['MACD_hist'] = hist

        # Get latest row
        latest = df.iloc[-1] if not df.empty else {}

        # Get company info
        company_df = stock.company.overview() if hasattr(stock, 'company') else None
        if company_df is not None and not company_df.empty:
            company = company_df.iloc[0].to_dict()
        else:
            company = {}

        result = {
            "price": latest.get("close"),
            "52w_high": df['high'].rolling(window=252, min_periods=1).max().iloc[-1] if not df.empty else None,
            "52w_low": df['low'].rolling(window=252, min_periods=1).min().iloc[-1] if not df.empty else None,
            "volume": latest.get("volume"),
            "avg_volume": df['volume'].rolling(window=20, min_periods=1).mean().iloc[-1] if not df.empty else None,
            "rsi": latest.get("RSI"),
            "macd": {
                "macd": latest.get("MACD"),
                "signal": latest.get("MACD_signal"),
                "hist": latest.get("MACD_hist"),
            },
            "sector": company.get("sector") if company else None,
            "industry": company.get("industry") if company else None,
            "market_cap": company.get("market_cap") if company else None,
            "earnings_date": company.get("earnings_date") if company else None,
        }
        logger.info(f"Stock context for {symbol}: {result}")
        return result
    except Exception as e:
        logger.error(f"Error getting stock context for {symbol}: {str(e)}")
        return None
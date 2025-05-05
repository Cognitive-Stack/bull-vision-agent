from vnstock import Vnstock, Listing, Trading, Company, Screener
import pandas as pd
from agents import function_tool
from loguru import logger
from vnstock.explorer.misc import vcb_exchange_rate, sjc_gold_price

def calculate_rsi(data, period=14):
    """Calculate the Relative Strength Index (RSI) for a given DataFrame of stock prices."""
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
    """Calculate the MACD, signal line, and histogram for a given DataFrame of stock prices."""
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

        df['RSI'] = calculate_rsi(df)
        macd, signal, hist = calculate_macd(df)
        df['MACD'] = macd
        df['MACD_signal'] = signal
        df['MACD_hist'] = hist

        latest = df.iloc[-1] if not df.empty else {}

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

@function_tool
def get_all_symbols():
    """
    Get a list of all available stock symbols on the Vietnamese market.

    Returns:
        list: List of ticker symbols.
    """
    try:
        listing = Listing()
        return listing.all_symbols()
    except Exception as e:
        logger.error(f"Error in get_all_symbols: {str(e)}")
        return []

@function_tool
def get_price_board(symbols):
    """
    Get real-time price board for a list of ticker symbols.

    Args:
        symbols (list): List of ticker strings, e.g. ['VCB', 'ACB', 'TCB']

    Returns:
        DataFrame: Real-time price board data.
    """
    try:
        board = Trading(source='VCI').price_board(symbols)
        return board
    except Exception as e:
        logger.error(f"Error in get_price_board: {str(e)}")
        return None

@function_tool
def get_company_overview(symbol):
    """
    Get detailed company overview information for a given symbol.

    Args:
        symbol (str): The stock ticker symbol.

    Returns:
        DataFrame: Company overview data.
    """
    try:
        company = Company(symbol=symbol, source='VCI')
        return company.overview()
    except Exception as e:
        logger.error(f"Error in get_company_overview: {str(e)}")
        return None

@function_tool
def get_balance_sheet(symbol, period='year', lang='en'):
    """
    Get the balance sheet for a company.

    Args:
        symbol (str): The stock ticker symbol.
        period (str): 'year' or 'quarter'.
        lang (str): Language, 'en' or 'vi'.

    Returns:
        DataFrame: Balance sheet data.
    """
    try:
        stock = Vnstock().stock(symbol=symbol, source='VCI')
        return stock.finance.balance_sheet(period=period, lang=lang, dropna=True)
    except Exception as e:
        logger.error(f"Error in get_balance_sheet: {str(e)}")
        return None

@function_tool
def get_income_statement(symbol, period='year', lang='en'):
    """
    Get the income statement for a company.

    Args:
        symbol (str): The stock ticker symbol.
        period (str): 'year' or 'quarter'.
        lang (str): Language, 'en' or 'vi'.

    Returns:
        DataFrame: Income statement data.
    """
    stock = Vnstock().stock(symbol=symbol, source='VCI')
    return stock.finance.income_statement(period=period, lang=lang, dropna=True)

@function_tool
def get_cash_flow(symbol, period='year'):
    """
    Get the cash flow statement for a company.

    Args:
        symbol (str): The stock ticker symbol.
        period (str): 'year' or 'quarter'.

    Returns:
        DataFrame: Cash flow data.
    """
    stock = Vnstock().stock(symbol=symbol, source='VCI')
    return stock.finance.cash_flow(period=period, dropna=True)

@function_tool
def get_financial_ratios(symbol, period='year', lang='en'):
    """
    Get financial ratios for a company.

    Args:
        symbol (str): The stock ticker symbol.
        period (str): 'year' or 'quarter'.
        lang (str): Language, 'en' or 'vi'.

    Returns:
        DataFrame: Financial ratios data.
    """
    stock = Vnstock().stock(symbol=symbol, source='VCI')
    return stock.finance.ratio(period=period, lang=lang, dropna=True)

@function_tool
def get_market_indices():
    """
    Get real-time data for major Vietnamese market indices (VNIndex, HNX, UPCOM).

    Returns:
        DataFrame: Indices price board data.
    """
    return Trading(source='VCI').price_board(['VNINDEX', 'HNX', 'UPCOM'])

@function_tool
def screen_stocks(params=None, limit=100):
    """
    Screen stocks based on custom parameters.

    Args:
        params (dict): Screening parameters, e.g. {"exchangeName": "HOSE,HNX,UPCOM"}
        limit (int): Maximum number of results.

    Returns:
        DataFrame: Screener results.
    """
    screener = Screener()
    return screener.stock(params=params or {"exchangeName": "HOSE,HNX,UPCOM"}, limit=limit)

@function_tool
def get_intraday_ticks(symbol, page_size=10000):
    """
    Get intraday tick data for a stock.

    Args:
        symbol (str): The stock ticker symbol.
        page_size (int): Number of ticks to fetch.

    Returns:
        DataFrame: Intraday tick data.
    """
    stock = Vnstock().stock(symbol=symbol, source='VCI')
    return stock.quote.intraday(symbol=symbol, page_size=page_size, show_log=False)

@function_tool
def get_fund_listings():
    """
    Get a list of all mutual funds listed on the Vietnamese market.

    Returns:
        DataFrame: Fund listing data.
    """
    from vnstock.explorer.fmarket.fund import Fund
    fund = Fund()
    return fund.listing()

@function_tool
def get_vcb_exchange_rate(date):
    """
    Get the VCB exchange rate for a specific date.

    Args:
        date (str): Date in 'YYYY-MM-DD' format.

    Returns:
        DataFrame: Exchange rate data.
    """
    return vcb_exchange_rate(date=date)

@function_tool
def get_sjc_gold_price():
    """
    Get the current SJC gold price.

    Returns:
        DataFrame: Gold price data.
    """
    return sjc_gold_price()
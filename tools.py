import yfinance as yf
import pandas as pd
import ta
from config import TRADING_CONFIG


def get_market_data(ticker: str, period: str = "3mo", interval: str = "1d") -> dict:
    """Fetch OHLCV data and compute technical indicators."""
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    if df.empty:
        return {"error": f"No data for {ticker}"}

    # Flatten multi-level columns produced by yfinance >= 0.2.x
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    close = df["Close"].squeeze()
    df["rsi"] = ta.momentum.RSIIndicator(close).rsi()
    macd = ta.trend.MACD(close)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    bb = ta.volatility.BollingerBands(close)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["sma_20"] = ta.trend.SMAIndicator(close, window=20).sma_indicator()
    df["sma_50"] = ta.trend.SMAIndicator(close, window=50).sma_indicator()

    latest = df.iloc[-1]
    return {
        "ticker": ticker,
        "current_price": round(float(latest["Close"]), 2),
        "rsi": round(float(latest["rsi"]), 2),
        "macd": round(float(latest["macd"]), 4),
        "macd_signal": round(float(latest["macd_signal"]), 4),
        "bb_upper": round(float(latest["bb_upper"]), 2),
        "bb_lower": round(float(latest["bb_lower"]), 2),
        "sma_20": round(float(latest["sma_20"]), 2),
        "sma_50": round(float(latest["sma_50"]), 2),
        "volume": int(latest["Volume"]),
    }


def calculate_position_size(price: float, stop_loss_pct: float = 0.02) -> dict:
    """Calculate position size based on risk management rules."""
    capital = TRADING_CONFIG["max_position_size"]
    risk_amount = capital * TRADING_CONFIG["risk_per_trade"]
    stop_loss_amount = price * stop_loss_pct
    shares = int(risk_amount / stop_loss_amount)
    return {
        "shares": shares,
        "total_value": round(shares * price, 2),
        "risk_amount": round(risk_amount, 2),
        "stop_loss_price": round(price * (1 - stop_loss_pct), 2),
    }


def execute_order(ticker: str, action: str, shares: int, price: float) -> dict:
    """Execute a paper or live trade order."""
    if TRADING_CONFIG["paper_trading"]:
        return {
            "status": "paper_executed",
            "ticker": ticker,
            "action": action,
            "shares": shares,
            "price": price,
            "total": round(shares * price, 2),
        }
    # Live trading integration point (e.g., Alpaca, IBKR)
    raise NotImplementedError("Live trading not configured. Set PAPER_TRADING=false and add broker integration.")

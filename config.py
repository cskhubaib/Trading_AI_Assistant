import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

LLM_CONFIG = {
    "model": "gemini-2.5-flash",
    "interactions_url": "https://generativelanguage.googleapis.com/v1beta/interactions",
    "api_key": GEMINI_API_KEY,
}

TRADING_CONFIG = {
    "broker_api_key": os.getenv("BROKER_API_KEY"),
    "broker_secret": os.getenv("BROKER_SECRET"),
    "paper_trading": os.getenv("PAPER_TRADING", "true").lower() == "true",
    "max_position_size": float(os.getenv("MAX_POSITION_SIZE", "1000")),
    "risk_per_trade": float(os.getenv("RISK_PER_TRADE", "0.02")),  # 2% risk per trade
}

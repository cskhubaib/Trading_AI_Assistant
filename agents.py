import json
import time
import requests
from config import LLM_CONFIG
from graph import build_trading_graph

AGENT_ROLES = {
    "MarketAnalyst": (
        "You are a quantitative market analyst. Interpret technical indicators, "
        "identify trends, and provide a concise market outlook. Be data-driven."
    ),
    "RiskManager": (
        "You are a risk manager. Evaluate the trade for risk/reward ratio, "
        "position sizing, and portfolio exposure. Approve or reject with reasoning."
    ),
    "Trader": (
        "You are an execution trader. Based on the analyst and risk manager input, "
        "confirm the final trade decision and summarize the trade plan concisely."
    ),
}


def _call_gemini(prompt: str, system: str, retries: int = 3) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_CONFIG['model']}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": LLM_CONFIG["api_key"],
    }
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": prompt}]}],
    }
    for attempt in range(retries):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 503:
                wait = 2 ** attempt
                print(f"  [Gemini] 503 Service Unavailable, retrying in {wait}s...")
                time.sleep(wait)
                continue
            if r.status_code == 429:
                wait = 30
                print(f"  [Gemini] 429 Quota exceeded, retrying in {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return "[No response]"


def run_autogen_trading_session(ticker: str):
    trading_graph = build_trading_graph()
    result = trading_graph.invoke({"ticker": ticker})

    market_summary = (
        f"Ticker: {ticker} | Price: ${result['market_data'].get('current_price')} | "
        f"RSI: {result['market_data'].get('rsi')} | "
        f"MACD: {result['market_data'].get('macd')} (Signal: {result['market_data'].get('macd_signal')}) | "
        f"SMA20: {result['market_data'].get('sma_20')} | SMA50: {result['market_data'].get('sma_50')} | "
        f"Analysis: {result['analysis']} | Decision: {result['decision']} | Order: {result['order_result']}"
    )

    conversation = f"Review this trading signal and validate the decision:\n{market_summary}"

    for agent_name, system_prompt in AGENT_ROLES.items():
        reply = _call_gemini(prompt=conversation, system=system_prompt)
        print(f"\n[{agent_name}]: {reply}")
        conversation += f"\n\n[{agent_name}]: {reply}"

    return result

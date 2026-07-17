from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from tools import get_market_data, calculate_position_size, execute_order


class TradingState(TypedDict):
    ticker: str
    market_data: dict
    analysis: str
    decision: str          # "BUY" | "SELL" | "HOLD"
    position: dict
    risk_approved: bool
    order_result: dict


def analyze_node(state: TradingState) -> TradingState:
    data = get_market_data(state["ticker"])
    state["market_data"] = data

    signals = []
    if data.get("rsi", 50) < 30:
        signals.append("RSI oversold (bullish)")
    elif data.get("rsi", 50) > 70:
        signals.append("RSI overbought (bearish)")

    if data.get("macd", 0) > data.get("macd_signal", 0):
        signals.append("MACD bullish crossover")
    else:
        signals.append("MACD bearish crossover")

    if data.get("sma_20", 0) > data.get("sma_50", 0):
        signals.append("Price above 50 SMA (uptrend)")
    else:
        signals.append("Price below 50 SMA (downtrend)")

    state["analysis"] = " | ".join(signals) if signals else "No clear signals"
    return state


def decide_node(state: TradingState) -> TradingState:
    analysis = state["analysis"]
    bullish = analysis.count("bullish") + analysis.count("uptrend")
    bearish = analysis.count("bearish") + analysis.count("downtrend") + analysis.count("overbought")

    if bullish > bearish:
        state["decision"] = "BUY"
    elif bearish > bullish:
        state["decision"] = "SELL"
    else:
        state["decision"] = "HOLD"
    return state


def risk_check_node(state: TradingState) -> TradingState:
    if state["decision"] == "HOLD":
        state["risk_approved"] = False
        return state

    price = state["market_data"].get("current_price", 0)
    position = calculate_position_size(price)
    state["position"] = position
    state["risk_approved"] = position["shares"] > 0
    return state


def execute_node(state: TradingState) -> TradingState:
    if not state.get("risk_approved"):
        state["order_result"] = {"status": "skipped", "reason": "risk check failed or HOLD decision"}
        return state

    result = execute_order(
        ticker=state["ticker"],
        action=state["decision"],
        shares=state["position"]["shares"],
        price=state["market_data"]["current_price"],
    )
    state["order_result"] = result
    return state


def route_after_risk(state: TradingState) -> Literal["execute", "end"]:
    return "execute" if state.get("risk_approved") else "end"


def build_trading_graph() -> StateGraph:
    graph = StateGraph(TradingState)
    graph.add_node("analyze", analyze_node)
    graph.add_node("decide", decide_node)
    graph.add_node("risk_check", risk_check_node)
    graph.add_node("execute", execute_node)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "decide")
    graph.add_edge("decide", "risk_check")
    graph.add_conditional_edges("risk_check", route_after_risk, {"execute": "execute", "end": END})
    graph.add_edge("execute", END)

    return graph.compile()

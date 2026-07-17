from agents import run_autogen_trading_session
from graph import build_trading_graph


def run_langgraph_only(ticker: str):
    """Run just the LangGraph pipeline without AutoGen agents."""
    graph = build_trading_graph()
    result = graph.invoke({"ticker": ticker})
    print(f"\n{'='*40}")
    print(f"Ticker:   {result['ticker']}")
    print(f"Price:    ${result['market_data'].get('current_price')}")
    print(f"Analysis: {result['analysis']}")
    print(f"Decision: {result['decision']}")
    print(f"Position: {result.get('position', {})}")
    print(f"Order:    {result['order_result']}")
    print(f"{'='*40}\n")
    return result


if __name__ == "__main__":
    ticker = "AAPL"

    print("=== LangGraph Pipeline ===")
    run_langgraph_only(ticker)

    print("\n=== AutoGen Multi-Agent Session ===")
    run_autogen_trading_session(ticker)

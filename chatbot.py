import streamlit as st
import requests
import base64
import json
import time
from PIL import Image
import io
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are an expert trading analyst and chart reader. When given a trading chart image:
1. Identify the asset, timeframe, and chart type
2. Analyze visible technical indicators (RSI, MACD, Bollinger Bands, Moving Averages, volume, etc.)
3. Identify key support/resistance levels, chart patterns (head & shoulders, triangles, flags, etc.)
4. Provide a clear trading prediction: BUY / SELL / HOLD
5. Give entry price, stop-loss, and take-profit targets if visible
6. Rate your confidence: Low / Medium / High
Keep your response structured and concise."""


def call_gemini_vision(image_bytes: bytes, user_message: str, history: list) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {"Content-Type": "application/json", "X-goog-api-key": GEMINI_API_KEY}

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    contents = []
    for msg in history[:-1]:  # past messages without image
        contents.append({
            "role": msg["role"],
            "parts": [{"text": msg["content"]}]
        })

    # latest message with image
    contents.append({
        "role": "user",
        "parts": [
            {"inline_data": {"mime_type": "image/png", "data": image_b64}},
            {"text": user_message}
        ]
    })

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
    }

    for attempt in range(3):
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 503:
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429:
            time.sleep(30)
            continue
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    return "Service unavailable. Please try again."


def call_gemini_text(user_message: str, history: list) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {"Content-Type": "application/json", "X-goog-api-key": GEMINI_API_KEY}

    contents = []
    for msg in history:
        contents.append({
            "role": msg["role"],
            "parts": [{"text": msg["content"]}]
        })

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
    }

    for attempt in range(3):
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 503:
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429:
            time.sleep(30)
            continue
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    return "Service unavailable. Please try again."


# ── UI ──────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Trading Analyst", page_icon="📈", layout="wide")
st.title("📈 AI Trading Chart Analyst")
st.caption("Upload a trading chart and ask for analysis, predictions, and trade setups.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None

with st.sidebar:
    st.header("📤 Upload Chart")
    uploaded_file = st.file_uploader("Upload a trading chart", type=["png", "jpg", "jpeg", "webp"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        st.session_state.image_bytes = buf.getvalue()
        st.session_state.uploaded_image = image
        st.image(image, caption="Uploaded Chart", use_container_width=True)
        st.success("Chart ready for analysis!")

    st.divider()
    st.markdown("**Quick Prompts:**")
    quick_prompts = [
        "Analyze this chart and give me a trade setup",
        "What is the trend direction?",
        "Identify key support and resistance levels",
        "Is this a good entry point?",
        "What chart pattern do you see?",
    ]
    for prompt in quick_prompts:
        if st.button(prompt, use_container_width=True):
            st.session_state.quick_prompt = prompt

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploaded_image = None
        st.session_state.image_bytes = None
        st.rerun()

# chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image"):
            st.image(msg["image"], width=300)
        st.markdown(msg["content"])

# input
user_input = st.chat_input("Ask about the chart... (e.g. 'What's the prediction for this chart?')")

if not user_input and hasattr(st.session_state, "quick_prompt"):
    user_input = st.session_state.quick_prompt
    del st.session_state.quick_prompt

if user_input:
    image_bytes = st.session_state.image_bytes
    image = st.session_state.uploaded_image

    with st.chat_message("user"):
        if image:
            st.image(image, width=300)
        st.markdown(user_input)

    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "image": image,
    })

    with st.chat_message("assistant"):
        with st.spinner("Analyzing chart..."):
            if image_bytes:
                response = call_gemini_vision(image_bytes, user_input, st.session_state.messages)
                st.session_state.image_bytes = None  # clear after first use, keep for follow-ups via text
                st.session_state.image_bytes = image_bytes  # keep for follow-up questions
            else:
                response = call_gemini_text(user_input, st.session_state.messages)
        st.markdown(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
    })

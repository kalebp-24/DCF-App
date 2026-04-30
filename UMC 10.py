#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 16:25:45 2026

@author: kalebpagel
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# -------------------------------
# PAGE SETUP
# -------------------------------
st.set_page_config(page_title="DCF Terminal", layout="wide")

st.title("📊 Equity Research DCF Terminal")
st.caption("Persistent dashboard — update stock anytime")

# -------------------------------
# CACHE DATA
# -------------------------------
@st.cache_data(ttl=3600)
def load_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.get_info(), stock.history(period="5y")

# -------------------------------
# SESSION STATE INIT
# -------------------------------
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

if "ticker" not in st.session_state:
    st.session_state.ticker = "AAPL"

# -------------------------------
# INPUT SECTION (ALWAYS VISIBLE)
# -------------------------------
st.header("1️⃣ Stock Selection")

ticker_input = st.text_input("Enter Stock Ticker", st.session_state.ticker).upper()

load_btn = st.button("🔄 Load / Refresh Stock Data")

# -------------------------------
# LOAD DATA ONLY ON BUTTON CLICK
# -------------------------------
if load_btn:
    try:
        info, hist = load_data(ticker_input)

        st.session_state.info = info
        st.session_state.hist = hist
        st.session_state.ticker = ticker_input
        st.session_state.data_loaded = True

    except:
        st.error("Rate limit hit or invalid ticker.")
        st.stop()

# -------------------------------
# IF DATA EXISTS → DISPLAY EVERYTHING
# -------------------------------
if st.session_state.data_loaded:

    info = st.session_state.info
    hist = st.session_state.hist

    # -------------------------------
    # MARKET SNAPSHOT
    # -------------------------------
    st.header(f"📌 Market Snapshot: {st.session_state.ticker}")

    price = info.get("currentPrice")
    market_cap = info.get("marketCap")
    beta = info.get("beta", 1.2)
    shares = info.get("sharesOutstanding")
    debt = info.get("totalDebt", 0)
    cash = info.get("totalCash", 0)
    revenue = info.get("totalRevenue", 0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Price", price)
    col2.metric("Market Cap", f"{market_cap:,.0f}" if market_cap else "N/A")
    col3.metric("Beta", beta)
    col4.metric("Shares", f"{shares:,.0f}")

    # -------------------------------
    # STOCK PERFORMANCE
    # -------------------------------
    st.subheader("📈 5-Year Stock Performance")

    norm = hist["Close"] / hist["Close"].iloc[0] * 100
    st.line_chart(norm)

    # -------------------------------
    # ASSUMPTIONS (ALWAYS VISIBLE)
    # -------------------------------
    st.header("2️⃣ Assumptions")

    growth = st.slider("Revenue Growth Rate", 0.00, 0.30, 0.05)
    margin = st.slider("EBIT Margin", 0.00, 0.50, 0.20)
    tax_rate = st.slider("Tax Rate", 0.00, 0.40, 0.25)
    reinvestment = st.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
    years = st.slider("Projection Years", 3, 10, 5)
    terminal_growth = st.slider("Terminal Growth Rate", 0.00, 0.05, 0.03)

    # WACC (simple input)
    wacc = st.slider("WACC (Discount Rate)", 0.05, 0.20, 0.10)

    # -------------------------------
    # DCF MODEL
    # -------------------------------
    st.header("3️⃣ Valuation Model")

    rev = revenue

    revenues, fcfs, disc_fcfs = [], [], []

    for t in range(1, years + 1):

        rev *= (1 + growth)

        ebit = rev * margin
        nopat = ebit * (1 - tax_rate)

        fcf = nopat * (1 - reinvestment)

        discounted = fcf / (1 + wacc) ** t

        revenues.append(rev)
        fcfs.append(fcf)
        disc_fcfs.append(discounted)

    terminal_fcf = fcfs[-1] * (1 + terminal_growth)
    terminal_value = terminal_fcf / (wacc - terminal_growth)
    terminal_discounted = terminal_value / (1 + wacc) ** years

    enterprise_value = sum(disc_fcfs) + terminal_discounted
    equity_value = enterprise_value - debt + cash
    intrinsic = equity_value / shares

    # -------------------------------
    # RESULTS
    # -------------------------------
    st.header("4️⃣ Valuation Output")

    col1, col2, col3 = st.columns(3)
    col1.metric("Enterprise Value", f"{enterprise_value:,.0f}")
    col2.metric("Equity Value", f"{equity_value:,.0f}")
    col3.metric("Intrinsic Value", f"{intrinsic:.2f}")

    diff = intrinsic - price

    if diff > 0:
        st.success(f"📈 Undervalued by {diff:.2f}")
    else:
        st.error(f"📉 Overvalued by {abs(diff):.2f}")

    # -------------------------------
    # TABLE
    # -------------------------------
    st.header("5️⃣ DCF Breakdown Table")

    df = pd.DataFrame({
        "Year": range(1, years + 1),
        "Revenue": revenues,
        "FCF": fcfs,
        "Discounted FCF": disc_fcfs
    })

    st.dataframe(df)

# -------------------------------
# IF NO DATA LOADED YET
# -------------------------------
else:
    st.info("Enter a ticker and click 'Load / Refresh Stock Data' to begin analysis.")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 16:28:14 2026

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
st.caption("Live financial dashboard (auto-updating)")

# -------------------------------
# CACHE DATA (IMPORTANT FOR STABILITY)
# -------------------------------
@st.cache_data(ttl=3600)
def load_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.get_info(), stock.history(period="5y")

# -------------------------------
# INPUT (NO BUTTON)
# -------------------------------
ticker = st.text_input("Enter Stock Ticker", "AAPL").upper()

if not ticker:
    st.info("Enter a ticker to begin analysis.")
    st.stop()

# -------------------------------
# LOAD DATA AUTOMATICALLY
# -------------------------------
try:
    info, hist = load_data(ticker)
except:
    st.error("Unable to fetch data (rate limit or invalid ticker). Try again shortly.")
    st.stop()

# -------------------------------
# MARKET SNAPSHOT
# -------------------------------
price = info.get("currentPrice")
market_cap = info.get("marketCap")
beta = info.get("beta", 1.2)
shares = info.get("sharesOutstanding")
debt = info.get("totalDebt", 0)
cash = info.get("totalCash", 0)
revenue = info.get("totalRevenue", 0)

st.header(f"📌 Market Snapshot: {ticker}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Price", price)
col2.metric("Market Cap", f"{market_cap:,.0f}" if market_cap else "N/A")
col3.metric("Beta", beta)
col4.metric("Shares", f"{shares:,.0f}")

st.divider()

# -------------------------------
# STOCK PERFORMANCE
# -------------------------------
st.subheader("📈 5-Year Stock Performance")

normalized = hist["Close"] / hist["Close"].iloc[0] * 100
st.line_chart(normalized)

st.caption("Normalized price index (Base = 100). Shows long-term performance trend.")

st.divider()

# -------------------------------
# ASSUMPTIONS
# -------------------------------
st.header("2️⃣ Operating Assumptions")

growth = st.slider("Revenue Growth Rate", 0.00, 0.30, 0.05)
margin = st.slider("EBIT Margin", 0.00, 0.50, 0.20)
tax_rate = st.slider("Tax Rate", 0.00, 0.40, 0.25)
reinvestment = st.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
years = st.slider("Projection Years", 3, 10, 5)
terminal_growth = st.slider("Terminal Growth Rate", 0.00, 0.05, 0.03)
wacc = st.slider("WACC (Discount Rate)", 0.05, 0.20, 0.10)

st.divider()

# -------------------------------
# DCF MODEL
# -------------------------------
st.header("3️⃣ Valuation Build")

rev = revenue

revenues, fcfs, disc_fcfs = [], [], []

for t in range(1, years + 1):

    rev *= (1 + growth)

    ebit = rev * margin
    nopat = ebit * (1 - tax_rate)

    # Free Cash Flow (correct definition)
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
# DCF TABLE
# -------------------------------
st.header("5️⃣ DCF Breakdown")

df = pd.DataFrame({
    "Year": range(1, years + 1),
    "Revenue": revenues,
    "FCF": fcfs,
    "Discounted FCF": disc_fcfs
})

st.dataframe(df)

st.caption("""
Revenue is the foundation of the entire valuation model.  
It drives EBIT → cash flow → intrinsic value.
""")
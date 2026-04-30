#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 15:49:21 2026

@author: kalebpagel
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# -------------------------------
# PAGE CONFIG (cleaner UI)
# -------------------------------
st.set_page_config(page_title="DCF Valuation Tool", layout="wide")

st.markdown("""
<style>
h1, h2, h3 {
    font-weight: 600;
}
.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Equity Research DCF Model")
st.caption("Built for valuation analysis — clean, structured, and finance-focused")

# -------------------------------
# CACHE DATA
# -------------------------------
@st.cache_data(ttl=3600)
def load_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.get_info(), stock.history(period="5y")

# -------------------------------
# 1. MARKET DATA
# -------------------------------
st.header("1️⃣ Market Overview")

ticker = st.text_input("Enter Stock Ticker", "AAPL").upper()

try:
    info, hist = load_data(ticker)
except:
    st.error("Rate limit hit — please wait and refresh.")
    st.stop()

price = info.get("currentPrice")
market_cap = info.get("marketCap")
beta_market = info.get("beta", 1.2)
shares = info.get("sharesOutstanding")
debt = info.get("totalDebt", 0)
cash = info.get("totalCash", 0)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Price", price)
col2.metric("Market Cap", f"{market_cap:,.0f}" if market_cap else "N/A")
col3.metric("Beta", beta_market)
col4.metric("Shares", f"{shares:,.0f}")

st.divider()

# -------------------------------
# 2. ASSUMPTIONS
# -------------------------------
st.header("2️⃣ Operating Assumptions")

growth = st.slider("Revenue Growth Rate", 0.00, 0.30, 0.05)
margin = st.slider("EBIT Margin", 0.00, 0.50, 0.20)
tax_rate = st.slider("Tax Rate", 0.00, 0.40, 0.25)
reinvestment = st.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
years = st.slider("Projection Years", 3, 10, 5)
terminal_growth = st.slider("Terminal Growth Rate", 0.00, 0.05, 0.03)

st.divider()

# -------------------------------
# 3. WACC (SIMPLIFIED USER INPUT)
# -------------------------------
st.header("3️⃣ Discount Rate (WACC)")

wacc = st.slider("WACC (Discount Rate)", 0.05, 0.20, 0.10)

st.markdown("### 📘 How WACC is Conceptually Built")

st.latex(r"R_e = R_f + \beta \times ERP")
st.latex(r"WACC = \frac{E}{V}R_e + \frac{D}{V}R_d(1 - T)")

st.caption("You are inputting WACC directly, but it represents a weighted cost of capital combining equity and debt risk.")

st.divider()

# -------------------------------
# 4. DCF MODEL
# -------------------------------
st.header("4️⃣ Cash Flow Projection")

rev = info.get("totalRevenue", 0)

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

st.divider()

# -------------------------------
# 5. EXPLANATION (FLOWING STYLE)
# -------------------------------
st.header("5️⃣ What the Model is Doing")

st.markdown("""
We start with **revenue**, then build forward:

- Revenue grows using assumptions
- EBIT is applied using margins
- Taxes convert EBIT into operating profit
- We remove reinvestment needs to get **Free Cash Flow**

""")

st.latex(r"FCF = Operating\ Cash\ Flow - Capital\ Expenditures")

st.markdown("""
Each future cash flow is then discounted back to today using WACC:

- Higher WACC → lower valuation
- Lower WACC → higher valuation
""")

st.divider()

# -------------------------------
# 6. TABLE (CLEANER LOOK)
# -------------------------------
st.header("6️⃣ DCF Projection Table")

df = pd.DataFrame({
    "Year": range(1, years + 1),
    "Revenue": revenues,
    "Free Cash Flow": fcfs,
    "Discounted FCF": disc_fcfs
})

st.dataframe(df, use_container_width=True)

st.caption("""
📌 Revenue is included because it is the **starting point of all valuation models**.  
It drives EBIT → cash flow → final intrinsic value.
""")

st.divider()

# -------------------------------
# 7. FINAL OUTPUT
# -------------------------------
st.header("7️⃣ Valuation Result")

col1, col2, col3 = st.columns(3)
col1.metric("Enterprise Value", f"{enterprise_value:,.0f}")
col2.metric("Equity Value", f"{equity_value:,.0f}")
col3.metric("Intrinsic Value", f"{intrinsic:.2f}")

diff = intrinsic - price

if diff > 0:
    st.success(f"📈 Undervalued by {diff:.2f}")
else:
    st.error(f"📉 Overvalued by {abs(diff):.2f}")
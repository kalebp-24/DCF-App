#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 15:14:25 2026

@author: kalebpagel
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# -------------------------------
# PAGE SETUP
# -------------------------------
st.set_page_config(page_title="Equity Research DCF Terminal", layout="wide")

st.title("📊 Equity Research DCF Terminal")
st.write("Market data → valuation → interpretation (real analyst workflow)")

# -------------------------------
# CACHE DATA (ANTI-RATE LIMIT)
# -------------------------------
@st.cache_data(ttl=3600)
def load_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.get_info(), stock.history(period="5y")

# -------------------------------
# STEP 1: MARKET DATA SNAPSHOT
# -------------------------------
st.header("1️⃣ Market Snapshot")

ticker = st.text_input("Enter Ticker", "AAPL").upper()

try:
    info, hist = load_data(ticker)
except:
    st.error("Yahoo Finance rate limit hit. Try again in a few minutes.")
    st.stop()

price = info.get("currentPrice")
market_cap = info.get("marketCap")
beta = info.get("beta", 1.2)
shares = info.get("sharesOutstanding")
debt = info.get("totalDebt", 0)
cash = info.get("totalCash", 0)
div_yield = info.get("dividendYield", 0)
ebitda = info.get("ebitda", None)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Price", price)
col2.metric("Market Cap", f"{market_cap:,.0f}" if market_cap else "N/A")
col3.metric("Beta", beta)
col4.metric("Dividend Yield", f"{div_yield:.2%}" if div_yield else "0%")

col5, col6 = st.columns(2)
col5.metric("Shares Outstanding", f"{shares:,.0f}")
col6.metric("Net Debt", f"{(debt - cash):,.0f}")

# -------------------------------
# 5-YEAR STOCK PERFORMANCE
# -------------------------------
st.subheader("📈 5-Year Stock Performance")

norm = hist["Close"] / hist["Close"].iloc[0] * 100
st.line_chart(norm)

st.markdown("""
📌 This chart shows **relative price performance (base = 100)** over 5 years.
It helps compare long-term momentum independent of price level.
""")

# -------------------------------
# STEP 2: ASSUMPTIONS
# -------------------------------
st.header("2️⃣ Operating Assumptions")

growth = st.slider("Revenue Growth", 0.00, 0.30, 0.05)
margin = st.slider("EBIT Margin", 0.00, 0.50, 0.20)
tax_rate = st.slider("Tax Rate", 0.00, 0.40, 0.25)
reinvestment = st.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
years = st.slider("Projection Years", 3, 10, 5)
terminal_growth = st.slider("Terminal Growth", 0.00, 0.05, 0.03)

# -------------------------------
# STEP 3: CAPM + WACC
# -------------------------------
st.header("3️⃣ Cost of Capital (WACC)")

rf = 0.04
erp = 0.06
rd = 0.05

Re = rf + beta * erp

E = price * shares
D = debt if debt else 0
V = E + D

E_V = E / V
D_V = D / V

wacc = (E_V * Re) + (D_V * rd * (1 - tax_rate))

st.markdown("### 📘 Core Formulas")

st.latex(r"R_e = R_f + \beta \times ERP")
st.latex(r"WACC = \frac{E}{V}R_e + \frac{D}{V}R_d(1 - T)")

col1, col2, col3 = st.columns(3)
col1.metric("Cost of Equity", f"{Re:.2%}")
col2.metric("WACC", f"{wacc:.2%}")
col3.metric("Debt Weight", f"{D_V:.2%}")

# -------------------------------
# STEP 4: CASH FLOW BUILD
# -------------------------------
st.header("4️⃣ Cash Flow Construction")

rev = info.get("totalRevenue", 0)

fcf_list = []
disc_list = []
rev_list = []

for t in range(1, years + 1):

    rev *= (1 + growth)

    ebit = rev * margin
    nopat = ebit * (1 - tax_rate)

    # REAL FCF DEFINITION (your request)
    fcf = nopat * (1 - reinvestment)

    discounted = fcf / (1 + wacc) ** t

    rev_list.append(rev)
    fcf_list.append(fcf)
    disc_list.append(discounted)

terminal_fcf = fcf_list[-1] * (1 + terminal_growth)
terminal_value = terminal_fcf / (wacc - terminal_growth)
terminal_discounted = terminal_value / (1 + wacc) ** years

enterprise_value = sum(disc_list) + terminal_discounted
equity_value = enterprise_value - D + cash
intrinsic = equity_value / shares

# -------------------------------
# STEP 5: VALUATION OUTPUT
# -------------------------------
st.header("5️⃣ Valuation Result")

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
# STEP 6: TABLE + CHARTS
# -------------------------------
st.header("6️⃣ Model Breakdown")

df = pd.DataFrame({
    "Year": range(1, years + 1),
    "Revenue": rev_list,
    "FCF": fcf_list,
    "Discounted FCF": disc_list
})

st.line_chart(df.set_index("Year")[["Revenue"]])
st.line_chart(df.set_index("Year")[["FCF"]])
st.bar_chart(df.set_index("Year")[["Discounted FCF"]])

st.dataframe(df)

# -------------------------------
# STEP 7: FLOWING EXPLANATION (LIVE ANALYST STYLE)
# -------------------------------
st.header("7️⃣ What is happening in this model")

st.markdown("""
### Step 1 — Market Context
We start with real market data (price, beta, leverage).

### Step 2 — Risk (CAPM)
We estimate required return:

""")
st.latex(r"R_e = R_f + \beta \times ERP")

st.markdown("""
### Step 3 — Discount Rate
We blend equity and debt:

""")
st.latex(r"WACC = \frac{E}{V}R_e + \frac{D}{V}R_d(1 - T)")

st.markdown("""
### Step 4 — Cash Flow
We compute true Free Cash Flow:

""")
st.latex(r"FCF = Operating\ Cash\ Flow - Capital\ Expenditures")

st.markdown("""
### Step 5 — Valuation
We discount future cash flows + terminal value to today.
""")
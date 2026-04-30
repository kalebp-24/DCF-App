#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 15:26:46 2026

@author: kalebpagel
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# -------------------------------
# PAGE SETUP
# -------------------------------
st.set_page_config(page_title="DCF Equity Research Tool", layout="wide")

st.title("📊 Equity Research DCF Model")
st.write("Market data → assumptions → valuation → interpretation")

# -------------------------------
# CACHE DATA (ANTI RATE LIMIT)
# -------------------------------
@st.cache_data(ttl=3600)
def load_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.get_info(), stock.history(period="5y")

# -------------------------------
# 1. MARKET DATA
# -------------------------------
st.header("1️⃣ Market Snapshot")

ticker = st.text_input("Enter Ticker", "AAPL").upper()

try:
    info, hist = load_data(ticker)
except:
    st.error("Rate limit hit. Wait a few minutes and retry.")
    st.stop()

price = info.get("currentPrice")
market_cap = info.get("marketCap")
beta_market = info.get("beta", 1.2)
shares = info.get("sharesOutstanding")
debt = info.get("totalDebt", 0)
cash = info.get("totalCash", 0)

col1, col2, col3 = st.columns(3)
col1.metric("Price", price)
col2.metric("Market Cap", f"{market_cap:,.0f}" if market_cap else "N/A")
col3.metric("Beta", beta_market)

st.write("📌 These inputs anchor the valuation in real market conditions.")

# -------------------------------
# 2. ASSUMPTIONS
# -------------------------------
st.header("2️⃣ Operating Assumptions")

growth = st.slider("Revenue Growth", 0.00, 0.30, 0.05)
margin = st.slider("EBIT Margin", 0.00, 0.50, 0.20)
tax_rate = st.slider("Tax Rate", 0.00, 0.40, 0.25)
reinvestment = st.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
years = st.slider("Projection Years", 3, 10, 5)
terminal_growth = st.slider("Terminal Growth", 0.00, 0.05, 0.03)

# -------------------------------
# 3. WACC (NOW FULLY ADJUSTABLE)
# -------------------------------
st.header("3️⃣ Cost of Capital (WACC)")

rf = st.slider("Risk-Free Rate (Rf)", 0.00, 0.08, 0.04)
erp = st.slider("Equity Risk Premium (ERP)", 0.05, 0.10, 0.06)
beta = st.slider("Beta (β)", 0.5, 2.0, float(beta_market))

rd = st.slider("Cost of Debt (Rd)", 0.01, 0.12, 0.05)

# CAPM
Re = rf + beta * erp

# capital structure
E = price * shares
D = debt if debt else 0
V = E + D

E_V = E / V
D_V = D / V

wacc = (E_V * Re) + (D_V * rd * (1 - tax_rate))

st.markdown("### 📘 Key Formulas")

st.latex(r"R_e = R_f + \beta \times ERP")
st.latex(r"WACC = \frac{E}{V}R_e + \frac{D}{V}R_d(1 - T)")

col1, col2, col3 = st.columns(3)
col1.metric("Cost of Equity", f"{Re:.2%}")
col2.metric("WACC", f"{wacc:.2%}")
col3.metric("Debt Weight", f"{D_V:.2%}")

# -------------------------------
# 4. DCF MODEL
# -------------------------------
st.header("4️⃣ DCF Projection")

rev = info.get("totalRevenue", 0)

revenues, fcfs, disc_fcfs = [], [], []

for t in range(1, years + 1):

    rev *= (1 + growth)

    ebit = rev * margin
    nopat = ebit * (1 - tax_rate)

    # TRUE FCF DEFINITION
    fcf = nopat * (1 - reinvestment)

    discounted = fcf / (1 + wacc) ** t

    revenues.append(rev)
    fcfs.append(fcf)
    disc_fcfs.append(discounted)

terminal_fcf = fcfs[-1] * (1 + terminal_growth)
terminal_value = terminal_fcf / (wacc - terminal_growth)
terminal_discounted = terminal_value / (1 + wacc) ** years

enterprise_value = sum(disc_fcfs) + terminal_discounted
equity_value = enterprise_value - D + cash
intrinsic = equity_value / shares

# -------------------------------
# 5. EXPLANATION (MOVED ABOVE TABLE)
# -------------------------------
st.header("5️⃣ Understanding the DCF Table")

st.markdown("""
### 📌 Why Revenue is Included in the Table

Revenue is shown because it is the **starting point of all cash flow projections**.

We grow revenue over time using assumptions, and it drives:

- EBIT (operating profit)
- NOPAT (after-tax earnings)
- Free Cash Flow (final valuation input)

Without revenue, the model has no economic foundation.

---

### 📌 How to Read the Table

Each row represents one future year:

- **Revenue** → size of business
- **FCF** → cash generated from operations
- **Discounted FCF** → today's value of that cash

We discount because:

> 💡 money today is worth more than money in the future
""")

# -------------------------------
# 6. TABLE
# -------------------------------
st.header("6️⃣ DCF Projection Table")

df = pd.DataFrame({
    "Year": range(1, years + 1),
    "Revenue": revenues,
    "FCF": fcfs,
    "Discounted FCF": disc_fcfs
})

st.dataframe(df)

# -------------------------------
# 7. FINAL RESULT
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
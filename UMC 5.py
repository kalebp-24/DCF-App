#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 15:05:57 2026

@author: kalebpagel
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# -------------------------------
# PAGE SETUP
# -------------------------------
st.set_page_config(page_title="DCF Model", layout="wide")

st.title("📊 Interactive DCF Valuation Model")
st.write("Fully automated Yahoo Finance DCF with CAPM-based WACC + explanations")

# -------------------------------
# CACHE DATA (FIX RATE LIMIT)
# -------------------------------
@st.cache_data(ttl=3600)
def load_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.get_info()

# -------------------------------
# STEP 1: STOCK INPUT (MINIMAL USER WORK)
# -------------------------------
st.header("1️⃣ Select Company")

ticker = st.text_input("Stock Ticker", "AAPL").upper()

try:
    info = load_data(ticker)
except:
    st.error("Yahoo Finance rate limit hit. Please wait and refresh.")
    st.stop()

# AUTO-FILLED DATA (NO USER INPUT NEEDED)
price = info.get("currentPrice")
revenue = info.get("totalRevenue")
shares = info.get("sharesOutstanding")
cash = info.get("totalCash", 0)
debt = info.get("totalDebt", 0)
beta_market = info.get("beta", 1.2)

if not revenue or not shares:
    st.warning("Missing data for this ticker.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Stock Price", price)
col2.metric("Revenue", f"${revenue:,.0f}")
col3.metric("Shares", f"{shares:,.0f}")

# -------------------------------
# STEP 2: ASSUMPTIONS (USER ONLY ADJUSTS KEY DRIVERS)
# -------------------------------
st.header("2️⃣ Key Assumptions")

growth = st.slider("Revenue Growth Rate", 0.00, 0.30, 0.05)
ebit_margin = st.slider("EBIT Margin", 0.00, 0.50, 0.20)
reinvestment = st.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
terminal_growth = st.slider("Terminal Growth Rate", 0.00, 0.05, 0.03)
years = st.slider("Projection Years", 3, 10, 5)

# MACRO DEFAULTS (auto + optional override feel)
rf = 0.04
erp = 0.06
rd = 0.05
tax_rate = 0.25
beta = beta_market if beta_market else 1.2

st.write("📌 Using market defaults:")
st.write(f"Risk-Free Rate: {rf}, ERP: {erp}, Beta: {beta:.2f}")

# -------------------------------
# STEP 3: WACC (CAPM EXPLAINED)
# -------------------------------
st.header("3️⃣ Cost of Capital (WACC)")

# CAPM
cost_of_equity = rf + beta * erp

# Capital structure
equity_val = price * shares
debt_val = debt if debt else 0
total_val = equity_val + debt_val

E_V = equity_val / total_val
D_V = debt_val / total_val

wacc = (E_V * cost_of_equity) + (D_V * rd * (1 - tax_rate))

st.subheader("📘 Formulas Used")

st.latex(r"R_e = R_f + \beta \times ERP")
st.latex(r"WACC = \frac{E}{V}R_e + \frac{D}{V}R_d(1 - T)")

col1, col2, col3 = st.columns(3)
col1.metric("Cost of Equity", f"{cost_of_equity:.2%}")
col2.metric("WACC", f"{wacc:.2%}")
col3.metric("Debt Weight", f"{D_V:.2%}")

# -------------------------------
# STEP 4: DCF MODEL
# -------------------------------
st.header("4️⃣ Discounted Cash Flow Model")

rev = revenue
revenues, fcfs, disc_fcfs = [], [], []

for t in range(1, years + 1):

    rev *= (1 + growth)

    ebit = rev * ebit_margin
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
equity_value_final = enterprise_value - debt_val + cash
intrinsic_value = equity_value_final / shares

# -------------------------------
# STEP 5: RESULTS
# -------------------------------
st.header("5️⃣ Valuation Output")

col1, col2, col3 = st.columns(3)
col1.metric("Enterprise Value", f"${enterprise_value:,.0f}")
col2.metric("Equity Value", f"${equity_value_final:,.0f}")
col3.metric("Intrinsic Value", f"${intrinsic_value:,.2f}")

diff = intrinsic_value - price

if diff > 0:
    st.success(f"📈 Undervalued by ${diff:.2f}")
else:
    st.error(f"📉 Overvalued by ${abs(diff):.2f}")

# -------------------------------
# STEP 6: VISUALS
# -------------------------------
st.header("6️⃣ Charts")

df = pd.DataFrame({
    "Year": range(1, years + 1),
    "Revenue": revenues,
    "FCF": fcfs,
    "Discounted FCF": disc_fcfs
})

st.line_chart(df.set_index("Year")[["Revenue"]])
st.line_chart(df.set_index("Year")[["FCF"]])
st.bar_chart(df.set_index("Year")[["Discounted FCF"]])

# -------------------------------
# STEP 7: EDUCATIONAL EXPLANATION (WITH EQUATIONS)
# -------------------------------
st.header("7️⃣ How This Model Works")

st.markdown("""
### 📌 Step 1: CAPM (Cost of Equity)

We estimate the required return using:

""")
st.latex(r"R_e = R_f + \beta \times ERP")

st.markdown("""
### 📌 Step 2: WACC

We weight debt and equity to get the discount rate:

""")
st.latex(r"WACC = \frac{E}{V}R_e + \frac{D}{V}R_d(1 - T)")

st.markdown("""
### 📌 Step 3: Free Cash Flow

We estimate cash available to investors:

""")
st.latex(r"FCF = NOPAT \times (1 - Reinvestment Rate)")

st.markdown("""
### 📌 Step 4: Terminal Value

We assume perpetual growth after forecast period:

""")
st.latex(r"TV = \frac{FCF_{final} \times (1 + g)}{WACC - g}")

st.markdown("""
### 📌 Step 5: Valuation

Enterprise Value is discounted cash flows + terminal value, then adjusted for net debt to get equity value.
""")
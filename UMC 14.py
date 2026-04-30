#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 16:40:41 2026

@author: kalebpagel
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# -------------------------------
# PAGE SETUP
# -------------------------------
st.set_page_config(page_title="Equity Research DCF", layout="wide")

st.title("📊 Equity Research DCF Workflow")
st.caption("Step-by-step valuation model: Market → Cash Flow → WACC → DCF")

# -------------------------------
# DATA
# -------------------------------
@st.cache_data(ttl=3600)
def load_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.get_info(), stock.history(period="5y")

ticker = st.text_input("Enter Stock Ticker", "AAPL").upper()

if not ticker:
    st.stop()

try:
    info, hist = load_data(ticker)
except:
    st.error("Error loading data.")
    st.stop()

# -------------------------------
# 1️⃣ MARKET DATA
# -------------------------------
st.header("1️⃣ Market Overview")

price = info.get("currentPrice")
market_cap = info.get("marketCap")
beta = info.get("beta", 1.2)
shares = info.get("sharesOutstanding")
revenue = info.get("totalRevenue", 0)
debt = info.get("totalDebt", 0)
cash = info.get("totalCash", 0)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Price", price)
col2.metric("Market Cap", f"{market_cap:,.0f}")
col3.metric("Beta", beta)
col4.metric("Shares", f"{shares:,.0f}")

st.divider()

# -------------------------------
# STOCK CHART
# -------------------------------
st.subheader("📈 5-Year Stock Performance")

norm = hist["Close"] / hist["Close"].iloc[0] * 100
st.line_chart(norm)

st.divider()

# -------------------------------
# 2️⃣ CASH FLOW INTUITION
# -------------------------------
st.header("2️⃣ Cash Flow Foundation")

st.latex(r"Net\ Debt = Total\ Debt - Cash")
net_debt = debt - cash

st.metric("Net Debt", f"{net_debt:,.0f}")

st.latex(r"FCF = Operating\ Cash\ Flow - Capital\ Expenditures")

st.markdown("""
### Why this matters
Free Cash Flow is the **true cash available to investors** after maintaining operations.
It is the starting point for valuation.
""")

st.divider()

# -------------------------------
# 3️⃣ WACC (NOW FIXED + FULLY DYNAMIC)
# -------------------------------
st.header("3️⃣ Cost of Capital (CAPM + WACC)")

rf = st.slider("Risk-Free Rate (Rf)", 0.00, 0.08, 0.04)
erp = st.slider("Equity Risk Premium (ERP)", 0.05, 0.10, 0.06)
rd = st.slider("Cost of Debt (Rd)", 0.01, 0.12, 0.05)
tax_rate = st.slider("Tax Rate", 0.00, 0.40, 0.25)

Re = rf + beta * erp   # CAPM (FULLY DYNAMIC NOW)

E = price * shares
D = debt if debt else 0
V = E + D

E_V = E / V
D_V = D / V

wacc = (E_V * Re) + (D_V * rd * (1 - tax_rate))  # NOW UPDATES PROPERLY

st.markdown("### Core Formulas")

st.latex(r"R_e = R_f + \beta \times ERP")
st.latex(r"WACC = \frac{E}{V}R_e + \frac{D}{V}R_d(1 - T)")

col1, col2, col3 = st.columns(3)
col1.metric("Cost of Equity", f"{Re:.2%}")
col2.metric("WACC", f"{wacc:.2%}")
col3.metric("Debt Weight", f"{D_V:.2%}")

st.divider()

# -------------------------------
# 4️⃣ FORECAST ASSUMPTIONS
# -------------------------------
st.header("4️⃣ Forecast Assumptions")

growth = st.slider("Revenue Growth Rate", 0.00, 0.30, 0.05)
margin = st.slider("EBIT Margin", 0.00, 0.50, 0.20)
reinvestment = st.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
years = st.slider("Forecast Years", 3, 10, 5)
terminal_growth = st.slider("Terminal Growth Rate", 0.00, 0.05, 0.03)

st.divider()

# -------------------------------
# 5️⃣ DCF MODEL
# -------------------------------
st.header("5️⃣ DCF Build")

rev = revenue
revenues, fcfs, disc_fcfs = [], [], []

for t in range(1, years + 1):

    rev = rev * (1 + growth)

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
intrinsic_value = equity_value / shares

# -------------------------------
# 6️⃣ FINAL OUTPUT
# -------------------------------
st.header("6️⃣ Valuation Result")

col1, col2, col3 = st.columns(3)
col1.metric("Enterprise Value", f"{enterprise_value:,.0f}")
col2.metric("Equity Value", f"{equity_value:,.0f}")
col3.metric("Intrinsic Value", f"{intrinsic_value:.2f}")

diff = intrinsic_value - price

if diff > 0:
    st.success(f"📈 Undervalued by {diff:.2f}")
else:
    st.error(f"📉 Overvalued by {abs(diff):.2f}")

# -------------------------------
# 7️⃣ EXPLANATION + FORMULAS (FIXED REQUEST)
# -------------------------------
st.header("7️⃣ How the Valuation is Built")

st.markdown("### Step 1 — Revenue Projection")

st.latex(r"Revenue_t = Revenue_{t-1} \times (1 + g)")

st.markdown("""
We start with current revenue and grow it using the selected growth rate.
This represents the expected expansion of the business over time.
""")

st.markdown("### Step 2 — Free Cash Flow")

st.latex(r"FCF = EBIT \times (1 - Tax) \times (1 - Reinvestment Rate)")

st.markdown("""
Revenue is converted into profit (EBIT), taxed, then adjusted for reinvestment needs.
This gives **cash actually available to investors**.
""")

st.markdown("### Step 3 — Discounting Cash Flows")

st.latex(r"DCF = \frac{FCF_t}{(1 + WACC)^t}")

st.markdown("""
Each cash flow is discounted using WACC because future money is worth less than present money.
""")

# -------------------------------
# 8️⃣ TABLE
# -------------------------------
st.header("8️⃣ DCF Projection Table")

df = pd.DataFrame({
    "Year": range(1, years + 1),
    "Revenue": revenues,
    "FCF": fcfs,
    "Discounted FCF": disc_fcfs
})

st.dataframe(df, use_container_width=True)

st.caption("""
Revenue is the starting engine of the model.
It flows through margins → cash flow → discounting → valuation.
""")
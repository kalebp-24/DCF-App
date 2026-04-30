#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 16:37:20 2026

@author: kalebpagel
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# -------------------------------
# PAGE CONFIG + STYLE
# -------------------------------
st.set_page_config(page_title="Equity Research DCF", layout="wide")

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}
h1, h2, h3 {
    font-weight: 600;
}
div[data-testid="stMetricValue"] {
    font-size: 20px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Equity Research DCF Workflow")
st.caption("A structured, step-by-step valuation model (Market → Cash Flow → WACC → DCF)")

# -------------------------------
# DATA LOADING
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
    st.error("Data unavailable or rate limit hit. Try again shortly.")
    st.stop()

# -------------------------------
# 1️⃣ COMPANY OVERVIEW
# -------------------------------
st.header("1️⃣ Company Overview")

price = info.get("currentPrice")
market_cap = info.get("marketCap")
beta = info.get("beta", 1.2)
shares = info.get("sharesOutstanding")
revenue = info.get("totalRevenue", 0)
debt = info.get("totalDebt", 0)
cash = info.get("totalCash", 0)
div_yield = info.get("dividendYield", 0)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Price", price)
col2.metric("Market Cap", f"{market_cap:,.0f}" if market_cap else "N/A")
col3.metric("Beta", beta)
col4.metric("Shares Outstanding", f"{shares:,.0f}")

st.markdown("""
📌 This section shows the **market’s current pricing and risk profile** of the company.
These inputs anchor all valuation assumptions.
""")

st.divider()

# -------------------------------
# STOCK PERFORMANCE
# -------------------------------
st.header("📈 5-Year Stock Performance")

norm = hist["Close"] / hist["Close"].iloc[0] * 100
st.line_chart(norm)

st.caption("Normalized price index (Base = 100). Used to understand long-term performance trend.")

st.divider()

# -------------------------------
# 2️⃣ CASH FLOW ANALYSIS
# -------------------------------
st.header("2️⃣ Cash Flow & Net Debt")

st.latex(r"Net\ Debt = Total\ Debt - Cash")

net_debt = debt - cash

st.metric("Net Debt", f"{net_debt:,.0f}")

st.markdown("### Free Cash Flow (Core Valuation Input)")

st.latex(r"FCF = Operating\ Cash\ Flow - Capital\ Expenditures")

st.markdown("""
📌 Free Cash Flow represents the **cash available to all investors after maintaining operations**.
It is the foundation of valuation in a DCF model.
""")

st.divider()

# -------------------------------
# 3️⃣ COST OF CAPITAL (WACC)
# -------------------------------
st.header("3️⃣ Cost of Capital (CAPM + WACC)")

rf = 0.04
erp = 0.06
rd = 0.05
tax_rate = 0.25

st.slider("Risk-Free Rate (Rf)", 0.00, 0.08, rf)
st.slider("Equity Risk Premium (ERP)", 0.05, 0.10, erp)
st.slider("Cost of Debt (Rd)", 0.01, 0.12, rd)
st.slider("Tax Rate", 0.00, 0.40, tax_rate)

Re = rf + beta * erp

E = price * shares
D = debt if debt else 0
V = E + D

E_V = E / V
D_V = D / V

wacc = (E_V * Re) + (D_V * rd * (1 - tax_rate))

st.markdown("### Key Formulas")

st.latex(r"R_e = R_f + \beta \times ERP")
st.latex(r"WACC = \frac{E}{V}R_e + \frac{D}{V}R_d(1 - T)")

col1, col2, col3 = st.columns(3)
col1.metric("Cost of Equity", f"{Re:.2%}")
col2.metric("WACC", f"{wacc:.2%}")
col3.metric("Debt Weight", f"{D_V:.2%}")

st.markdown("""
📌 WACC represents the **blended return required by all investors**.
It is the discount rate used in valuation.
""")

st.divider()

# -------------------------------
# 4️⃣ DCF SETTINGS
# -------------------------------
st.header("4️⃣ Forecast Assumptions")

growth = st.slider("Revenue Growth Rate", 0.00, 0.30, 0.05)
margin = st.slider("EBIT Margin", 0.00, 0.50, 0.20)
reinvestment = st.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
years = st.slider("Forecast Years", 3, 10, 5)
terminal_growth = st.slider("Terminal Growth Rate", 0.00, 0.05, 0.03)

st.markdown("""
📌 Longer forecasts increase detail but reduce certainty.
Most professional models use 5–10 years.
""")

st.divider()

# -------------------------------
# 5️⃣ DCF MODEL
# -------------------------------
st.header("5️⃣ Discounted Cash Flow Build")

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
intrinsic_value = equity_value / shares

# -------------------------------
# 6️⃣ RESULTS
# -------------------------------
st.header("6️⃣ Valuation Output")

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
# 7️⃣ DCF TABLE
# -------------------------------
st.header("7️⃣ DCF Breakdown Table")

df = pd.DataFrame({
    "Year": range(1, years + 1),
    "Revenue": revenues,
    "FCF": fcfs,
    "Discounted FCF": disc_fcfs
})

st.dataframe(df, use_container_width=True)

st.caption("""
📌 Revenue is the starting engine of the valuation model.
It drives EBIT → cash flow → intrinsic value.
""")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 14:58:21 2026

@author: kalebpagel
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# -------------------------------
# PAGE SETUP
# -------------------------------
st.set_page_config(page_title="DCF Valuation Model", layout="wide")

st.title("📊 Interactive DCF Valuation Model")
st.write("CAPM-based WACC + Yahoo Finance + Live valuation model")

# -------------------------------
# CACHE YAHOO FINANCE DATA (FIX RATE LIMIT)
# -------------------------------
@st.cache_data(ttl=3600)
def load_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.get_info()

# -------------------------------
# STEP 1: INPUT
# -------------------------------
st.header("1️⃣ Company Selection")

ticker = st.text_input("Enter Stock Ticker", "AAPL").upper()

try:
    info = load_data(ticker)
except:
    st.error("Yahoo Finance rate limit hit. Please wait a few minutes and refresh.")
    st.stop()

current_price = info.get("currentPrice")
revenue = info.get("totalRevenue")
shares = info.get("sharesOutstanding")
cash = info.get("totalCash", 0)
debt = info.get("totalDebt", 0)

if not revenue or not shares:
    st.warning("Invalid ticker or missing data.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Stock Price", current_price)
col2.metric("Revenue", f"${revenue:,.0f}")
col3.metric("Shares", f"{shares:,.0f}")

# -------------------------------
# STEP 2: WACC (CAPM MODEL)
# -------------------------------
st.header("2️⃣ Cost of Capital (CAPM WACC)")

rf = st.slider("Risk-Free Rate (Rf)", 0.00, 0.08, 0.04)
beta = st.slider("Beta (β)", 0.5, 2.0, 1.2)
erp = st.slider("Equity Risk Premium (ERP)", 0.05, 0.10, 0.06)

rd = st.slider("Cost of Debt (Rd)", 0.01, 0.12, 0.05)
tax_rate = st.slider("Tax Rate", 0.00, 0.40, 0.25)

# CAPM
cost_of_equity = rf + beta * erp

equity_market = current_price * shares
debt_value = debt if debt else 0
total_value = equity_market + debt_value

E_V = equity_market / total_value
D_V = debt_value / total_value

wacc = (E_V * cost_of_equity) + (D_V * rd * (1 - tax_rate))

col1, col2, col3 = st.columns(3)
col1.metric("Cost of Equity", f"{cost_of_equity:.2%}")
col2.metric("Debt Weight", f"{D_V:.2%}")
col3.metric("WACC", f"{wacc:.2%}")

# -------------------------------
# STEP 3: ASSUMPTIONS
# -------------------------------
st.header("3️⃣ Operating Assumptions")

growth = st.slider("Revenue Growth Rate", 0.00, 0.30, 0.05)
ebit_margin = st.slider("EBIT Margin", 0.00, 0.50, 0.20)
reinvestment = st.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
terminal_growth = st.slider("Terminal Growth Rate", 0.00, 0.05, 0.03)
years = st.slider("Projection Years", 3, 10, 5)

# -------------------------------
# STEP 4: DCF MODEL
# -------------------------------
st.header("4️⃣ Valuation Build")

rev = revenue
revenues, fcfs, discounted_fcfs = [], [], []

for year in range(1, years + 1):

    rev *= (1 + growth)

    ebit = rev * ebit_margin
    nopat = ebit * (1 - tax_rate)
    fcf = nopat * (1 - reinvestment)

    discounted = fcf / (1 + wacc) ** year

    revenues.append(rev)
    fcfs.append(fcf)
    discounted_fcfs.append(discounted)

terminal_fcf = fcfs[-1] * (1 + terminal_growth)
terminal_value = terminal_fcf / (wacc - terminal_growth)
terminal_discounted = terminal_value / (1 + wacc) ** years

enterprise_value = sum(discounted_fcfs) + terminal_discounted
equity_value = enterprise_value - debt_value + cash
intrinsic_value = equity_value / shares

# -------------------------------
# STEP 5: RESULTS
# -------------------------------
st.header("5️⃣ Valuation Results")

col1, col2, col3 = st.columns(3)
col1.metric("Enterprise Value", f"${enterprise_value:,.0f}")
col2.metric("Equity Value", f"${equity_value:,.0f}")
col3.metric("Intrinsic Value", f"${intrinsic_value:,.2f}")

diff = intrinsic_value - current_price

if diff > 0:
    st.success(f"📈 Undervalued by ${diff:.2f}")
else:
    st.error(f"📉 Overvalued by ${abs(diff):.2f}")

# -------------------------------
# STEP 6: TABLE
# -------------------------------
st.header("6️⃣ Projection Table")

df = pd.DataFrame({
    "Year": list(range(1, years + 1)),
    "Revenue": revenues,
    "FCF": fcfs,
    "Discounted FCF": discounted_fcfs
})

st.dataframe(df)

# -------------------------------
# STEP 7: VISUALS
# -------------------------------
st.header("7️⃣ Charts")

st.subheader("Revenue Growth")
st.line_chart(df.set_index("Year")["Revenue"])

st.subheader("Free Cash Flow")
st.line_chart(df.set_index("Year")["FCF"])

st.subheader("Discounted Cash Flow")
st.bar_chart(df.set_index("Year")["Discounted FCF"])

# -------------------------------
# STEP 8: EXPLANATION
# -------------------------------
st.header("8️⃣ How the Model Works")

st.markdown("""
**1. Revenue Projection**  
Revenue grows based on assumed growth rate.

**2. Operating Profit (EBIT)**  
We apply EBIT margin to revenue.

**3. Taxes & Cash Flow**  
NOPAT = EBIT × (1 - tax rate)

**4. Free Cash Flow**  
FCF = NOPAT × (1 - reinvestment rate)

**5. Discounting**  
We discount cash flows using WACC (CAPM-based).

**6. Terminal Value**  
We assume perpetual growth after projection period.
""")
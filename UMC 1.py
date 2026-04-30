#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 14:42:37 2026

@author: kalebpagel
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="DCF Valuation Model", layout="wide")

st.title("📊 Discounted Cash Flow (DCF) Valuation Model")
st.write("Built using Yahoo Finance data and user assumptions")

# -------------------------------
# SIDEBAR INPUTS
# -------------------------------
st.sidebar.header("📌 Model Assumptions")

ticker = st.sidebar.text_input("Stock Ticker", "AAPL").upper()

growth_rate = st.sidebar.slider("Revenue Growth Rate", 0.00, 0.30, 0.05)
ebit_margin = st.sidebar.slider("EBIT Margin", 0.00, 0.50, 0.20)
tax_rate = st.sidebar.slider("Tax Rate", 0.00, 0.40, 0.25)
reinvestment_rate = st.sidebar.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
wacc = st.sidebar.slider("WACC (Discount Rate)", 0.05, 0.20, 0.10)
terminal_growth = st.sidebar.slider("Terminal Growth Rate", 0.00, 0.05, 0.03)
years = st.sidebar.slider("Projection Years", 3, 10, 5)

# -------------------------------
# FETCH DATA
# -------------------------------
stock = yf.Ticker(ticker)
info = stock.info

current_price = info.get("currentPrice")
revenue = info.get("totalRevenue")
shares = info.get("sharesOutstanding")
cash = info.get("totalCash", 0)
debt = info.get("totalDebt", 0)

if not revenue or not shares:
    st.error("Missing financial data for this ticker.")
    st.stop()

st.subheader(f"📈 Analysis for {ticker}")

col1, col2, col3 = st.columns(3)
col1.metric("Current Price", f"${current_price}")
col2.metric("Revenue", f"${revenue:,.0f}")
col3.metric("Shares Outstanding", f"{shares:,.0f}")

# -------------------------------
# DCF MODEL
# -------------------------------
revenues = []
fcfs = []
discounted_fcfs = []

current_revenue = revenue

for year in range(1, years + 1):

    current_revenue *= (1 + growth_rate)
    ebit = current_revenue * ebit_margin
    nopat = ebit * (1 - tax_rate)
    reinvestment = nopat * reinvestment_rate
    fcf = nopat - reinvestment

    discounted_fcf = fcf / (1 + wacc) ** year

    revenues.append(current_revenue)
    fcfs.append(fcf)
    discounted_fcfs.append(discounted_fcf)

# Terminal Value
terminal_fcf = fcfs[-1] * (1 + terminal_growth)
terminal_value = terminal_fcf / (wacc - terminal_growth)
terminal_discounted = terminal_value / (1 + wacc) ** years

enterprise_value = sum(discounted_fcfs) + terminal_discounted
equity_value = enterprise_value - debt + cash
intrinsic_value = equity_value / shares

# -------------------------------
# RESULTS SECTION
# -------------------------------
st.subheader("💰 Valuation Result")

col1, col2, col3 = st.columns(3)
col1.metric("Enterprise Value", f"${enterprise_value:,.0f}")
col2.metric("Equity Value", f"${equity_value:,.0f}")
col3.metric("Intrinsic Value / Share", f"${intrinsic_value:,.2f}")

diff = intrinsic_value - current_price

if diff > 0:
    st.success(f"📈 Undervalued by ${diff:.2f}")
else:
    st.error(f"📉 Overvalued by ${abs(diff):.2f}")

# -------------------------------
# CASH FLOW TABLE
# -------------------------------
st.subheader("📊 Projected Cash Flows")

df = pd.DataFrame({
    "Year": list(range(1, years + 1)),
    "Revenue": revenues,
    "FCF": fcfs,
    "Discounted FCF": discounted_fcfs
})

st.dataframe(df)

# -------------------------------
# VISUALIZATION
# -------------------------------
st.subheader("📉 Cash Flow Trend")

st.line_chart(df.set_index("Year")[["FCF", "Discounted FCF"]])

# -------------------------------
# EXPLANATION SECTION
# -------------------------------
st.subheader("🧠 How this valuation works")

st.markdown("""
**Step 1: Revenue Projection**  
We grow revenue using the assumed growth rate.

**Step 2: EBIT Calculation**  
We apply EBIT margin to estimate operating profit.

**Step 3: NOPAT**  
We adjust EBIT for taxes to get Net Operating Profit After Tax.

**Step 4: Free Cash Flow (FCF)**  
We subtract reinvestment needs to estimate cash available to investors.

**Step 5: Discounting**  
We discount future cash flows using WACC (risk-adjusted rate).

**Step 6: Terminal Value**  
We estimate value beyond forecast period using perpetual growth model.
""")
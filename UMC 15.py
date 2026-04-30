#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 16:43:32 2026

@author: kalebpagel
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="DCF Terminal", layout="wide")

st.title("📊 Equity Research DCF Workflow")

# -------------------------------
# SAFE DATA LOADER
# -------------------------------
@st.cache_data(ttl=3600)
def load_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.get_info()
    hist = stock.history(period="5y")
    return info, hist

ticker = st.text_input("Enter Stock Ticker", "AAPL").upper()

if not ticker:
    st.stop()

try:
    info, hist = load_data(ticker)
except:
    st.error("Failed to load data (Yahoo Finance issue).")
    st.stop()

# -------------------------------
# SAFE EXTRACTION (IMPORTANT FIX)
# -------------------------------
price = info.get("currentPrice") or 0
market_cap = info.get("marketCap") or 0
beta = info.get("beta") or 1.2
shares = info.get("sharesOutstanding") or 1
debt = info.get("totalDebt") or 0
cash = info.get("totalCash") or 0
revenue = info.get("totalRevenue") or 0

# -------------------------------
# MARKET SNAPSHOT
# -------------------------------
st.header("Market Overview")

col1, col2, col3 = st.columns(3)
col1.metric("Price", price)
col2.metric("Market Cap", f"{market_cap:,.0f}")
col3.metric("Beta", beta)

# -------------------------------
# STOCK CHART
# -------------------------------
st.subheader("5Y Stock Performance")

if len(hist) > 0:
    norm = hist["Close"] / hist["Close"].iloc[0] * 100
    st.line_chart(norm)
else:
    st.warning("No price history available")

# -------------------------------
# INPUTS
# -------------------------------
st.header("Assumptions")

growth = st.slider("Revenue Growth", 0.00, 0.30, 0.05)
margin = st.slider("EBIT Margin", 0.00, 0.50, 0.20)
tax_rate = st.slider("Tax Rate", 0.00, 0.40, 0.25)
reinvestment = st.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
years = st.slider("Years", 3, 10, 5)
terminal_growth = st.slider("Terminal Growth", 0.00, 0.05, 0.03)

# -------------------------------
# WACC (SAFE)
# -------------------------------
rf = st.slider("Rf", 0.00, 0.08, 0.04)
erp = st.slider("ERP", 0.05, 0.10, 0.06)
rd = st.slider("Cost of Debt", 0.01, 0.12, 0.05)

Re = rf + beta * erp

E = price * shares
D = debt
V = max(E + D, 1)  # ✅ prevents division by zero

E_V = E / V
D_V = D / V

wacc = (E_V * Re) + (D_V * rd * (1 - tax_rate))

# -------------------------------
# SAFETY CHECK FOR WACC
# -------------------------------
if wacc <= terminal_growth:
    st.error("WACC must be greater than terminal growth rate.")
    st.stop()

# -------------------------------
# DCF MODEL
# -------------------------------
rev = revenue

fcfs, disc_fcfs = [], []

for t in range(1, years + 1):

    rev = rev * (1 + growth)
    ebit = rev * margin
    nopat = ebit * (1 - tax_rate)
    fcf = nopat * (1 - reinvestment)

    discounted = fcf / (1 + wacc) ** t

    fcfs.append(fcf)
    disc_fcfs.append(discounted)

terminal_fcf = fcfs[-1] * (1 + terminal_growth)
terminal_value = terminal_fcf / (wacc - terminal_growth)
terminal_discounted = terminal_value / (1 + wacc) ** years

enterprise_value = sum(disc_fcfs) + terminal_discounted
equity_value = enterprise_value - debt + cash
intrinsic_value = equity_value / max(shares, 1)

# -------------------------------
# OUTPUT
# -------------------------------
st.header("Valuation")

col1, col2, col3 = st.columns(3)
col1.metric("EV", f"{enterprise_value:,.0f}")
col2.metric("Equity", f"{equity_value:,.0f}")
col3.metric("Intrinsic", f"{intrinsic_value:.2f}")

diff = intrinsic_value - price

if diff > 0:
    st.success(f"Undervalued by {diff:.2f}")
else:
    st.error(f"Overvalued by {abs(diff):.2f}")
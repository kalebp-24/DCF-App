#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 16:22:32 2026

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

st.title("📊 Equity Research DCF Terminal")
st.caption("Load a company → analyze → value → interpret")

# -------------------------------
# CACHE DATA
# -------------------------------
@st.cache_data(ttl=3600)
def load_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.get_info(), stock.history(period="5y")

# -------------------------------
# INPUT SECTION (WITH BUTTON)
# -------------------------------
st.header("1️⃣ Company Selection")

ticker = st.text_input("Enter Stock Ticker", "AAPL").upper()

load = st.button("🔍 Load Analysis")

if load:

    try:
        info, hist = load_data(ticker)
    except:
        st.error("Yahoo Finance rate limit hit. Try again later.")
        st.stop()

    # -------------------------------
    # MARKET DATA
    # -------------------------------
    price = info.get("currentPrice")
    market_cap = info.get("marketCap")
    beta_market = info.get("beta", 1.2)
    shares = info.get("sharesOutstanding")
    debt = info.get("totalDebt", 0)
    cash = info.get("totalCash", 0)
    revenue = info.get("totalRevenue", 0)

    st.subheader("📌 Market Snapshot")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Price", price)
    col2.metric("Market Cap", f"{market_cap:,.0f}" if market_cap else "N/A")
    col3.metric("Beta", beta_market)
    col4.metric("Shares", f"{shares:,.0f}")

    # -------------------------------
    # STOCK PERFORMANCE GRAPH
    # -------------------------------
    st.subheader("📈 5-Year Stock Performance")

    norm = hist["Close"] / hist["Close"].iloc[0] * 100
    st.line_chart(norm)

    st.caption("Normalized performance (base = 100). Shows long-term trend independent of price level.")

    st.divider()

    # -------------------------------
    # ASSUMPTIONS
    # -------------------------------
    st.header("2️⃣ Operating Assumptions")

    growth = st.slider("Revenue Growth Rate", 0.00, 0.30, 0.05)
    st.caption("Revenue(t) = Revenue(t-1) × (1 + g)")

    margin = st.slider("EBIT Margin", 0.00, 0.50, 0.20)
    st.caption("EBIT = Revenue × EBIT Margin")

    tax_rate = st.slider("Tax Rate", 0.00, 0.40, 0.25)
    st.caption("NOPAT = EBIT × (1 - Tax Rate)")

    reinvestment = st.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
    st.caption("FCF = NOPAT × (1 - Reinvestment Rate)")

    years = st.slider("Projection Years", 3, 10, 5)

    terminal_growth = st.slider("Terminal Growth Rate", 0.00, 0.05, 0.03)
    st.caption("TV = FCF × (1 + g) / (WACC - g)")

    st.divider()

    # -------------------------------
    # WACC (SIMPLIFIED INPUT)
    # -------------------------------
    st.header("3️⃣ Discount Rate (WACC)")

    wacc = st.slider("WACC (Discount Rate)", 0.05, 0.20, 0.10)

    st.markdown("### 📘 Core Theory Behind WACC")

    st.latex(r"R_e = R_f + \beta \times ERP")
    st.latex(r"WACC = \frac{E}{V}R_e + \frac{D}{V}R_d(1 - T)")

    st.caption("WACC represents the blended cost of financing a company (equity + debt).")

    st.divider()

    # -------------------------------
    # DCF MODEL
    # -------------------------------
    st.header("4️⃣ DCF Valuation Build")

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
    intrinsic = equity_value / shares

    # -------------------------------
    # RESULTS
    # -------------------------------
    st.header("5️⃣ Valuation Output")

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
    # TABLE (DCF BREAKDOWN)
    # -------------------------------
    st.header("6️⃣ DCF Projection Table")

    df = pd.DataFrame({
        "Year": range(1, years + 1),
        "Revenue": revenues,
        "FCF": fcfs,
        "Discounted FCF": disc_fcfs
    })

    st.dataframe(df)

    st.caption("""
    📌 Revenue is included because it is the **starting engine of valuation**.
    Every downstream metric (EBIT → FCF → value) is derived from it.
    """)
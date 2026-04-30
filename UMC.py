#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 14:28:32 2026

@author: kalebpagel
"""

import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="DCF Valuation Tool", layout="wide")

st.title("📊 DCF Valuation Dashboard")
st.markdown("Estimate intrinsic value using a Discounted Cash Flow (DCF) model using Yahoo Finance data.")

# Sidebar
st.sidebar.header("🔍 Company Input")
ticker = st.sidebar.text_input("Enter Stock Ticker", "AAPL")

# Load data
if st.sidebar.button("Load Company Data"):

    with st.spinner("Fetching data..."):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            st.session_state.data = {
                "price": info.get("currentPrice", 0),
                "revenue": info.get("totalRevenue", 0),
                "shares": info.get("sharesOutstanding", 1),
                "debt": info.get("totalDebt", 0),
                "cash": info.get("totalCash", 0)
            }

        except:
            st.error("Error loading data")

# Show data
if "data" in st.session_state:

    data = st.session_state.data

    col1, col2, col3 = st.columns(3)
    col1.metric("Stock Price", f"${data['price']:.2f}")
    col2.metric("Revenue", f"${data['revenue']:,}")
    col3.metric("Shares", f"{data['shares']:,}")

    st.markdown("---")

    st.subheader("⚙️ Assumptions")

    growth = st.slider("Growth Rate", 0.0, 0.2, 0.05)
    margin = st.slider("EBIT Margin", 0.0, 0.5, 0.2)
    tax = st.slider("Tax Rate", 0.0, 0.4, 0.25)
    reinvest = st.slider("Reinvestment Rate", 0.0, 1.0, 0.3)
    wacc = st.slider("WACC", 0.01, 0.2, 0.1)
    terminal = st.slider("Terminal Growth", 0.0, 0.05, 0.03)
    years = st.slider("Years", 3, 10, 5)

    st.markdown("""
    💡 **Explanation**
    - Growth: Revenue growth assumption  
    - Margin: Profitability  
    - WACC: Discount rate  
    - Reinvestment: % reinvested into business  
    """)

    if st.button("Run DCF"):

        if wacc <= terminal:
            st.error("WACC must be greater than terminal growth")
        else:
            rev = data["revenue"]
            fcf_list = []
            disc_list = []

            for i in range(1, years + 1):
                rev *= (1 + growth)
                fcf = rev * margin * (1 - tax) * (1 - reinvest)
                disc = fcf / ((1 + wacc) ** i)

                fcf_list.append(fcf)
                disc_list.append(disc)

            terminal_fcf = fcf_list[-1] * (1 + terminal)
            terminal_val = terminal_fcf / (wacc - terminal)
            terminal_disc = terminal_val / ((1 + wacc) ** years)

            enterprise = sum(disc_list) + terminal_disc
            equity = enterprise - data["debt"] + data["cash"]
            intrinsic = equity / data["shares"]

            st.subheader("💰 Results")

            col1, col2 = st.columns(2)
            col1.metric("Intrinsic Value", f"${intrinsic:.2f}")
            col2.metric("Market Price", f"${data['price']:.2f}")

            if intrinsic > data["price"]:
                st.success("UNDERVALUED")
            else:
                st.error("OVERVALUED")

            df = pd.DataFrame({
                "Year": list(range(1, years + 1)),
                "FCF": fcf_list,
                "Discounted FCF": disc_list
            })

            st.subheader("📊 Breakdown")
            st.dataframe(df)
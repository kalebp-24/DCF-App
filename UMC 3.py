#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 14:50:54 2026

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
st.write("A full equity research-style DCF model using CAPM-based WACC and live Yahoo Finance data.")

# -------------------------------
# STEP 1: STOCK INPUT
# -------------------------------
st.header("1️⃣ Company Selection")

ticker = st.text_input("Enter Stock Ticker", "AAPL").upper()

stock = yf.Ticker(ticker)
info = stock.info

current_price = info.get("currentPrice")
revenue = info.get("totalRevenue")
shares = info.get("sharesOutstanding")
cash = info.get("totalCash", 0)
debt = info.get("totalDebt", 0)

if not revenue or not shares:
    st.warning("Enter a valid ticker to continue.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Stock Price", current_price)
col2.metric("Revenue", f"${revenue:,.0f}")
col3.metric("Shares Outstanding", f"{shares:,.0f}")

# -------------------------------
# STEP 2: WACC (CAPM MODEL)
# -------------------------------
st.header("2️⃣ Cost of Capital (CAPM-Based WACC)")

rf = st.slider("Risk-Free Rate (Rf)", 0.00, 0.08, 0.04)
beta = st.slider("Beta (β)", 0.5, 2.0, 1.2)
erp = st.slider("Equity Risk Premium (ERP)", 0.05, 0.10, 0.06)

rd = st.slider("Cost of Debt (Rd)", 0.01, 0.12, 0.05)
tax_rate = st.slider("Tax Rate", 0.00, 0.40, 0.25)

# CAPM
cost_of_equity = rf + beta * erp

equity_value_market = current_price * shares
debt_value = debt if debt else 0
total_value = equity_value_market + debt_value

E_V = equity_value_market / total_value
D_V = debt_value / total_value

wacc = (E_V * cost_of_equity) + (D_V * rd * (1 - tax_rate))

col1, col2, col3 = st.columns(3)
col1.metric("Cost of Equity (Re)", f"{cost_of_equity:.2%}")
col2.metric("Debt Weight", f"{D_V:.2%}")
col3.metric("WACC", f"{wacc:.2%}")

# -------------------------------
# STEP 3: OPERATING ASSUMPTIONS
# -------------------------------
st.header("3️⃣ Operating Assumptions")

growth = st.slider("Revenue Growth Rate", 0.00, 0.30, 0.05)
ebit_margin = st.slider("EBIT Margin", 0.00, 0.50, 0.20)
reinvestment_rate = st.slider("Reinvestment Rate", 0.00, 1.00, 0.30)
terminal_growth = st.slider("Terminal Growth Rate", 0.00, 0.05, 0.03)
years = st.slider("Projection Years", 3, 10, 5)

# -------------------------------
# STEP 4: DCF MODEL
# -------------------------------
st.header("4️⃣ Valuation Build")

current_revenue = revenue

revenues = []
fcfs = []
discounted_fcfs = []

for year in range(1, years + 1):

    current_revenue *= (1 + growth)

    ebit = current_revenue * ebit_margin
    nopat = ebit * (1 - tax_rate)
    fcf = nopat * (1 - reinvestment_rate)

    discounted_fcf = fcf / (1 + wacc) ** year

    revenues.append(current_revenue)
    fcfs.append(fcf)
    discounted_fcfs.append(discounted_fcf)

terminal_fcf = fcfs[-1] * (1 + terminal_growth)
terminal_value = terminal_fcf / (wacc - terminal_growth)
terminal_discounted = terminal_value / (1 + wacc) ** years

enterprise_value = sum(discounted_fcfs) + terminal_discounted
equity_value = enterprise_value - debt_value + cash
intrinsic_value = equity_value / shares

# -------------------------------
# STEP 5: RESULTS (LIVE)
# -------------------------------
st.header("5️⃣ Valuation Results")

col1, col2, col3 = st.columns(3)
col1.metric("Enterprise Value", f"${enterprise_value:,.0f}")
col2.metric("Equity Value", f"${equity_value:,.0f}")
col3.metric("Intrinsic Value / Share", f"${intrinsic_value:,.2f}")

diff = intrinsic_value - current_price

st.subheader("Valuation Signal")

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
st.header("7️⃣ Visual Breakdown")

st.subheader("Revenue Projection")
st.line_chart(df.set_index("Year")["Revenue"])

st.subheader("Free Cash Flow")
st.line_chart(df.set_index("Year")["FCF"])

st.subheader("Discounted Cash Flows")
st.bar_chart(df.set_index("Year")["Discounted FCF"])

# -------------------------------
# STEP 8: EXPLANATION (LEARNING LAYER)
# -------------------------------
st.header("8️⃣ How the Model Works")

st.markdown("""
**Step 1: Revenue Growth**  
We project future revenue using a constant growth rate.

**Step 2: Operating Profit**  
EBIT is calculated using the EBIT margin.

**Step 3: Taxes & Cash Flow**  
We compute NOPAT and subtract reinvestment to get Free Cash Flow.

**Step 4: Discounting**  
Future cash flows are discounted using WACC (risk-adjusted rate).

**Step 5: Terminal Value**  
We assume perpetual growth after projection period.

**Step 6: Equity Value**  
Enterprise value is adjusted for cash and debt to get equity value.
""")
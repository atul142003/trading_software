import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

from scanner.market_scanner import scan_market
from scanner.stocks import NIFTY50
from indicators.technical import add_indicators
import yfinance as yf


# ===========================
# PAGE CONFIG
# ===========================
st.set_page_config(
    page_title="Live Market Scanner",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Live Market Scanner")

# ===========================
# SIDEBAR CONFIG
# ===========================
st.sidebar.header("⚙️ Scanner Settings")

# Stock selection
mode = st.sidebar.radio(
    "Select Scan Mode",
    ["NIFTY50", "Custom Symbols", "Single Symbol"]
)

if mode == "NIFTY50":
    symbols = NIFTY50
    st.sidebar.info(f"Scanning {len(NIFTY50)} NIFTY50 stocks")

elif mode == "Custom Symbols":
    symbols_input = st.sidebar.text_area(
        "Enter symbols (comma-separated)",
        value="RELIANCE.NS, TCS.NS, INFY.NS",
        height=100
    )
    symbols = [s.strip().upper() for s in symbols_input.split(",")]
    st.sidebar.info(f"Scanning {len(symbols)} custom stocks")

else:  # Single Symbol
    symbol = st.sidebar.text_input(
        "Enter Symbol",
        value="RELIANCE.NS"
    )
    symbols = [symbol.upper()]
    st.sidebar.info(f"Scanning {symbol.upper()}")

# Refresh interval
refresh_interval = st.sidebar.slider(
    "Refresh Interval (seconds)",
    min_value=60,
    max_value=600,
    value=300,
    step=60
)

# Signal filter
min_confidence = st.sidebar.slider(
    "Minimum Confidence (%)",
    min_value=0,
    max_value=100,
    value=70,
    step=5
)

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox(
    "Auto Refresh",
    value=False
)

# ===========================
# MAIN SCAN FUNCTION
# ===========================
@st.cache_data(ttl=refresh_interval)
def run_scan(symbols_tuple):
    """Run market scan with caching"""
    return scan_market(list(symbols_tuple))


# ===========================
# DISPLAY RESULTS
# ===========================
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    scan_button = st.button(
        "🔍 Scan Market Now",
        key="scan_btn",
        use_container_width=True
    )

with col2:
    last_scan = st.empty()

with col3:
    status_placeholder = st.empty()

# Run scan
if scan_button or auto_refresh:
    with st.spinner("Scanning market..."):
        status_placeholder.info("⏳ Scanning in progress...")

        # Run the scan
        results_df = run_scan(tuple(symbols))

        if results_df.empty:
            status_placeholder.warning("⚠️ No signals found")
            st.info("Market conditions may not have produced any signals matching the criteria.")

        else:
            # Apply confidence filter
            filtered_df = results_df[
                results_df["Confidence"] >= min_confidence
            ].copy()

            # Update timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            last_scan.success(f"✅ Last scan: {current_time}")
            status_placeholder.success(f"Found {len(filtered_df)} signal(s)")

            # ===========================
            # SIGNALS SUMMARY METRICS
            # ===========================
            st.subheader("📈 Signal Summary")

            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

            buy_count = len(filtered_df[filtered_df["Signal"].isin(["BUY", "STRONG BUY"])])
            sell_count = len(filtered_df[filtered_df["Signal"].isin(["SELL", "STRONG SELL"])])
            hold_count = len(filtered_df[filtered_df["Signal"] == "HOLD"])
            avg_confidence = filtered_df["Confidence"].mean()

            with metric_col1:
                st.metric("🟢 BUY Signals", buy_count)

            with metric_col2:
                st.metric("🔴 SELL Signals", sell_count)

            with metric_col3:
                st.metric("⚪ HOLD Signals", hold_count)

            with metric_col4:
                st.metric("📊 Avg Confidence", f"{avg_confidence:.1f}%")

            # ===========================
            # DETAILED SIGNALS TABLE
            # ===========================
            st.subheader("🎯 Detailed Signals")

            # Format display dataframe
            display_df = filtered_df.copy()
            display_df["Confidence"] = display_df["Confidence"].apply(lambda x: f"{x:.1f}%")
            display_df["Buy Score"] = display_df["Buy Score"].apply(lambda x: f"{x:.2f}")
            display_df["Sell Score"] = display_df["Sell Score"].apply(lambda x: f"{x:.2f}")
            display_df["Net Score"] = display_df["Net Score"].apply(lambda x: f"{x:.2f}")

            # Color code signals
            def color_signal(signal):
                if signal in ["STRONG BUY", "BUY"]:
                    return "🟢"
                elif signal in ["STRONG SELL", "SELL"]:
                    return "🔴"
                else:
                    return "⚪"

            display_df["Signal"] = display_df["Signal"].apply(
                lambda x: f"{color_signal(x)} {x}"
            )

            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )

            # ===========================
            # SIGNAL DISTRIBUTION CHARTS
            # ===========================
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.subheader("Signal Distribution")

                signal_counts = filtered_df["Signal"].value_counts()
                fig_pie = go.Figure(
                    data=[
                        go.Pie(
                            labels=signal_counts.index,
                            values=signal_counts.values,
                            hole=0.3
                        )
                    ]
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_chart2:
                st.subheader("Confidence Distribution")

                fig_hist = go.Figure(
                    data=[
                        go.Histogram(
                            x=filtered_df["Confidence"],
                            nbinsx=20,
                            marker_color="royalblue"
                        )
                    ]
                )
                fig_hist.update_layout(
                    height=400,
                    xaxis_title="Confidence (%)",
                    yaxis_title="Count"
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            # ===========================
            # TOP SIGNALS
            # ===========================
            st.subheader("⭐ Top Signals by Confidence")

            top_signals = filtered_df.nlargest(5, "Confidence")[
                ["Symbol", "Signal", "Confidence", "Net Score"]
            ].copy()

            top_signals["Confidence"] = top_signals["Confidence"].apply(lambda x: f"{x:.1f}%")
            top_signals["Net Score"] = top_signals["Net Score"].apply(lambda x: f"{x:.2f}")

            st.dataframe(
                top_signals,
                use_container_width=True,
                hide_index=True
            )

            # ===========================
            # EXPORT OPTIONS
            # ===========================
            st.subheader("💾 Export Results")

            col_export1, col_export2 = st.columns(2)

            with col_export1:
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"scanner_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            with col_export2:
                json_str = filtered_df.to_json()
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"scanner_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )

# ===========================
# INFO & HELP
# ===========================
with st.expander("ℹ️ Scanner Information"):
    st.markdown("""
    ### Market Scanner Details

    **Signal Types:**
    - 🟢 **STRONG BUY**: High confidence bullish signal with strong AI backing
    - 🟢 **BUY**: Bullish signal with good confluence
    - 🔴 **STRONG SELL**: High confidence bearish signal
    - 🔴 **SELL**: Bearish signal
    - ⚪ **HOLD**: Mixed or weak signals

    **Analysis Components:**
    - Multi-timeframe analysis (1m, 5m, 15m, 30m, 60m, 1d)
    - Hybrid scoring engine (rule-based + AI model)
    - Technical indicators: EMA, RSI, MACD, ADX, Bollinger Bands, ATR
    - XGBoost ML model for direction prediction

    **Data Source:**
    - Real-time data via yfinance
    - 30-day historical data at 5-minute intervals
    - Updated every 5 minutes during market hours

    **Filters:**
    - Minimum confidence threshold
    - Trend strength validation
    - ADX-based trend confirmation
    - Risk controls on low timeframes
    """)

with st.expander("⚙️ Settings Info"):
    st.markdown(f"""
    **Current Settings:**
    - Scan Mode: {mode}
    - Symbols: {len(symbols)}
    - Refresh Interval: {refresh_interval}s
    - Minimum Confidence: {min_confidence}%
    - Auto Refresh: {auto_refresh}
    """)

# ===========================
# AUTO REFRESH LOOP
# ===========================
if auto_refresh:
    placeholder = st.empty()

    while True:
        time.sleep(refresh_interval)

        with placeholder.container():
            st.info(f"🔄 Next refresh in {refresh_interval}s...")
            time.sleep(1)

        st.rerun()

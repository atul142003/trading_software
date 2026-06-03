import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

from indicators.technical import add_indicators
from market_data import (
    download_ohlcv, 
    get_live_market_data, 
    run_backtest, 
    Portfolio, 
    get_portfolio_summary,
    calculate_position_size,
    calculate_stop_loss,
    calculate_take_profit,
    calculate_portfolio_risk,
    export_to_excel,
    export_to_pdf,
    get_model_accuracy_metrics,
    track_prediction_accuracy
)
from ai.trend import detect_trend
from ai.signals import generate_signal
from ai.predict import predict_direction
from ai.multi_timeframe import analyze_timeframe
from patterns.candles import detect_pattern
from ai.explain import explain_signal

st.set_page_config(
    page_title="AI Trading Software V1.1",
    layout="wide"
)

st.title("📈 AI Trading Software V1.1")

# Initialize portfolio in session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = Portfolio()

symbol = st.text_input(
    "Enter Symbol",
    "RELIANCE.NS"
)

# =========================
# LIVE MARKET UPDATES
# =========================

st.subheader("📊 Live Market Updates")

# Auto-refresh toggle
auto_refresh = st.checkbox("Auto-refresh (every 30 seconds)", value=False)

# Get live market data
live_data = get_live_market_data(symbol)

if "error" in live_data:
    st.error(f"Error fetching live data: {live_data['error']}")
else:
    # Display live market metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        change_color = "normal" if live_data["change"] >= 0 else "inverse"
        st.metric(
            "Current Price",
            f"₹{live_data['current_price']}",
            f"{live_data['change']:+.2f} ({live_data['change_percent']:+.2f}%)",
            delta_color=change_color
        )
    
    with col2:
        st.metric("Day High", f"₹{live_data['high']}")
    
    with col3:
        st.metric("Day Low", f"₹{live_data['low']}")
    
    with col4:
        st.metric("Volume", f"{live_data['volume']:,}")
    
    # Additional market info
    col5, col6, col7 = st.columns(3)
    
    with col5:
        st.metric("Open", f"₹{live_data['open']}")
    
    with col6:
        st.metric("52W High", f"₹{live_data['52w_high']}")
    
    with col7:
        st.metric("52W Low", f"₹{live_data['52w_low']}")
    
    # Market Cap
    market_cap_cr = live_data['market_cap'] / 10000000  # Convert to crores
    st.metric("Market Cap", f"₹{market_cap_cr:.2f} Cr")

# Auto-refresh logic
if auto_refresh:
    st_autorefresh = st.empty()
    import time
    while auto_refresh:
        live_data = get_live_market_data(symbol)
        if "error" not in live_data:
            with st_autorefresh.container():
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    change_color = "normal" if live_data["change"] >= 0 else "inverse"
                    st.metric(
                        "Current Price",
                        f"₹{live_data['current_price']}",
                        f"{live_data['change']:+.2f} ({live_data['change_percent']:+.2f}%)",
                        delta_color=change_color
                    )
                
                with col2:
                    st.metric("Day High", f"₹{live_data['high']}")
                
                with col3:
                    st.metric("Day Low", f"₹{live_data['low']}")
                
                with col4:
                    st.metric("Volume", f"{live_data['volume']:,}")
                
                col5, col6, col7 = st.columns(3)
                
                with col5:
                    st.metric("Open", f"₹{live_data['open']}")
                
                with col6:
                    st.metric("52W High", f"₹{live_data['52w_high']}")
                
                with col7:
                    st.metric("52W Low", f"₹{live_data['52w_low']}")
                
                market_cap_cr = live_data['market_cap'] / 10000000
                st.metric("Market Cap", f"₹{market_cap_cr:.2f} Cr")
        
        time.sleep(30)
        st.rerun()

st.divider()

# =========================
# PORTFOLIO TRACKING
# =========================

st.subheader("💼 Portfolio Tracking")

# Get portfolio summary
portfolio_summary = get_portfolio_summary(st.session_state.portfolio)

# Display portfolio overview
col1, col2, col3, col4 = st.columns(4)

with col1:
    pnl_color = "normal" if portfolio_summary['total_pnl'] >= 0 else "inverse"
    st.metric(
        "Total Portfolio Value",
        f"₹{portfolio_summary['total_value']:,.2f}",
        f"{portfolio_summary['total_pnl']:+,.2f} ({portfolio_summary['total_pnl_percent']:+.2f}%)",
        delta_color=pnl_color
    )

with col2:
    st.metric("Available Cash", f"₹{portfolio_summary['cash']:,.2f}")

with col3:
    invested = portfolio_summary['total_value'] - portfolio_summary['cash']
    st.metric("Invested Amount", f"₹{invested:,.2f}")

with col4:
    num_positions = len(portfolio_summary['positions'])
    st.metric("Number of Positions", num_positions)

# Add/Remove Position Section
st.divider()
st.subheader("📝 Manage Positions")

col_add, col_remove = st.columns(2)

with col_add:
    st.write("**Add Position**")
    add_symbol = st.text_input("Symbol", key="add_symbol")
    add_quantity = st.number_input("Quantity", min_value=1, value=10, key="add_quantity")
    add_price = st.number_input("Price (₹)", min_value=0.01, value=100.0, key="add_price")
    
    if st.button("Add to Portfolio", key="add_btn"):
        if add_symbol and add_quantity > 0 and add_price > 0:
            st.session_state.portfolio.add_position(add_symbol.upper(), add_quantity, add_price)
            st.success(f"Added {add_quantity} shares of {add_symbol.upper()} at ₹{add_price}")
            st.rerun()
        else:
            st.error("Please fill all fields correctly")

with col_remove:
    st.write("**Remove Position**")
    if portfolio_summary['positions']:
        remove_symbol = st.selectbox(
            "Select Symbol",
            options=list(portfolio_summary['positions'].keys()),
            key="remove_symbol"
        )
        remove_quantity = st.number_input(
            "Quantity to Remove",
            min_value=1,
            max_value=portfolio_summary['positions'][remove_symbol]['quantity'],
            value=portfolio_summary['positions'][remove_symbol]['quantity'],
            key="remove_quantity"
        )
        current_price = portfolio_summary['positions'][remove_symbol]['current_price']
        remove_price = st.number_input(
            "Sell Price (₹)",
            min_value=0.01,
            value=float(current_price) if current_price > 0 else 100.0,
            key="remove_price"
        )
        
        if st.button("Remove from Portfolio", key="remove_btn"):
            success = st.session_state.portfolio.remove_position(remove_symbol, remove_quantity, remove_price)
            if success:
                st.success(f"Removed {remove_quantity} shares of {remove_symbol} at ₹{remove_price}")
                st.rerun()
            else:
                st.error("Failed to remove position")
    else:
        st.info("No positions to remove")

# Display Current Positions
if portfolio_summary['positions']:
    st.divider()
    st.subheader("📋 Current Positions")
    
    positions_data = []
    for symbol, pos_data in portfolio_summary['positions'].items():
        positions_data.append({
            'Symbol': symbol,
            'Quantity': pos_data['quantity'],
            'Avg Price (₹)': round(pos_data['avg_price'], 2),
            'Current Price (₹)': round(pos_data['current_price'], 2),
            'Position Value (₹)': round(pos_data['position_value'], 2),
            'P&L (₹)': round(pos_data['pnl'], 2),
            'P&L (%)': round(pos_data['pnl_percent'], 2)
        })
    
    positions_df = pd.DataFrame(positions_data)
    
    # Color-code P&L
    def color_pnl(val):
        color = 'green' if val >= 0 else 'red'
        return f'color: {color}'
    
    styled_df = positions_df.style.map(color_pnl, subset=['P&L (₹)', 'P&L (%)'])
    
    st.dataframe(styled_df, use_container_width=True)
    
    # Export Portfolio
    st.divider()
    st.subheader("📥 Export Portfolio")
    
    col_pexp1, col_pexp2 = st.columns(2)
    
    with col_pexp1:
        if st.button("Export Portfolio to Excel", key="export_portfolio_excel"):
            portfolio_data = {
                "Portfolio Summary": pd.DataFrame([portfolio_summary]),
                "Current Positions": positions_df
            }
            excel_data = export_to_excel(portfolio_data)
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name="portfolio_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col_pexp2:
        if st.button("Export Portfolio to PDF", key="export_portfolio_pdf"):
            portfolio_data = {
                "Portfolio Summary": portfolio_summary,
                "Current Positions": positions_df
            }
            pdf_data = export_to_pdf(portfolio_data, "Portfolio Report")
            st.download_button(
                label="Download PDF",
                data=pdf_data,
                file_name="portfolio_report.pdf",
                mime="application/pdf"
            )
else:
    st.info("No positions in portfolio. Add positions to start tracking.")

st.divider()

# =========================
# RISK MANAGEMENT PANEL
# =========================

st.subheader("⚠️ Risk Management Panel")

# Position Sizing Calculator
st.write("**Position Sizing Calculator**")
col_ps1, col_ps2, col_ps3, col_ps4 = st.columns(4)

with col_ps1:
    account_balance = st.number_input("Account Balance (₹)", min_value=1000, value=100000, key="ps_balance")
with col_ps2:
    risk_per_trade = st.number_input("Risk Per Trade (%)", min_value=0.1, max_value=100.0, value=2.0, key="ps_risk")
with col_ps3:
    entry_price = st.number_input("Entry Price (₹)", min_value=0.01, value=100.0, key="ps_entry")
with col_ps4:
    stop_loss_price = st.number_input("Stop Loss Price (₹)", min_value=0.01, value=95.0, key="ps_sl")

if st.button("Calculate Position Size", key="calc_pos"):
    pos_result = calculate_position_size(account_balance, risk_per_trade, entry_price, stop_loss_price)
    
    if "error" in pos_result:
        st.error(pos_result["error"])
    else:
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("Position Size", f"{pos_result['position_size']} shares")
        with col_r2:
            st.metric("Position Value", f"₹{pos_result['position_value']:,.2f}")
        with col_r3:
            st.metric("Risk Amount", f"₹{pos_result['risk_amount']:,.2f}")

st.divider()

# Stop Loss Calculator
st.write("**Stop Loss Calculator**")
col_sl1, col_sl2, col_sl3 = st.columns(3)

with col_sl1:
    sl_entry = st.number_input("Entry Price (₹)", min_value=0.01, value=100.0, key="sl_entry")
with col_sl2:
    sl_method = st.selectbox("Method", ["atr", "percentage", "support"], key="sl_method")
with col_sl3:
    if sl_method == "atr":
        sl_atr = st.number_input("ATR Value", min_value=0.01, value=5.0, key="sl_atr")
        sl_multiplier = st.number_input("ATR Multiplier", min_value=0.5, max_value=5.0, value=2.0, key="sl_mult")
    elif sl_method == "percentage":
        sl_atr = st.number_input("Stop Loss %", min_value=0.1, max_value=50.0, value=5.0, key="sl_pct")
        sl_multiplier = 1.0
    else:
        sl_atr = st.number_input("Support Level (₹)", min_value=0.01, value=90.0, key="sl_support")
        sl_multiplier = 1.0

if st.button("Calculate Stop Loss", key="calc_sl"):
    sl_result = calculate_stop_loss(sl_entry, sl_atr, sl_multiplier, sl_method)
    
    if "error" in sl_result:
        st.error(sl_result["error"])
    else:
        col_slr1, col_slr2 = st.columns(2)
        with col_slr1:
            st.metric("Stop Loss Price", f"₹{sl_result['stop_loss_price']}")
        with col_slr2:
            st.metric("Stop Loss %", f"{sl_result['stop_loss_pct']}%")

st.divider()

# Take Profit Calculator
st.write("**Take Profit Calculator**")
col_tp1, col_tp2, col_tp3 = st.columns(3)

with col_tp1:
    tp_entry = st.number_input("Entry Price (₹)", min_value=0.01, value=100.0, key="tp_entry")
with col_tp2:
    tp_sl = st.number_input("Stop Loss Price (₹)", min_value=0.01, value=95.0, key="tp_sl")
with col_tp3:
    tp_ratio = st.number_input("Risk:Reward Ratio", min_value=0.5, max_value=10.0, value=2.0, key="tp_ratio")

if st.button("Calculate Take Profit", key="calc_tp"):
    tp_result = calculate_take_profit(tp_entry, tp_sl, tp_ratio)
    
    col_tpr1, col_tpr2 = st.columns(2)
    with col_tpr1:
        st.metric("Take Profit Price", f"₹{tp_result['take_profit_price']}")
    with col_tpr2:
        st.metric("Take Profit %", f"{tp_result['take_profit_pct']}%")

st.divider()

# Portfolio Risk Analysis
st.write("**Portfolio Risk Analysis**")
if portfolio_summary['positions']:
    current_prices = {symbol: data['current_price'] for symbol, data in portfolio_summary['positions'].items()}
    portfolio_risk = calculate_portfolio_risk(st.session_state.portfolio, current_prices)
    
    col_pr1, col_pr2, col_pr3 = st.columns(3)
    with col_pr1:
        st.metric("Total Exposure", f"₹{portfolio_risk['total_exposure']:,.2f}")
    with col_pr2:
        st.metric("Cash Ratio", f"{portfolio_risk['cash_ratio']}%")
    with col_pr3:
        st.metric("Number of Positions", portfolio_risk['number_of_positions'])
    
    if portfolio_risk['concentration_risk']:
        st.write("**Concentration Risk by Position**")
        concentration_df = pd.DataFrame(
            list(portfolio_risk['concentration_risk'].items()),
            columns=['Symbol', 'Portfolio %']
        )
        st.dataframe(concentration_df, use_container_width=True)
else:
    st.info("Add positions to analyze portfolio risk.")

st.divider()

# =========================
# MODEL ACCURACY DASHBOARD
# =========================

st.subheader("🎯 Model Accuracy Dashboard")

# Get model accuracy metrics
accuracy_metrics = get_model_accuracy_metrics()

if "error" in accuracy_metrics:
    st.error(f"Error loading accuracy metrics: {accuracy_metrics['error']}")
else:
    # Display key metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        acc_color = "normal" if accuracy_metrics["model_accuracy"] >= 50 else "inverse"
        st.metric(
            "Model Accuracy",
            f"{accuracy_metrics['model_accuracy']}%",
            delta_color=acc_color
        )
    
    with col_m2:
        st.metric("Precision", f"{accuracy_metrics['precision']}%")
    
    with col_m3:
        st.metric("Recall", f"{accuracy_metrics['recall']}%")
    
    with col_m4:
        st.metric("F1 Score", f"{accuracy_metrics['f1_score']}%")
    
    # Additional metrics
    col_m5, col_m6, col_m7 = st.columns(3)
    
    with col_m5:
        st.metric("ROC-AUC", f"{accuracy_metrics['roc_auc']}%")
    
    with col_m6:
        st.metric("Cross-Val Accuracy", f"{accuracy_metrics['cv_accuracy']}% (±{accuracy_metrics['cv_std']}%)")
    
    with col_m7:
        st.metric("Win Rate (Backtest)", f"{accuracy_metrics['win_rate']}%")
    
    # Backtest performance comparison
    st.divider()
    st.write("**Backtest Performance vs Buy & Hold**")
    
    col_bp1, col_bp2, col_bp3 = st.columns(3)
    
    with col_bp1:
        return_color = "normal" if accuracy_metrics["backtest_return"] >= 0 else "inverse"
        st.metric(
            "Strategy Returns",
            f"+{accuracy_metrics['backtest_return']}%",
            delta_color=return_color
        )
    
    with col_bp2:
        st.metric("Buy & Hold Returns", f"+{accuracy_metrics['buy_hold_return']}%")
    
    with col_bp3:
        st.metric("Outperformance", f"+{accuracy_metrics['outperformance']}%")
    
    # Detailed metrics table
    st.divider()
    st.write("**Detailed Model Metrics**")
    
    detailed_metrics = {
        "Metric": [
            "Model Accuracy",
            "Precision",
            "Recall",
            "F1 Score",
            "ROC-AUC",
            "Cross-Val Accuracy",
            "Cross-Val Std Dev",
            "Specificity",
            "Sensitivity",
            "Backtest Return",
            "Buy & Hold Return",
            "Win Rate",
            "Outperformance"
        ],
        "Value": [
            f"{accuracy_metrics['model_accuracy']}%",
            f"{accuracy_metrics['precision']}%",
            f"{accuracy_metrics['recall']}%",
            f"{accuracy_metrics['f1_score']}%",
            f"{accuracy_metrics['roc_auc']}%",
            f"{accuracy_metrics['cv_accuracy']}%",
            f"±{accuracy_metrics['cv_std']}%",
            f"{accuracy_metrics['specificity']}%",
            f"{accuracy_metrics['sensitivity']}%",
            f"+{accuracy_metrics['backtest_return']}%",
            f"+{accuracy_metrics['buy_hold_return']}%",
            f"{accuracy_metrics['win_rate']}%",
            f"+{accuracy_metrics['outperformance']}%"
        ],
        "Assessment": [
            "Fair" if accuracy_metrics['model_accuracy'] >= 50 else "Low",
            "Low" if accuracy_metrics['precision'] < 50 else "Good",
            "Good" if accuracy_metrics['recall'] >= 60 else "Fair",
            "Fair" if accuracy_metrics['f1_score'] >= 40 else "Low",
            "Fair" if accuracy_metrics['roc_auc'] >= 60 else "Low",
            "Inconsistent" if accuracy_metrics['cv_std'] > 10 else "Stable",
            "High" if accuracy_metrics['cv_std'] > 15 else "Moderate",
            "Fair" if accuracy_metrics['specificity'] >= 50 else "Low",
            "Good" if accuracy_metrics['sensitivity'] >= 60 else "Fair",
            "Excellent" if accuracy_metrics['backtest_return'] > 100 else "Good",
            "Baseline",
            "Good" if accuracy_metrics['win_rate'] >= 55 else "Fair",
            "Excellent" if accuracy_metrics['outperformance'] > 50 else "Good"
        ]
    }
    
    st.dataframe(
        pd.DataFrame(detailed_metrics),
        width="stretch"
    )
    
    # Model status
    st.divider()
    st.write("**Model Status**")
    
    if accuracy_metrics['model_accuracy'] >= 55 and accuracy_metrics['win_rate'] >= 55:
        st.success("✅ Model is performing well - Ready for paper trading")
    elif accuracy_metrics['model_accuracy'] >= 50:
        st.warning("⚠️ Model performance is fair - Use with caution")
    else:
        st.error("❌ Model needs improvement - Not recommended for trading")

st.divider()

if st.button("Analyze"):

    # Download Daily Data
    df = download_ohlcv(symbol, period="2y", interval="1d")

    if len(df) == 0:
        st.error("No data found.")
        st.stop()

    # Add Indicators
    df = add_indicators(df)

    latest = df.iloc[-1]
    reasons = explain_signal(latest)

    # Core Analysis
    trend = detect_trend(latest)

    signal = generate_signal(latest)

    pattern = detect_pattern(df)

    # AI Prediction
    features = [
        latest["RSI"],
        latest["EMA20"],
        latest["EMA50"],
        latest["MACD"]
    ]

    prediction, confidence = predict_direction(features)

    # =========================
    # MAIN ANALYSIS
    # =========================

    st.subheader("Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Trend", trend)

    with col2:
        st.metric("Signal", signal)

    with col3:
        st.metric("Pattern", pattern)

    st.metric(
        "AI Prediction",
        f"{prediction} ({confidence}%)"
    )

    # =========================
    # INDICATORS
    # =========================

    st.subheader("Technical Indicators")

    indicator_data = {
        "RSI": round(latest["RSI"], 2),
        "MACD": round(latest["MACD"], 2),
        "EMA20": round(latest["EMA20"], 2),
        "EMA50": round(latest["EMA50"], 2),
        "EMA200": round(latest["EMA200"], 2),
        "ATR": round(latest["ATR"], 2),
        "ADX": round(latest["ADX"], 2)
    }

    st.dataframe(
    pd.DataFrame(
        indicator_data.items(),
        columns=["Indicator", "Value"]
    ),
    width="stretch"
    )

    # =========================
    # MULTI TIMEFRAME ANALYSIS
    # =========================

    st.subheader("Multi-Timeframe Analysis")

    timeframes = {
        "1 Min": ("1m", "7d"),
        "5 Min": ("5m", "30d"),
        "15 Min": ("15m", "60d"),
        "30 Min": ("30m", "60d"),
        "1 Hour": ("60m", "730d"),
        "1 Day": ("1d", "2y")
    }

    results = []

    for name, (interval, period) in timeframes.items():

        try:
            result = analyze_timeframe(
                symbol,
                interval,
                period
            )

            if result:
                results.append({
                    "Timeframe": name,
                    **result
                })

        except Exception as e:
            results.append({
                "Timeframe": name,
                "Trend": "Error",
                "Signal": str(e),
                "RSI": "",
                "ADX": ""
            })

    st.dataframe(
    pd.DataFrame(results),
    width="stretch"
    )

    st.subheader("Signal Explanation")

    for reason in reasons:
        st.markdown(f"✓ {reason}")

    # =========================
    # PRICE CHART
    # =========================

    st.subheader("Price Chart")

    # Add auto-refresh controls
    col_refresh1, col_refresh2 = st.columns([2, 1])
    with col_refresh1:
        auto_refresh = st.checkbox("Auto-refresh", value=False, key="chart_auto_refresh")
    with col_refresh2:
        if auto_refresh:
            refresh_interval = st.selectbox(
                "Refresh every",
                [5, 10, 30, 60],
                index=1,
                key="chart_refresh_interval"
            )
            st.write(f"seconds")

    # Create candlestick chart with professional features
    fig = go.Figure()

    # Add candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='OHLC',
        increasing_line_color='#00ff00',
        decreasing_line_color='#ff0000'
    ))

    # Add volume bars
    fig.add_trace(go.Bar(
        x=df.index,
        y=df['Volume'],
        name='Volume',
        yaxis='y2',
        marker_color='rgba(128, 128, 128, 0.3)',
        opacity=0.3
    ))

    # Add moving averages
    if 'EMA20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['EMA20'],
            name='EMA20',
            line=dict(color='yellow', width=1),
            opacity=0.7
        ))

    if 'EMA50' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['EMA50'],
            name='EMA50',
            line=dict(color='orange', width=1),
            opacity=0.7
        ))

    if 'EMA200' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['EMA200'],
            name='EMA200',
            line=dict(color='blue', width=1),
            opacity=0.7
        ))

    # Update layout for professional trading terminal
    fig.update_layout(
        title=f'{symbol} Professional Trading Terminal',
        xaxis_title='Date',
        yaxis_title='Price',
        template='plotly_dark',
        height=700,
        xaxis_rangeslider_visible=True,
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

    # =========================
    # LAST 10 CANDLES
    # =========================

    st.subheader("Recent Market Data")

    st.dataframe(
    df.tail(10),
    width="stretch"
    )

    # Export Analysis
    st.divider()
    st.subheader("📥 Export Analysis")
    
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        if st.button("Export Analysis to Excel", key="export_analysis_excel"):
            analysis_data = {
                "Technical Indicators": pd.DataFrame([indicator_data]),
                "Multi-Timeframe Analysis": pd.DataFrame(results),
                "Recent Market Data": df.tail(10)
            }
            excel_data = export_to_excel(analysis_data)
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name=f"{symbol}_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col_exp2:
        if st.button("Export Analysis to PDF", key="export_analysis_pdf"):
            analysis_data = {
                "Technical Indicators": indicator_data,
                "Multi-Timeframe Analysis": results,
                "Recent Market Data": df.tail(10)
            }
            pdf_data = export_to_pdf(analysis_data, f"{symbol} Analysis Report")
            st.download_button(
                label="Download PDF",
                data=pdf_data,
                file_name=f"{symbol}_analysis.pdf",
                mime="application/pdf"
            )

    # =========================
    # BACKTESTING RESULTS
    # =========================

    st.divider()
    st.subheader("📊 Backtesting Results")

    if st.button("Run Backtest"):
        with st.spinner("Running backtest..."):
            backtest_results = run_backtest(df, "EMARSIMACDStrategy")
            
            if "error" in backtest_results:
                st.error(f"Backtest failed: {backtest_results['error']}")
            else:
                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    return_color = "normal" if backtest_results["Return (%)"] >= 0 else "inverse"
                    st.metric(
                        "Total Return",
                        f"{backtest_results['Return (%)']}%",
                        delta_color=return_color
                    )
                
                with col2:
                    st.metric("Sharpe Ratio", backtest_results["Sharpe Ratio"])
                
                with col3:
                    st.metric("Win Rate", f"{backtest_results['Win Rate (%)']}%")
                
                with col4:
                    dd_color = "inverse" if backtest_results["Max Drawdown (%)"] < 0 else "normal"
                    st.metric(
                        "Max Drawdown",
                        f"{backtest_results['Max Drawdown (%)']}%",
                        delta_color=dd_color
                    )
                
                # Additional metrics
                col5, col6, col7 = st.columns(3)
                
                with col5:
                    st.metric("Total Trades", backtest_results["Total Trades"])
                
                with col6:
                    st.metric("Profit Factor", backtest_results["Profit Factor"])
                
                with col7:
                    st.metric("Final Equity", f"₹{backtest_results['Final Equity']:,.2f}")
                
                # Detailed results table
                st.subheader("Detailed Backtest Metrics")
                
                detailed_metrics = {
                    "Metric": [
                        "Return (%)",
                        "Sharpe Ratio",
                        "Max Drawdown (%)",
                        "Win Rate (%)",
                        "Total Trades",
                        "Avg Trade (%)",
                        "Best Trade (%)",
                        "Worst Trade (%)",
                        "Profit Factor",
                        "Expectancy (%)",
                        "Final Equity ($)",
                        "Avg Trade Duration"
                    ],
                    "Value": [
                        backtest_results["Return (%)"],
                        backtest_results["Sharpe Ratio"],
                        backtest_results["Max Drawdown (%)"],
                        backtest_results["Win Rate (%)"],
                        backtest_results["Total Trades"],
                        backtest_results["Avg Trade (%)"],
                        backtest_results["Best Trade (%)"],
                        backtest_results["Worst Trade (%)"],
                        backtest_results["Profit Factor"],
                        backtest_results["Expectancy"],
                        backtest_results["Final Equity"],
                        backtest_results["Avg Trade Duration"]
                    ]
                }
                
                st.dataframe(
                    pd.DataFrame(detailed_metrics),
                    width="stretch"
                )
                
                # Trade History
                if 'trades' in backtest_results and not backtest_results['trades'].empty:
                    st.subheader("📜 Trade History")
                    
                    trades_df = backtest_results['trades'].copy()
                    
                    # Format the trades dataframe for better display
                    if 'EntryTime' in trades_df.columns:
                        trades_df['EntryTime'] = pd.to_datetime(trades_df['EntryTime'])
                    if 'ExitTime' in trades_df.columns:
                        trades_df['ExitTime'] = pd.to_datetime(trades_df['ExitTime'])
                    
                    # Calculate PnL percentage if not present
                    if 'PnL' in trades_df.columns and 'EntryPrice' in trades_df.columns:
                        trades_df['PnL %'] = (trades_df['PnL'] / trades_df['EntryPrice'] * 100).round(2)
                    
                    # Select and rename columns for display
                    display_columns = []
                    column_mapping = {}
                    
                    if 'EntryTime' in trades_df.columns:
                        display_columns.append('EntryTime')
                        column_mapping['EntryTime'] = 'Entry Date'
                    if 'ExitTime' in trades_df.columns:
                        display_columns.append('ExitTime')
                        column_mapping['ExitTime'] = 'Exit Date'
                    if 'EntryPrice' in trades_df.columns:
                        display_columns.append('EntryPrice')
                        column_mapping['EntryPrice'] = 'Entry Price (₹)'
                    if 'ExitPrice' in trades_df.columns:
                        display_columns.append('ExitPrice')
                        column_mapping['ExitPrice'] = 'Exit Price (₹)'
                    if 'Size' in trades_df.columns:
                        display_columns.append('Size')
                        column_mapping['Size'] = 'Quantity'
                    if 'PnL' in trades_df.columns:
                        display_columns.append('PnL')
                        column_mapping['PnL'] = 'PnL (₹)'
                    if 'PnL %' in trades_df.columns:
                        display_columns.append('PnL %')
                        column_mapping['PnL %'] = 'PnL (%)'
                    if 'Duration' in trades_df.columns:
                        display_columns.append('Duration')
                        column_mapping['Duration'] = 'Duration'
                    
                    if display_columns:
                        trades_display = trades_df[display_columns].copy()
                        trades_display = trades_display.rename(columns=column_mapping)
                        
                        # Add win/loss indicator
                        if 'PnL (₹)' in trades_display.columns:
                            trades_display['Result'] = trades_display['PnL (₹)'].apply(
                                lambda x: '✅ WIN' if x > 0 else '❌ LOSS'
                            )
                        
                        st.dataframe(
                            trades_display,
                            width="stretch",
                            use_container_width=True
                        )
                        
                        # Trade summary
                        winning_trades = len(trades_df[trades_df['PnL'] > 0]) if 'PnL' in trades_df.columns else 0
                        losing_trades = len(trades_df[trades_df['PnL'] < 0]) if 'PnL' in trades_df.columns else 0
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Winning Trades", winning_trades)
                        with col2:
                            st.metric("Losing Trades", losing_trades)
                        with col3:
                            st.metric("Win/Loss Ratio", f"{winning_trades}:{losing_trades}" if losing_trades > 0 else f"{winning_trades}:0")
                else:
                    st.info("No trade history available for this backtest.")
                
                # Export Backtest Results
                st.divider()
                st.subheader("📥 Export Backtest Results")
                
                col_bexp1, col_bexp2 = st.columns(2)
                
                with col_bexp1:
                    if st.button("Export Backtest to Excel", key="export_backtest_excel"):
                        backtest_data = {
                            "Backtest Metrics": pd.DataFrame([backtest_results]),
                            "Trade History": trades_df if 'trades_df' in locals() else pd.DataFrame()
                        }
                        excel_data = export_to_excel(backtest_data)
                        st.download_button(
                            label="Download Excel",
                            data=excel_data,
                            file_name=f"{symbol}_backtest.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                
                with col_bexp2:
                    if st.button("Export Backtest to PDF", key="export_backtest_pdf"):
                        backtest_data = {
                            "Backtest Metrics": backtest_results,
                            "Trade History": trades_df if 'trades_df' in locals() else pd.DataFrame()
                        }
                        pdf_data = export_to_pdf(backtest_data, f"{symbol} Backtest Report")
                        st.download_button(
                            label="Download PDF",
                            data=pdf_data,
                            file_name=f"{symbol}_backtest.pdf",
                            mime="application/pdf"
                        )
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
    page_title="ASA Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Professional Header
st.markdown("""
<div class="main-header">
    <div style="display: flex; align-items: center; gap: 1rem;">
        <img src="icon.png" alt="ASA Trading Icon" style="width: 60px; height: 60px; border-radius: 10px;">
        <div>
            <h1 style="margin: 0;">ASA Trading</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">Advanced AI-Powered Trading Analysis Platform</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["Dashboard", "Market Analysis", "Portfolio", "Risk Management", "Backtesting"],
    label_visibility="collapsed"
)

# Initialize portfolio in session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = Portfolio()

# Dashboard Page
if page == "Dashboard":
    st.header("🏠 Dashboard")
    
    # Quick Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Portfolio Value", "₹100,000", "+0%")
    with col2:
        st.metric("Total P&L", "₹0", "0%")
    with col3:
        st.metric("Active Positions", "0")
    
    st.divider()
    
    # Symbol Input
    symbol = st.text_input(
        "Enter Symbol for Analysis",
        "RELIANCE.NS",
        key="dashboard_symbol"
    )
    
    if symbol:
        st.subheader(f"📊 {symbol} Quick Overview")
        
        # Fetch and display quick data
        try:
            df = download_ohlcv(symbol, period="1mo", interval="1d")
            if not df.empty:
                df = add_indicators(df)
                
                # Quick Chart
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='OHLC'
                ))
                fig.update_layout(
                    title=f'{symbol} Price Chart',
                    template='plotly_dark',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Quick Stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Current Price", f"₹{df['Close'].iloc[-1]:.2f}")
                with col2:
                    st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
                with col3:
                    st.metric("MACD", f"{df['MACD'].iloc[-1]:.2f}")
                with col4:
                    st.metric("ATR", f"{df['ATR'].iloc[-1]:.2f}")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
    
    st.divider()
    st.info("👈 Use the sidebar to navigate to other sections")
    
# Market Analysis Page
elif page == "Market Analysis":
    st.header("📈 Market Analysis")
    symbol = st.text_input("Enter Symbol", "RELIANCE.NS", key="analysis_symbol")
    
    if symbol:
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

# Portfolio Page
elif page == "Portfolio":
    st.header("💼 Portfolio Management")
    
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
                try:
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
                except ImportError as e:
                    st.error(f"Excel export requires openpyxl. Install with: pip install openpyxl")
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
        
        with col_pexp2:
            if st.button("Export Portfolio to PDF", key="export_portfolio_pdf"):
                try:
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
                except ImportError as e:
                    st.error(f"PDF export requires reportlab. Install with: pip install reportlab")
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
    else:
        st.info("No positions in portfolio. Add positions to start tracking.")

# Risk Management Page
elif page == "Risk Management":
    st.header("⚠️ Risk Management")
    
    # Position Sizing Calculator
    st.subheader("Position Sizing Calculator")
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
    st.subheader("Stop Loss Calculator")
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
    st.subheader("Take Profit Calculator")
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
    st.subheader("Portfolio Risk Analysis")
    portfolio_summary = get_portfolio_summary(st.session_state.portfolio)
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

# Backtesting Page
elif page == "Backtesting":
    st.header("📊 Backtesting")
    st.info("Backtesting functionality coming soon. Use Market Analysis for now.")
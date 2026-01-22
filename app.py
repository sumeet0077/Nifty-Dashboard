import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import io
import time
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Nifty 500 Market Breadth",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Modern Dark Theme
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #374151;
        text-align: center;
    }
    h1, h2, h3 {
        color: #f8fafc !important;
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. ROBUST DATA ENGINE (With Rate Limit Protection)
# ---------------------------------------------------------
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_nifty500_tickers():
    """Fetches the official Nifty 500 list from NSE with fallback."""
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        s = requests.get(url, headers=headers, timeout=5).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')))
        return [symbol + ".NS" for symbol in df['Symbol']]
    except Exception as e:
        # Failsafe: If NSE is down, use a solid fallback list
        return ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'LICI.NS', 'HUL.NS']

@st.cache_data(ttl=3600)
def fetch_data_robust(tickers):
    """Downloads data in small batches to avoid Yahoo blocking the IP."""
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    
    # SPLIT TICKERS INTO BATCHES OF 30 (Conservative batch size)
    chunk_size = 30
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    all_data_list = []
    
    # Progress Bar
    progress_text = "Fetching market data safely..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, batch in enumerate(ticker_chunks):
        try:
            # Download batch
            batch_data = yf.download(batch, start=start_date, progress=False, threads=True)
            
            # Extract 'Adj Close' safely
            if isinstance(batch_data.columns, pd.MultiIndex):
                if 'Adj Close' in batch_data.columns.get_level_values(0):
                    batch_data = batch_data['Adj Close']
                elif 'Close' in batch_data.columns.get_level_values(0):
                    batch_data = batch_data['Close']
                else:
                    # Specific fix for some yfinance versions
                    try:
                        batch_data = batch_data.xs('Adj Close', axis=1, level=0, drop_level=True)
                    except:
                        pass # Keep as is if structure is weird

            all_data_list.append(batch_data)
            
            # Update progress bar
            percent_complete = int(((i + 1) / len(ticker_chunks)) * 100)
            my_bar.progress(percent_complete, text=f"Downloading batch {i+1}/{len(ticker_chunks)}")
            
            # CRITICAL: Wait to be polite to Yahoo
            time.sleep(1.0)
            
        except Exception as e:
            print(f"Skipped batch {i}: {e}")
            continue

    my_bar.empty() # Clear the progress bar when done
    
    # Combine everything
    if all_data_list:
        full_data = pd.concat(all_data_list, axis=1)
        # Remove duplicate columns if any
        full_data = full_data.loc[:, ~full_data.columns.duplicated()]
        return full_data
    else:
        return pd.DataFrame()

# ---------------------------------------------------------
# 3. LOGIC ENGINE
# ---------------------------------------------------------
def calculate_breadth(data):
    if data.empty:
        return pd.Series()
        
    sma_200 = data.rolling(window=200).mean()
    valid_stocks = data.notna().sum(axis=1)
    
    # "Quorum Rule": Ignore days with bad data (<20% of stocks found)
    # This prevents the chart from crashing to 0% if Yahoo fails for a day
    valid_mask = valid_stocks >= (len(data.columns) * 0.2) 
    
    count_above = (data >= sma_200).sum(axis=1)
    breadth = (count_above / valid_stocks) * 100
    
    # Filter bad days
    breadth[~valid_mask] = pd.NA
    return breadth.dropna()

# ---------------------------------------------------------
# 4. UI RENDERING
# ---------------------------------------------------------
st.title("⚡ Nifty 500 Market Breadth")
st.markdown("### Real-time Market Strength Indicator")

# Execute
tickers = get_nifty500_tickers()
raw_data = fetch_data_robust(tickers) # Uses the new robust function
breadth_series = calculate_breadth(raw_data)

# Key Metrics
if not breadth_series.empty:
    latest_val = breadth_series.iloc[-1]
    prev_val = breadth_series.iloc[-2]
    change = latest_val - prev_val
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Stocks > 200 SMA", value=f"{latest_val:.1f}%", delta=f"{change:.1f}%")
    
    with col2:
        sentiment = "Neutral"
        if latest_val > 80: sentiment = "Overbought (Risk)"
        elif latest_val < 20: sentiment = "Oversold (Buy)"
        elif change > 0: sentiment = "Improving"
        else: sentiment = "Weakening"
        
        st.metric(label="Market Sentiment", value=sentiment, delta_color="off")
        
    with col3:
        st.metric(label="Total Stocks Tracked", value=len(tickers))

    # -----------------------------------------------------
    # 5. MODERN CHART (Plotly)
    # -----------------------------------------------------
    fig = go.Figure()

    # Gradient Area Chart
    fig.add_trace(go.Scatter(
        x=breadth_series.index, 
        y=breadth_series.values,
        mode='lines',
        name='Breadth',
        line=dict(color='#00f2ff', width=2), # Cyan Neon
        fill='tozeroy',
        fillcolor='rgba(0, 242, 255, 0.1)'
    ))

    # Reference Zones
    zones = [(90, 'red'), (80, 'orange'), (20, 'green'), (10, 'lime')]
    for level, color in zones:
        fig.add_shape(type="line", x0=breadth_series.index.min(), x1=breadth_series.index.max(), 
                      y0=level, y1=level, line=dict(color=color, dash='dot', width=1))

    # Layout
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(range=[0, 100], gridcolor='#374151'),
        xaxis=dict(gridcolor='#374151'),
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        hovermode="x unified",
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Historical Data Table (Expandable)
    with st.expander("View Raw Data"):
        st.dataframe(breadth_series.sort_index(ascending=False), use_container_width=True)

else:
    st.error("Could not fetch data. The server might be busy. Please refresh in 1 minute.")

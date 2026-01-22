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

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .metric-card { background-color: #1f2937; border: 1px solid #374151; }
    h1, h2, h3 { color: #f8fafc !important; font-family: 'Inter', sans-serif; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. ROBUST DATA ENGINE (Ultra-Safe Mode)
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_nifty500_tickers():
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        s = requests.get(url, headers=headers, timeout=10).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')))
        # Filter out the fake "Dummy" ticker that NSE includes
        symbols = [x + ".NS" for x in df['Symbol'] if "DUMMY" not in x]
        return symbols
    except Exception as e:
        return ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS']

@st.cache_data(ttl=3600)
def fetch_data_safe(tickers):
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    
    # ULTRA-SAFE CONFIGURATION
    chunk_size = 15          # Very small batches
    sleep_time = 2.0         # Long sleep between batches
    
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    all_data_list = []
    
    # Progress UI
    progress_text = "Fetching data (Slow & Safe mode)..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, batch in enumerate(ticker_chunks):
        # Retry mechanism
        for attempt in range(2): 
            try:
                # Download
                batch_data = yf.download(batch, start=start_date, progress=False, threads=False, timeout=20)
                
                # Clean Data
                if isinstance(batch_data.columns, pd.MultiIndex):
                    if 'Adj Close' in batch_data.columns.get_level_values(0):
                        batch_data = batch_data['Adj Close']
                    elif 'Close' in batch_data.columns.get_level_values(0):
                        batch_data = batch_data['Close']
                    else:
                        try: batch_data = batch_data.xs('Adj Close', axis=1, level=0, drop_level=True)
                        except: pass

                if not batch_data.empty:
                    all_data_list.append(batch_data)
                
                # Success - break retry loop
                break 
            except Exception as e:
                if attempt == 0:
                    time.sleep(5) # Wait 5s before retry
                else:
                    print(f"Failed batch {i} after retry: {e}")

        # Update Progress
        percent = int(((i + 1) / len(ticker_chunks)) * 100)
        my_bar.progress(percent, text=f"Downloading batch {i+1}/{len(ticker_chunks)}")
        
        # Mandatory Sleep
        time.sleep(sleep_time)

    my_bar.empty()
    
    if all_data_list:
        full_data = pd.concat(all_data_list, axis=1)
        return full_data.loc[:, ~full_data.columns.duplicated()]
    return pd.DataFrame()

# ---------------------------------------------------------
# 3. LOGIC & UI
# ---------------------------------------------------------
def calculate_breadth(data):
    if data.empty: return pd.Series()
    sma_200 = data.rolling(window=200).mean()
    valid_stocks = data.notna().sum(axis=1)
    # Require at least 50 stocks to calculate (prevent 0% spikes)
    valid_mask = valid_stocks >= 50 
    
    count_above = (data >= sma_200).sum(axis=1)
    breadth = (count_above / valid_stocks) * 100
    breadth[~valid_mask] = pd.NA
    return breadth.dropna()

st.title("⚡ Nifty 500 Market Breadth")

tickers = get_nifty500_tickers()
data = fetch_data_safe(tickers)
breadth = calculate_breadth(data)

if not breadth.empty:
    latest = breadth.iloc[-1]
    change = latest - breadth.iloc[-2]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Stocks > 200 SMA", f"{latest:.1f}%", f"{change:.1f}%")
    
    sentiment = "Neutral"
    if latest > 80: sentiment = "Overbought"
    elif latest < 20: sentiment = "Oversold"
    c2.metric("Sentiment", sentiment)
    c3.metric("Stocks Tracked", f"{data.shape[1]}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=breadth.index, y=breadth.values, fill='tozeroy', 
                             line=dict(color='#00f2ff', width=2), name='Breadth'))
    
    for l, c in [(90,'red'), (80,'orange'), (20,'green')]:
        fig.add_shape(type="line", x0=breadth.index.min(), x1=breadth.index.max(), y0=l, y1=l, 
                      line=dict(color=c, dash='dot'))
    
    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=500, margin=dict(t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Data load incomplete due to network limits. Please refresh the page.")

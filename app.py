import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import io
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Nifty 500 Market Breadth", layout="wide")
st.markdown("""<style>.stApp {background-color: #0e1117;} h1, h2, h3 {color: #f8fafc;}</style>""", unsafe_allow_html=True)

# --- CACHED FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_nifty500_tickers():
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        s = requests.get(url, headers=headers, timeout=5).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')))
        return [symbol + ".NS" for symbol in df['Symbol']]
    except:
        return ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS']

@st.cache_data(ttl=3600)
def fetch_data(tickers):
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    data = yf.download(tickers, start=start_date, progress=False, threads=True)
    if isinstance(data.columns, pd.MultiIndex):
        try:
            if 'Adj Close' in data.columns.get_level_values(0): data = data['Adj Close']
            elif 'Close' in data.columns.get_level_values(0): data = data['Close']
            else: data = data.xs('Adj Close', axis=1, level=0, drop_level=True)
        except: pass
    return data

def calculate_breadth(data):
    sma_200 = data.rolling(window=200).mean()
    valid_stocks = data.notna().sum(axis=1)
    valid_mask = valid_stocks >= (len(data.columns) * 0.3)
    count_above = (data >= sma_200).sum(axis=1)
    breadth = (count_above / valid_stocks) * 100
    breadth[~valid_mask] = pd.NA
    return breadth.dropna()

# --- APP LOGIC ---
st.title("⚡ Nifty 500 Market Breadth")

with st.spinner('Fetching data...'):
    tickers = get_nifty500_tickers()
    data = fetch_data(tickers)
    breadth = calculate_breadth(data)

if not breadth.empty:
    latest = breadth.iloc[-1]
    change = latest - breadth.iloc[-2]
    
    c1, c2 = st.columns(2)
    c1.metric("Stocks > 200 SMA", f"{latest:.1f}%", f"{change:.1f}%")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=breadth.index, y=breadth.values, fill='tozeroy', 
                             line=dict(color='#00f2ff'), name='Breadth'))
    for l, c in [(90,'red'),(80,'orange'),(20,'green')]:
        fig.add_shape(type="line", x0=breadth.index.min(), x1=breadth.index.max(), y0=l, y1=l, line=dict(color=c, dash='dot'))
    
    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=500)
    st.plotly_chart(fig, use_container_width=True)
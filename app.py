import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests
import io
import time

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="Nifty 500 Market Breadth", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0e1117; } 
    h1, h2, h3 { color: #f8fafc; }
    .stMetric { background-color: #1f2937; padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. GET ALL 500 TICKERS
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_nifty500_tickers():
    try:
        url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        s = requests.get(url, headers=headers, timeout=10).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')))
        tickers = [x + ".NS" for x in df['Symbol'] if "DUMMY" not in str(x).upper()]
        return tickers
    except Exception as e:
        st.error(f"Failed to fetch Nifty 500 list from NSE: {e}")
        return []

# ---------------------------------------------------------
# 3. HIGH-SPEED DATA DOWNLOADER
# ---------------------------------------------------------
def fetch_full_market_data(tickers):
    if not tickers:
        return pd.DataFrame()
        
    st.info(f"🚀 Starting download for all {len(tickers)} stocks. Please wait...")
    
    chunk_size = 100 
    chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    all_data = []
    progress_bar = st.progress(0, text="Initializing...")
    start_time = time.time()
    
    for i, chunk in enumerate(chunks):
        try:
            elapsed = time.time() - start_time
            progress_bar.progress((i) / len(chunks), text=f"Downloading Batch {i+1}/{len(chunks)} ({int(elapsed)}s elapsed)")
            
            # Download
            batch = yf.download(chunk, start="2015-01-01", progress=False, threads=True, timeout=20)
            
            # Clean Data
            if isinstance(batch.columns, pd.MultiIndex):
                if 'Adj Close' in batch.columns.get_level_values(0):
                    batch = batch['Adj Close']
                elif 'Close' in batch.columns.get_level_values(0):
                    batch = batch['Close']
                else:
                    batch = batch.xs(batch.columns.get_level_values(0)[0], axis=1, level=0, drop_level=True)
            
            batch = batch.dropna(axis=1, how='all')
            
            if not batch.empty:
                all_data.append(batch)
                
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Batch {i} failed: {e}")
            
    progress_bar.empty()
    
    if all_data:
        full_df = pd.concat(all_data, axis=1)
        full_df = full_df.loc[:, ~full_df.columns.duplicated()]
        return full_df
        
    return pd.DataFrame()

# ---------------------------------------------------------
# 4. MAIN APP LOGIC
# ---------------------------------------------------------
st.title("⚡ Nifty 500 Market Breadth")

tickers = get_nifty500_tickers()

if tickers:
    data = fetch_full_market_data(tickers)
    
    if not data.empty:
        with st.spinner("Calculating moving averages..."):
            sma_200 = data.rolling(window=200).mean()
            valid_stocks = data.notna().sum(axis=1)
            valid_mask = valid_stocks >= 100
            
            # --- CALCULATIONS ---
            count_above = (data >= sma_200).sum(axis=1)
            count_below = valid_stocks - count_above
            
            # Breadth Percentage
            breadth_pct = (count_above / valid_stocks) * 100
            breadth_pct[~valid_mask] = pd.NA
            
            # Clean up the counts for plotting
            count_above[~valid_mask] = pd.NA
            count_below[~valid_mask] = pd.NA
            
            # Create a combined DataFrame for easier handling
            df_final = pd.DataFrame({
                'Breadth %': breadth_pct,
                'Count Above': count_above,
                'Count Below': count_below
            }).dropna()

        if not df_final.empty:
            latest = df_final.iloc[-1]
            prev = df_final.iloc[-2] if len(df_final) > 1 else latest
            
            # --- METRICS ROW ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Stocks > 200 SMA (%)", f"{latest['Breadth %']:.1f}%", f"{latest['Breadth %'] - prev['Breadth %']:.1f}%")
            c2.metric("Count Above (Bullish)", f"{int(latest['Count Above'])}", f"{int(latest['Count Above'] - prev['Count Above'])}")
            c3.metric("Count Below (Bearish)", f"{int(latest['Count Below'])}", f"{int(latest['Count Below'] - prev['Count Below'])}", delta_color="inverse")
            
            sentiment = "Neutral"
            if latest['Breadth %'] > 80: sentiment = "Overbought"
            elif latest['Breadth %'] < 20: sentiment = "Oversold"
            c4.metric("Sentiment", sentiment)

            # --- CHART 1: BREADTH PERCENTAGE ---
            st.subheader("1. Breadth Percentage (Indicator)")
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=df_final.index, y=df_final['Breadth %'], fill='tozeroy', 
                                     line=dict(color='#00f2ff', width=1.5), name='Breadth %'))
            
            # Zones
            fig1.add_hrect(y0=0, y1=20, fillcolor="green", opacity=0.15, layer="below", line_width=0)
            fig1.add_hrect(y0=80, y1=100, fillcolor="red", opacity=0.15, layer="below", line_width=0)
            for l in [20, 50, 80]:
                fig1.add_shape(type="line", x0=df_final.index.min(), x1=df_final.index.max(), y0=l, y1=l, 
                              line=dict(color='gray', dash='dot', width=1), opacity=0.5)

            fig1.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400,
                xaxis=dict(rangeslider=dict(visible=False), type="date"),
                yaxis=dict(range=[0, 100], fixedrange=True, title="Percentage (%)"),
                margin=dict(t=10, b=10)
            )
            st.plotly_chart(fig1, use_container_width=True)

            # --- CHART 2: STACKED COUNT CHART ---
            st.subheader("2. Market Participation (Volume of Stocks)")
            fig2 = go.Figure()

            # Stacked Area: Green (Above)
            fig2.add_trace(go.Scatter(
                x=df_final.index, y=df_final['Count Above'],
                mode='lines',
                name='Above 200 SMA',
                stackgroup='one', # This creates the stack
                line=dict(width=0),
                fillcolor='rgba(34, 197, 94, 0.6)' # Green
            ))

            # Stacked Area: Red (Below)
            fig2.add_trace(go.Scatter(
                x=df_final.index, y=df_final['Count Below'],
                mode='lines',
                name='Below 200 SMA',
                stackgroup='one',
                line=dict(width=0),
                fillcolor='rgba(239, 68, 68, 0.6)' # Red
            ))

            fig2.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400,
                xaxis=dict(rangeslider=dict(visible=True), type="date"), # Scrollbar on the bottom chart
                yaxis=dict(title="Number of Stocks"),
                hovermode="x unified",
                margin=dict(t=10, b=0),
                legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
            )
            st.plotly_chart(fig2, use_container_width=True)
            
        else:
            st.error("Calculated data is empty.")
    else:
        st.error("No data downloaded.")
else:
    st.error("Could not fetch ticker list.")
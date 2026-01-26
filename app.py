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
            
            # Identify Excluded Stocks (Latest date has NaN SMA)
            # We look at the very last row of the SMA dataframe
            latest_sma_values = sma_200.iloc[-1]
            excluded_tickers = latest_sma_values[latest_sma_values.isna()].index.tolist()
            
            # Remove .NS for cleaner display
            excluded_clean = [x.replace('.NS', '') for x in excluded_tickers]
            
            # --- CALCULATIONS ---
            has_sma = sma_200.notna()
            
            count_above = (data > sma_200).astype(int)
            count_above = count_above.where(has_sma).sum(axis=1)
            
            count_below = (data <= sma_200).astype(int)
            count_below = count_below.where(has_sma).sum(axis=1)
            
            valid_total = count_above + count_below
            total_target = len(tickers)
            count_excluded = total_target - valid_total
            
            breadth_pct = (count_above / valid_total) * 100
            
            valid_mask = valid_total >= 100
            breadth_pct[~valid_mask] = pd.NA
            
            df_final = pd.DataFrame({
                'Breadth %': breadth_pct,
                'Count Above': count_above,
                'Count Below': count_below,
                'Excluded': count_excluded
            }).dropna()

        if not df_final.empty:
            latest = df_final.iloc[-1]
            prev = df_final.iloc[-2] if len(df_final) > 1 else latest
            
            # --- METRICS ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Stocks > 200 SMA (%)", f"{latest['Breadth %']:.1f}%", f"{latest['Breadth %'] - prev['Breadth %']:.1f}%")
            c2.metric("Count Above (Bullish)", f"{int(latest['Count Above'])}", f"{int(latest['Count Above'] - prev['Count Above'])}")
            c3.metric("Count Below (Bearish)", f"{int(latest['Count Below'])}", f"{int(latest['Count Below'] - prev['Count Below'])}", delta_color="inverse")
            c4.metric("Excluded (New IPOs)", f"{int(latest['Excluded'])}", help="Stocks with <200 days history")

            # --- CHART 1 ---
            st.subheader("1. Breadth Percentage (Indicator)")
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=df_final.index, y=df_final['Breadth %'], fill='tozeroy', 
                                     fillcolor='rgba(0, 242, 255, 0.2)',
                                     line=dict(color='#00f2ff', width=1.5), name='Breadth %'))
            
            # Bands: Green (0-20), Red (80-100)
            fig1.add_hrect(y0=0, y1=20, fillcolor="green", opacity=0.3, layer="below", line_width=0)
            fig1.add_hrect(y0=80, y1=100, fillcolor="red", opacity=0.3, layer="below", line_width=0)
            
            for l in [20, 50, 80]:
                fig1.add_shape(type="line", x0=df_final.index.min(), x1=df_final.index.max(), y0=l, y1=l, 
                              line=dict(color='gray', dash='dot', width=1), opacity=0.5)

            fig1.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=450,
                xaxis=dict(rangeslider=dict(visible=False), type="date"),
                yaxis=dict(range=[0, 100], fixedrange=True, title="Percentage (%)"), margin=dict(t=10, b=10))
            st.plotly_chart(fig1, use_container_width=True)

            # --- CHART 2 ---
            st.subheader("2. Market Participation")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df_final.index, y=df_final['Count Above'], mode='lines', name='Above 200 SMA', stackgroup='one', line=dict(width=0), fillcolor='rgba(34, 197, 94, 0.6)'))
            fig2.add_trace(go.Scatter(x=df_final.index, y=df_final['Count Below'], mode='lines', name='Below 200 SMA', stackgroup='one', line=dict(width=0), fillcolor='rgba(239, 68, 68, 0.6)'))
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400,
                xaxis=dict(rangeslider=dict(visible=True), type="date"), yaxis=dict(title="Number of Stocks"),
                hovermode="x unified", margin=dict(t=10, b=0), legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"))
            st.plotly_chart(fig2, use_container_width=True)
            
            # --- EXCLUDED LIST SECTION ---
            st.markdown("---")
            with st.expander(f"⚠️ View List of {len(excluded_clean)} Excluded Stocks (Insufficient Data / New IPOs)"):
                st.write("These stocks were found in the Nifty 500 list but do not have a valid 200-day Moving Average yet (usually because they listed less than 200 days ago).")
                
                # Format as a clean table
                # Split list into 4 columns for readability
                col_a, col_b, col_c, col_d = st.columns(4)
                
                # Distribute items across columns
                for idx, stock in enumerate(excluded_clean):
                    if idx % 4 == 0: col_a.write(f"• {stock}")
                    elif idx % 4 == 1: col_b.write(f"• {stock}")
                    elif idx % 4 == 2: col_c.write(f"• {stock}")
                    else: col_d.write(f"• {stock}")
            
        else:
            st.error("Calculated data is empty.")
    else:
        st.error("No data downloaded.")
else:
    st.error("Could not fetch ticker list.")
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import time
from datetime import datetime

# ---------------------------------------------------------
# PAGE CONFIG
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
# DYNAMIC NIFTY 500 TICKERS FROM NSE
# ---------------------------------------------------------
@st.cache_data(ttl=86400)  # refresh daily
def get_nifty500_tickers():
    url = "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
    try:
        df = pd.read_csv(url)
        # Flexible column detection
        symbol_col = None
        for col in df.columns:
            if 'symbol' in col.lower():
                symbol_col = col
                break
        
        if not symbol_col:
            st.error("Could not detect 'Symbol' column in NSE CSV. Format may have changed.")
            return []
        
        symbols = df[symbol_col].dropna().astype(str).str.strip().str.upper()
        # Filter obviously invalid entries
        symbols = symbols[symbols.str.len().between(3, 12) & symbols.str.isalnum()]
        
        tickers = [sym + ".NS" for sym in symbols]
        tickers = sorted(list(set(tickers)))
        
        st.success(f"Loaded {len(tickers)} Nifty 500 tickers from NSE")
        return tickers
    
    except Exception as e:
        st.error(f"Failed to fetch Nifty 500 list: {str(e)}")
        st.info("Using fallback minimal list – please try again later")
        # Very small fallback in case of complete failure
        fallback = ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "TCS.NS", "HINDUNILVR.NS"]
        return fallback

# ---------------------------------------------------------
# SAFE MARKET DATA DOWNLOADER (daily refresh)
# ---------------------------------------------------------
@st.cache_data(ttl=86400, show_spinner="Refreshing daily market data...")
def fetch_full_market_data(tickers):
    if not tickers:
        return pd.DataFrame()
    
    chunk_size = 12
    sleep_time = 3.0
    max_retries = 2
    
    n = len(tickers)
    st.info(f"Downloading {n} stocks safely (daily refresh mode)...")
    
    chunks = [tickers[i:i + chunk_size] for i in range(0, n, chunk_size)]
    all_data = []
    
    progress = st.progress(0.0)
    status = st.empty()
    
    start_time = time.time()
    
    for i, chunk in enumerate(chunks):
        for attempt in range(max_retries + 1):
            try:
                elapsed = int(time.time() - start_time)
                status.text(f"Batch {i+1}/{len(chunks)} (attempt {attempt+1}) – {elapsed}s elapsed")
                
                batch = yf.download(
                    chunk,
                    start="2020-01-01",
                    progress=False,
                    threads=False,
                    timeout=30,
                    auto_adjust=True,
                    repair=True
                )
                
                if batch.empty:
                    break
                
                # Robust close price extraction
                if isinstance(batch.columns, pd.MultiIndex):
                    if 'Close' in batch.columns.get_level_values(0):
                        batch = batch['Close']
                    elif 'Close' in batch.columns.get_level_values(1):
                        batch = batch.xs('Close', level=1, axis=1)
                    else:
                        batch = batch.iloc[:, :len(chunk)]
                        batch.columns = chunk[:len(batch.columns)]
                elif len(chunk) == 1:
                    batch.columns = chunk
                
                batch = batch.dropna(axis=1, how='all')
                
                if not batch.empty:
                    all_data.append(batch)
                
                break  # success
                
            except Exception as e:
                if attempt == max_retries:
                    st.warning(f"Batch {i+1} failed after {max_retries+1} attempts: {str(e)}")
                time.sleep(5 * (attempt + 1))
        
        progress.progress((i + 1) / len(chunks))
        time.sleep(sleep_time)
    
    status.empty()
    progress.empty()
    
    if not all_data:
        st.error("No usable price data downloaded.")
        return pd.DataFrame()
    
    df = pd.concat(all_data, axis=1)
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.dropna(how='all', axis=0)
    
    return df

# ---------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------
st.title("⚡ Nifty 500 Market Breadth Dashboard")

# Force refresh button
if st.button("🔄 Force Full Refresh (Tickers + Data)", type="primary"):
    st.cache_data.clear()
    st.rerun()

tickers = get_nifty500_tickers()

if not tickers:
    st.stop()

data = fetch_full_market_data(tickers)

if data.empty:
    st.error("No price data available. Try force refresh or check later.")
    st.stop()

# Calculate metrics
with st.spinner("Calculating breadth indicators..."):
    # Use min_periods=100 to allow newer stocks to contribute partially
    sma_200 = data.rolling(window=200, min_periods=100).mean()
    
    latest_close = data.iloc[-1]
    latest_sma = sma_200.iloc[-1]
    
    valid = latest_close.notna() & latest_sma.notna()
    
    above = (latest_close > latest_sma) & valid
    below = (~above) & valid
    
    count_above = above.sum()
    count_below = below.sum()
    count_valid = count_above + count_below
    excluded_count = len(tickers) - count_valid
    
    excluded_stocks = data.columns[~valid].str.replace('.NS$', '', regex=True).tolist()
    
    # Time series
    has_sma = sma_200.notna()
    count_above_ts = (data > sma_200).where(has_sma).sum(axis=1)
    count_below_ts = (data <= sma_200).where(has_sma).sum(axis=1)
    
    valid_count_ts = count_above_ts + count_below_ts
    breadth_pct_ts = (count_above_ts / valid_count_ts * 100).where(valid_count_ts >= 100)
    
    df_chart = pd.DataFrame({
        'Date': data.index,
        'Breadth %': breadth_pct_ts,
        'Above': count_above_ts,
        'Below': count_below_ts
    }).dropna(subset=['Breadth %'])

# Display results
if not df_chart.empty:
    latest = df_chart.iloc[-1]
    prev = df_chart.iloc[-2] if len(df_chart) > 1 else latest
    
    cols = st.columns(4)
    cols[0].metric(
        "Above 200 SMA (%)",
        f"{latest['Breadth %']:.1f}%",
        f"{latest['Breadth %'] - prev['Breadth %']:.1f}%"
    )
    cols[1].metric(
        "Count Above",
        f"{int(latest['Above']):,}",
        f"{int(latest['Above'] - prev['Above']):+}"
    )
    cols[2].metric(
        "Count Below",
        f"{int(latest['Below']):,}",
        f"{int(latest['Below'] - prev['Below']):+}",
        delta_color="inverse"
    )
    cols[3].metric(
        "Excluded (no 200 SMA)",
        f"{excluded_count} / {len(tickers)}"
    )
    
    # Chart 1: Breadth %
    st.subheader("Market Breadth (% stocks > 200-day SMA)")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=df_chart['Date'], y=df_chart['Breadth %'],
        fill='tozeroy', fillcolor='rgba(0, 242, 255, 0.2)',
        line=dict(color='#00f2ff', width=2),
        name='Breadth %'
    ))
    
    fig1.add_hrect(0, 20, fillcolor="green", opacity=0.25, line_width=0)
    fig1.add_hrect(80, 100, fillcolor="red", opacity=0.25, line_width=0)
    
    for lvl in [20, 50, 80]:
        fig1.add_hline(y=lvl, line_dash="dot", line_color="gray", opacity=0.6)
    
    fig1.update_layout(
        template="plotly_dark", height=480,
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(range=[0, 100], title="%"),
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Chart 2: Stacked counts
    st.subheader("Participation (Above vs Below 200 SMA)")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_chart['Date'], y=df_chart['Above'],
        name="Above", stackgroup='one',
        fillcolor='rgba(34,197,94,0.5)', line_width=0
    ))
    fig2.add_trace(go.Scatter(
        x=df_chart['Date'], y=df_chart['Below'],
        name="Below", stackgroup='one',
        fillcolor='rgba(239,68,68,0.5)', line_width=0
    ))
    
    fig2.update_layout(
        template="plotly_dark", height=420,
        margin=dict(l=10, r=10, t=30, b=0),
        yaxis_title="Number of Stocks",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Excluded list
    if excluded_stocks:
        with st.expander(f"Excluded stocks ({len(excluded_stocks)}) – usually recent listings"):
            st.write(", ".join(sorted(excluded_stocks)))
    
    # Footer
    last_date = data.index[-1].strftime("%Y-%m-%d")
    refresh_time = datetime.now().strftime("%Y-%m-%d %H:%M IST")
    st.caption(f"Data as of {last_date} • Last refresh: {refresh_time} • Source: Yahoo Finance + NSE")
    
else:
    st.warning("Not enough historical data to compute breadth after cleaning.")
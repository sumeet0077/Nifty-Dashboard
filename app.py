import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import time
import numpy as np

# ---------------------------------------------------------
# PAGE CONFIGURATION
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
# TICKER LIST (manually maintained – update periodically)
# ---------------------------------------------------------
@st.cache_data(ttl=86400)  # 24 hours
def get_nifty500_tickers():
    tickers = [
        "360ONE.NS", "3MINDIA.NS", "ABB.NS", "ACC.NS", "AIAENG.NS", "APLAPOLLO.NS", "AUBANK.NS", "AARTIIND.NS", 
        "AAVAS.NS", "ABBOTINDIA.NS", "ADANIENSOL.NS", "ADANIENT.NS", "ADANIGREEN.NS", "ADANIPORTS.NS", "ADANIPOWER.NS", 
        "ATGL.NS", "AWL.NS", "ABCAPITAL.NS", "ABFRL.NS", "ABSLAMC.NS", "ETHERMOT.NS", "AFFLE.NS", "AJANTPHARM.NS", 
        "APLLTD.NS", "ALKEM.NS", "ALKYLAMINE.NS", "ALLCARGO.NS", "ALOKINDS.NS", "ARE&M.NS", "AMBER.NS", "AMBUJACEM.NS", 
        "ANANDRATHI.NS", "ANGELONE.NS", "ANURAS.NS", "APARINDS.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "APTUS.NS", 
        "ACI.NS", "ASAHIINDIA.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTERDM.NS", "ASTRAZEN.NS", "ASTRAL.NS", "ATUL.NS", 
        "AUROPHARMA.NS", "AVANTIFEED.NS", "DMART.NS", "AXISBANK.NS", "BASF.NS", "BSE.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", 
        "BAJAJFINSV.NS", "BAJAJHLDNG.NS", "BALAMINES.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", 
        "BANKBARODA.NS", "BANKINDIA.NS", "MAHABANK.NS", "BATAINDIA.NS", "BAYERCROP.NS", "BERGEPAINT.NS", "BDL.NS", 
        "BEL.NS", "BHARATFORG.NS", "BHEL.NS", "BPCL.NS", "BHARTIARTL.NS", "BIKAJI.NS", "BIOCON.NS", "BIRLACORPN.NS", 
        "BSOFT.NS", "BLS.NS", "BLUESTARCO.NS", "BORORENEW.NS", "BOSCHLTD.NS", "BRIGADE.NS", "BCG.NS", "BRITANNIA.NS", 
        "MAPMYINDIA.NS", "CCL.NS", "CESC.NS", "CGPOWER.NS", "CIEINDIA.NS", "CRISIL.NS", "CSBBANK.NS", "CAMPUS.NS", 
        "CANFINHOME.NS", "CANBK.NS", "CAPLIPOINT.NS", "CGCL.NS", "CARBORUNIV.NS", "CASTROLIND.NS", "CEATLTD.NS", 
        "CENTRALBK.NS", "CDSL.NS", "CENTURYPLY.NS", "CERA.NS", "CHALET.NS", "CHAMBLFERT.NS", "CHEMPLASTS.NS", 
        "CHOLAHLDNG.NS", "CHOLAFIN.NS", "CIPLA.NS", "CUB.NS", "CLEAN.NS", "COALINDIA.NS", "COCHINSHIP.NS", "COFORGE.NS", 
        "COLPAL.NS", "CAMS.NS", "CONCOR.NS", "COROMANDEL.NS", "CRAFTSMAN.NS", "CREDITACC.NS", "CROMPTON.NS", 
        "CUMMINSIND.NS", "CYIENT.NS", "DCMSHRIRAM.NS", "DLF.NS", "DABUR.NS", "DALBHARAT.NS", "DATAPATTNS.NS", 
        "DEEPAKFERT.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "DEVYANI.NS", "DIVISLAB.NS", "DIXON.NS", "LALPATHLAB.NS", 
        "DRREDDY.NS", "EIDPARRY.NS", "EIHOTEL.NS", "EPL.NS", "EASEMYTRIP.NS", "EICHERMOT.NS", "ELECON.NS", "ELGIEQUIP.NS", 
        "EMAMILTD.NS", "ENDURANCE.NS", "EQUITASBNK.NS", "ERIS.NS", "ESCORTS.NS", "EXIDEIND.NS", "FDC.NS", "NYKAA.NS", 
        "FEDERALBNK.NS", "FACT.NS", "FINEORG.NS", "FINCABLES.NS", "FINPIPE.NS", "FSL.NS", "FORTIS.NS", "GRINFRA.NS", 
        "GAIL.NS", "GMMPFAUDLR.NS", "GMRAIRPORT.NS", "GALAXYSURF.NS", "GARFIBRES.NS", "GATEWAY.NS", "GENUSPOWER.NS", 
        "GESHIP.NS", "GICRE.NS", "GILLETTE.NS", "GLAND.NS", "GLAXO.NS", "GLENMARK.NS", "MEDANTA.NS", "GOCOLORS.NS", 
        "GODFRYPHLP.NS", "GODREJAGRO.NS", "GODREJCP.NS", "GODREJIND.NS", "GODREJPROP.NS", "GPPL.NS", "GRANULES.NS", 
        "GRAPHITE.NS", "GRASIM.NS", "GRINDWELL.NS", "GUJALKALI.NS", "GAEL.NS", "FLUOROCHEM.NS", "GUJGASLTD.NS", 
        "GMDCLTD.NS", "GNFC.NS", "GPIL.NS", "GSFC.NS", "GSPL.NS", "HEG.NS", "HBLPOWER.NS", "HCLTECH.NS", "HDFCAMC.NS", 
        "HDFCBANK.NS", "HDFCLIFE.NS", "HFCL.NS", "HLEGLAS.NS", "HAPPSTMNDS.NS", "HATHWAY.NS", "HATSUN.NS", "HAVELLS.NS", 
        "HEMIPROP.NS", "HEROMOTOCO.NS", "HIKAL.NS", "HIMATSEIDE.NS", "HINDALCO.NS", "HAL.NS", "HINDCOPPER.NS", 
        "HINDPETRO.NS", "HINDUNILVR.NS", "HINDZINC.NS", "HOMEFIRST.NS", "HONAUT.NS", "HUDCO.NS", "ICICIBANK.NS", 
        "ICICIGI.NS", "ICICIPRULI.NS", "IDBI.NS", "IDFCFIRSTB.NS", "IFBIND.NS", "IIFL.NS", "IRB.NS", "IRCON.NS", "ITC.NS", 
        "ITI.NS", "INDIACEM.NS", "INDIAMART.NS", "INDIANB.NS", "IEX.NS", "INDHOTEL.NS", "IOC.NS", "IOB.NS", "IRCTC.NS", 
        "IRFC.NS", "INDIGOPNTS.NS", "IGL.NS", "INDUSTOWER.NS", "INDUSINDBK.NS", "INFIBEAM.NS", "NAUKRI.NS", "INFY.NS", 
        "INGERRAND.NS", "INTELLECT.NS", "INDIGO.NS", "IPCALAB.NS", "JBCHEPHARM.NS", "JKCEMENT.NS", "JKLAKSHMI.NS", 
        "JKPAPER.NS", "JKTYRE.NS", "JMFINANCIL.NS", "JSWENERGY.NS", "JSWINFRA.NS", "JSWSTEEL.NS", "JAICORPLTD.NS", 
        "J&KBANK.NS", "JINDALSAW.NS", "JSL.NS", "JINDALSTEL.NS", "JIOFIN.NS", "JUBLFOOD.NS", "JUBLINGREA.NS", 
        "JUBLPHARMA.NS", "JUSTDIAL.NS", "JYOTHYLAB.NS", "KPRMILL.NS", "KEI.NS", "KNRCON.NS", "KPITTECH.NS", "KRBL.NS", 
        "KSB.NS", "KAJARIACER.NS", "KPIL.NS", "KALYANKJIL.NS", "KANSAINER.NS", "KARURVYSYA.NS", "KEC.NS", "KIRLOSENG.NS", 
        "KIRLOSBROS.NS", "KFINTECH.NS", "KOTAKBANK.NS", "KIMS.NS", "LTF.NS", "LT.NS", "LTTS.NS", "LICHSGFIN.NS", 
        "LTIM.NS", "LAOPALA.NS", "LATENTVIEW.NS", "LAURUSLABS.NS", "LXCHEM.NS", "LEMONTREE.NS", "LICI.NS", 
        "LINDEINDIA.NS", "LUPIN.NS", "MMTC.NS", "MOIL.NS", "MRF.NS", "MTARTECH.NS", "LODHA.NS", "MGL.NS", "M&MFIN.NS", 
        "M&M.NS", "MHRIL.NS", "MAHLIFE.NS", "MANAPPURAM.NS", "MRPL.NS", "MANKIND.NS", "MARICO.NS", "MARUTI.NS", 
        "MASTEK.NS", "MFSL.NS", "MAXHEALTH.NS", "MAZDOCK.NS", "MEDPLUS.NS", "METROBRAND.NS", "METROPOLIS.NS", 
        "MINDACORP.NS", "MSUMI.NS", "MOTILALOFS.NS", "MPHASIS.NS", "MCX.NS", "MUTHOOTFIN.NS", "NATCOPHARM.NS", 
        "NBCC.NS", "NCC.NS", "NHPC.NS", "NLCINDIA.NS", "NMDC.NS", "NSLNISP.NS", "NOCIL.NS", "NTPC.NS", "NH.NS", 
        "NATIONALUM.NS", "NAVINFLUOR.NS", "NAZARA.NS", "NESTLEIND.NS", "NETWORK18.NS", "NAM-INDIA.NS", "NUVAMA.NS", 
        "NUVOCO.NS", "OBEROIRLTY.NS", "ONGC.NS", "OIL.NS", "OLECTRA.NS", "PAYTM.NS", "OFSS.NS", "ORIENTELEC.NS", 
        "POLICYBZR.NS", "PCBL.NS", "PIIND.NS", "PNBHOUSING.NS", "PNCINFRA.NS", "PVRINOX.NS", "PAGEIND.NS", 
        "PATANJALI.NS", "PERSISTENT.NS", "PETRONET.NS", "PHOENIXLTD.NS", "PIDILITIND.NS", "PPLPHARMA.NS", 
        "POLYMED.NS", "POLYCAB.NS", "POONAWALLA.NS", "PFC.NS", "POWERGRID.NS", "PRAJIND.NS", "PRESTIGE.NS", 
        "PRINCEPIPE.NS", "PGHH.NS", "PNB.NS", "QUESS.NS", "RRKABEL.NS", "RBLBANK.NS", "RECLTD.NS", "RHIM.NS", 
        "RITES.NS", "RADICO.NS", "RVNL.NS", "RAILTEL.NS", "RAIN.NS", "RAINBOW.NS", "RAJESHEXPO.NS", "RALLIS.NS", 
        "RCF.NS", "RATNAMANI.NS", "RTNINDIA.NS", "RAYMOND.NS", "REDINGTON.NS", "RELIANCE.NS", "RBA.NS", "ROSSARI.NS", 
        "ROUTE.NS", "SBFC.NS", "SBICARD.NS", "SBILIFE.NS", "SJVN.NS", "SKFINDIA.NS", "SRF.NS", "SAFARI.NS", 
        "MOTHERSON.NS", "SANOFI.NS", "SAPPHIRE.NS", "SAREGAMA.NS", "SCHAEFFLER.NS", "SCHNEIDER.NS", "SEQUENT.NS", 
        "SHARDACROP.NS", "SFL.NS", "SHILPAMED.NS", "SCI.NS", "RENUKA.NS", "SHRIRAMFIN.NS", "SHYAMMETL.NS", "SIEMENS.NS", 
        "SOBHA.NS", "SOLARINDS.NS", "SONACOMS.NS", "SONATSOFTW.NS", "SOUTHBANK.NS", "SPANDANA.NS", "SPARC.NS", 
        "STARHEALTH.NS", "SBIN.NS", "SAIL.NS", "SWSOLAR.NS", "STLTECH.NS", "STAR.NS", "SUDARSCHEM.NS", "SUMICHEM.NS", 
        "SUNPHARMA.NS", "SUNTV.NS", "SUNDARMFIN.NS", "SUNDRMFAST.NS", "SUNTECK.NS", "SUPRAJIT.NS", "SUPREMEIND.NS", 
        "SUZLON.NS", "SYMPHONY.NS", "SYRMA.NS", "TVSMOTOR.NS", "TANLA.NS", "TATACHEM.NS", "TATACOMM.NS", "TCS.NS", 
        "TATACONSUM.NS", "TATAELXSI.NS", "TATAINVEST.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", 
        "TATATECH.NS", "TTML.NS", "TEAMLEASE.NS", "TECHM.NS", "TEJASNET.NS", "NIACL.NS", "RAMCOCEM.NS", "THERMAX.NS", 
        "TIMKEN.NS", "TITAN.NS", "TORNTPHARM.NS", "TORNTPOWER.NS", "TRENT.NS", "TRIDENT.NS", "TRIVENI.NS", 
        "TRITURBINE.NS", "TIINDIA.NS", "UCOBANK.NS", "UNOMINDA.NS", "UPL.NS", "UTIAMC.NS", "UJJIVANSFB.NS", 
        "ULTRACEMCO.NS", "UNIONBANK.NS", "UBL.NS", "UNISPIRITS.NS", "VGUARD.NS", "VIPIND.NS", "VAIBHAVGBL.NS", 
        "VAKRANGEE.NS", "VARROC.NS", "VBL.NS", "VEDL.NS", "MANYAVAR.NS", "VIJAYA.NS", "VINATIORGA.NS", "IDEA.NS", 
        "VOLTAS.NS", "WELCORP.NS", "WELSPUNLIV.NS", "WESTLIFE.NS", "WHIRLPOOL.NS", "WIPRO.NS", "WOCKPHARMA.NS", 
        "YESBANK.NS", "ZFCVINDIA.NS", "ZEEL.NS", "ZENSARTECH.NS", "ZOMATO.NS", "ZYDUSLIFE.NS", "ZYDUSWELL.NS", "ECLERX.NS"
        # Add newly included stocks from 2024–2026 here (check NSE monthly)
    ]
    return sorted(list(set(tickers)))   # remove accidental duplicates

# ---------------------------------------------------------
# IMPROVED SAFE DOWNLOADER
# ---------------------------------------------------------
def fetch_full_market_data(tickers):
    if not tickers:
        return pd.DataFrame()
    
    chunk_size = 12          # smaller = safer in 2026
    sleep_time = 3.0         # increased
    max_retries_per_chunk = 2
    
    n = len(tickers)
    st.info(f"Downloading {n} Nifty 500 stocks in safe mode (~4–7 min)...")
    
    chunks = [tickers[i:i + chunk_size] for i in range(0, n, chunk_size)]
    all_data = []
    
    progress = st.progress(0.0)
    status_text = st.empty()
    
    for i, chunk in enumerate(chunks):
        for attempt in range(max_retries_per_chunk + 1):
            try:
                status_text.text(f"Batch {i+1}/{len(chunks)} (attempt {attempt+1}) – {int(time.time() - time_start):,}s elapsed")
                
                batch = yf.download(
                    chunk,
                    start="2020-01-01",      # ← shorter history = much more reliable
                    progress=False,
                    threads=False,
                    timeout=30,
                    auto_adjust=True,
                    repair=True              # tries to fix some broken responses
                )
                
                # Robust column extraction
                if batch.empty:
                    break
                
                if isinstance(batch.columns, pd.MultiIndex):
                    if 'Close' in batch.columns.get_level_values(0):
                        batch = batch['Close']
                    elif 'Close' in batch.columns.get_level_values(1):
                        batch = batch.xs('Close', axis=1, level=1, drop_level=True)
                    else:
                        # fallback – take first level if only one ticker or broken
                        batch = batch.iloc[:, :len(chunk)]
                        batch.columns = chunk[:len(batch.columns)]
                else:
                    # single ticker case
                    if len(chunk) == 1:
                        batch.columns = chunk
                
                # Drop completely empty columns
                batch = batch.dropna(axis=1, how='all')
                
                if not batch.empty:
                    all_data.append(batch)
                
                break  # success → next chunk
                
            except Exception as e:
                if attempt < max_retries_per_chunk:
                    time.sleep(5 * (attempt + 1))
                else:
                    st.warning(f"Batch {i+1} failed after retries: {e}")
        
        progress.progress((i + 1) / len(chunks))
        time.sleep(sleep_time)
    
    status_text.empty()
    progress.empty()
    
    if not all_data:
        return pd.DataFrame()
    
    df = pd.concat(all_data, axis=1)
    # Final cleanup
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.dropna(how='all', axis=0)   # remove fully empty rows
    
    return df

# ---------------------------------------------------------
# MAIN LOGIC
# ---------------------------------------------------------
st.title("⚡ Nifty 500 Market Breadth Dashboard")

tickers = get_nifty500_tickers()

if not tickers:
    st.error("Ticker list empty.")
    st.stop()

data = fetch_full_market_data(tickers)

if data.empty:
    st.error("Failed to download any usable data. Try again later — Yahoo is very strict in 2026.")
    st.stop()

with st.spinner("Computing breadth indicators..."):
    sma_200 = data.rolling(window=200, min_periods=100).mean()   # allow partial on newer stocks
    
    # Latest complete day
    latest_close = data.iloc[-1]
    latest_sma   = sma_200.iloc[-1]
    
    valid_mask = latest_sma.notna() & latest_close.notna()
    
    above = (latest_close > latest_sma) & valid_mask
    below = (latest_close <= latest_sma) & valid_mask
    
    count_above_now = above.sum()
    count_below_now = below.sum()
    count_valid_now = count_above_now + count_below_now
    count_excluded  = len(tickers) - count_valid_now
    
    excluded_tickers = data.columns[~valid_mask].str.replace('.NS$', '', regex=True).tolist()
    
    # Time series for chart
    has_sma = sma_200.notna()
    count_above_ts = (data > sma_200).where(has_sma).sum(axis=1)
    count_below_ts = (data <= sma_200).where(has_sma).sum(axis=1)
    
    breadth_pct_ts = (count_above_ts / (count_above_ts + count_below_ts) * 100).where((count_above_ts + count_below_ts) >= 100)
    
    df_chart = pd.DataFrame({
        'Date': data.index,
        'Breadth %': breadth_pct_ts,
        'Above': count_above_ts,
        'Below': count_below_ts
    }).dropna(subset=['Breadth %'])

# ────────────────────────────────────────────────
# METRICS
# ────────────────────────────────────────────────
if not df_chart.empty:
    latest = df_chart.iloc[-1]
    prev   = df_chart.iloc[-2] if len(df_chart) > 1 else latest
    
    cols = st.columns(4)
    cols[0].metric("Above 200 SMA (%)", f"{latest['Breadth %']:.1f}%", f"{latest['Breadth %']-prev['Breadth %']:.1f}%")
    cols[1].metric("Count Above", f"{int(latest['Above']):,}", f"{int(latest['Above']-prev['Above']):+}")
    cols[2].metric("Count Below", f"{int(latest['Below']):,}", f"{int(latest['Below']-prev['Below']):+}", delta_color="inverse")
    cols[3].metric("Excluded / No 200 SMA", f"{count_excluded} / {len(tickers)}")

    # Chart 1 – Breadth %
    st.subheader("Market Breadth (% stocks > 200 SMA)")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=df_chart['Date'], y=df_chart['Breadth %'],
        fill='tozeroy', fillcolor='rgba(0,242,255,0.15)',
        line=dict(color='#00f2ff', width=2),
        name='Breadth %'
    ))
    
    fig1.add_hrect(0, 20, fillcolor="green", opacity=0.25, line_width=0)
    fig1.add_hrect(80, 100, fillcolor="red", opacity=0.25, line_width=0)
    
    for level in [20, 50, 80]:
        fig1.add_hline(y=level, line_dash="dot", line_color="gray", opacity=0.6)
    
    fig1.update_layout(
        template="plotly_dark", height=480, margin=dict(l=10,r=10,t=30,b=10),
        yaxis=dict(range=[0,100], title="%"), xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Chart 2 – Stacked participation
    st.subheader("Participation (Above vs Below)")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_chart['Date'], y=df_chart['Above'],
                             name="Above", stackgroup='one',
                             fillcolor='rgba(34,197,94,0.5)', line_width=0))
    fig2.add_trace(go.Scatter(x=df_chart['Date'], y=df_chart['Below'],
                             name="Below", stackgroup='one',
                             fillcolor='rgba(239,68,68,0.5)', line_width=0))
    
    fig2.update_layout(
        template="plotly_dark", height=420, margin=dict(l=10,r=10,t=30,b=0),
        yaxis_title="Number of Stocks", hovermode="x unified",
        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Excluded list
    if excluded_tickers:
        with st.expander(f"Excluded stocks ({len(excluded_tickers)}) – usually recent listings / data issues"):
            st.write(", ".join(sorted(excluded_tickers)))
else:
    st.warning("Not enough data points to calculate breadth after cleaning.")

st.caption("Data: Yahoo Finance • 200-day SMA • Last update: " + str(data.index[-1].date()))
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
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
# 2. CLEANED & UPDATED TICKER LIST (No Dead Stocks)
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_nifty500_tickers():
    # This list has been manually cleaned of merged/delisted stocks causing errors
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
    ]
    return list(set(tickers))

# ---------------------------------------------------------
# 3. SAFE MODE DOWNLOADER (Slower but 100% Reliable)
# ---------------------------------------------------------
def fetch_full_market_data(tickers):
    if not tickers:
        return pd.DataFrame()
    
    # SAFE MODE CONFIGURATION
    chunk_size = 20    # Smaller batches to avoid Rate Limits
    sleep_time = 1.0   # Sleep 1s between batches
    
    st.info(f"🚀 Starting SAFE MODE download for {len(tickers)} stocks. This will take about 2-3 minutes...")
    
    chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    all_data = []
    
    progress_bar = st.progress(0, text="Initializing Safe Mode...")
    start_time = time.time()
    
    for i, chunk in enumerate(chunks):
        try:
            elapsed = int(time.time() - start_time)
            progress_bar.progress((i) / len(chunks), text=f"Processing Batch {i+1}/{len(chunks)} ({elapsed}s)")
            
            # SAFE DOWNLOAD: threads=False is key to stopping the 401 Errors
            # We retry once if a batch fails completely
            try:
                batch = yf.download(chunk, start="2015-01-01", progress=False, threads=False, timeout=20, auto_adjust=True)
            except Exception:
                time.sleep(5)
                batch = yf.download(chunk, start="2015-01-01", progress=False, threads=False, timeout=20, auto_adjust=True)
            
            # Clean Data Structure
            if isinstance(batch.columns, pd.MultiIndex):
                if 'Close' in batch.columns.get_level_values(0):
                    batch = batch['Close']
                elif 'Close' in batch.columns.get_level_values(1):
                    batch = batch.xs('Close', axis=1, level=1, drop_level=True)
                else:
                    batch = batch.iloc[:, :len(chunk)] 
            
            # Drop empty columns
            batch = batch.dropna(axis=1, how='all')
            
            if not batch.empty:
                all_data.append(batch)
            
            # Mandatory sleep to prevent Yahoo Blocking
            time.sleep(sleep_time)
            
        except Exception as e:
            print(f"Batch {i} skipped: {e}")
            
    progress_bar.empty()
    
    if all_data:
        full_df = pd.concat(all_data, axis=1)
        return full_df.loc[:, ~full_df.columns.duplicated()]
        
    return pd.DataFrame()

# ---------------------------------------------------------
# 4. MAIN APP LOGIC
# ---------------------------------------------------------
st.title("⚡ Nifty 500 Market Breadth")

tickers = get_nifty500_tickers()

if tickers:
    data = fetch_full_market_data(tickers)
    
    if not data.empty:
        with st.spinner("Calculating metrics..."):
            sma_200 = data.rolling(window=200).mean()
            
            latest_sma_values = sma_200.iloc[-1]
            excluded_tickers = latest_sma_values[latest_sma_values.isna()].index.tolist()
            excluded_clean = [x.replace('.NS', '') for x in excluded_tickers]
            
            has_sma = sma_200.notna()
            
            count_above = (data > sma_200).astype(int).where(has_sma).sum(axis=1)
            count_below = (data <= sma_200).astype(int).where(has_sma).sum(axis=1)
            
            valid_total = count_above + count_below
            total_target = len(tickers)
            count_excluded = total_target - valid_total
            
            breadth_pct = (count_above / valid_total) * 100
            breadth_pct[valid_total < 100] = pd.NA
            
            df_final = pd.DataFrame({
                'Breadth %': breadth_pct,
                'Count Above': count_above,
                'Count Below': count_below,
                'Excluded': count_excluded
            }).dropna()

        if not df_final.empty:
            latest = df_final.iloc[-1]
            prev = df_final.iloc[-2] if len(df_final) > 1 else latest
            
            # Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Stocks > 200 SMA (%)", f"{latest['Breadth %']:.1f}%", f"{latest['Breadth %'] - prev['Breadth %']:.1f}%")
            c2.metric("Count Above", f"{int(latest['Count Above'])}", f"{int(latest['Count Above'] - prev['Count Above'])}")
            c3.metric("Count Below", f"{int(latest['Count Below'])}", f"{int(latest['Count Below'] - prev['Count Below'])}", delta_color="inverse")
            c4.metric("Excluded (New/No Data)", f"{int(latest['Excluded'])}")

            # Chart 1
            st.subheader("1. Breadth Percentage")
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=df_final.index, y=df_final['Breadth %'], fill='tozeroy', 
                                     fillcolor='rgba(0, 242, 255, 0.2)',
                                     line=dict(color='#00f2ff', width=1.5), name='Breadth %'))
            
            fig1.add_hrect(y0=0, y1=20, fillcolor="green", opacity=0.3, layer="below", line_width=0)
            fig1.add_hrect(y0=80, y1=100, fillcolor="red", opacity=0.3, layer="below", line_width=0)
            
            for l in [20, 50, 80]:
                fig1.add_shape(type="line", x0=df_final.index.min(), x1=df_final.index.max(), y0=l, y1=l, 
                              line=dict(color='gray', dash='dot', width=1), opacity=0.5)

            fig1.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=450,
                xaxis=dict(rangeslider=dict(visible=False), type="date"),
                yaxis=dict(range=[0, 100], fixedrange=True, title="Percentage (%)"), margin=dict(t=10, b=10))
            
            st.plotly_chart(fig1)

            # Chart 2
            st.subheader("2. Market Participation")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df_final.index, y=df_final['Count Above'], mode='lines', name='Above 200 SMA', stackgroup='one', line=dict(width=0), fillcolor='rgba(34, 197, 94, 0.6)'))
            fig2.add_trace(go.Scatter(x=df_final.index, y=df_final['Count Below'], mode='lines', name='Below 200 SMA', stackgroup='one', line=dict(width=0), fillcolor='rgba(239, 68, 68, 0.6)'))
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400,
                xaxis=dict(rangeslider=dict(visible=True), type="date"), yaxis=dict(title="Number of Stocks"),
                hovermode="x unified", margin=dict(t=10, b=0), legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"))
            
            st.plotly_chart(fig2)
            
            # Excluded List
            st.markdown("---")
            with st.expander(f"⚠️ View List of {len(excluded_clean)} Excluded Stocks"):
                st.write("These stocks have insufficient data (New IPOs) or failed to download.")
                col_a, col_b, col_c, col_d = st.columns(4)
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
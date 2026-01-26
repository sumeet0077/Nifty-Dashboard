import pandas as pd
import yfinance as yf
import requests
import io
import time
from datetime import datetime, timedelta

def get_nifty500_tickers():
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        s = requests.get(url, headers=headers, timeout=10).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')))
        return [x + ".NS" for x in df['Symbol'] if "DUMMY" not in x]
    except:
        return ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS'] # Fallback

def fetch_and_calculate():
    tickers = get_nifty500_tickers()
    start_date = "2015-01-01"
    
    # Download in batches
    chunk_size = 50
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    all_data_list = []
    
    print(f"Downloading data for {len(tickers)} stocks...")
    
    for i, batch in enumerate(ticker_chunks):
        try:
            # Robust download
            batch_data = yf.download(batch, start=start_date, progress=False, threads=False, timeout=20)
            
            # Extract 'Adj Close'
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
                
            print(f"Batch {i+1}/{len(ticker_chunks)} done.")
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"Batch {i} failed: {e}")

    if not all_data_list:
        print("No data fetched.")
        return

    # Combine
    data = pd.concat(all_data_list, axis=1)
    data = data.loc[:, ~data.columns.duplicated()]
    
    # Calculate Breadth
    sma_200 = data.rolling(window=200).mean()
    valid_stocks = data.notna().sum(axis=1)
    valid_mask = valid_stocks >= 50
    
    count_above = (data >= sma_200).sum(axis=1)
    breadth = (count_above / valid_stocks) * 100
    breadth[~valid_mask] = pd.NA
    
    # Save to CSV
    df_final = pd.DataFrame(breadth.dropna(), columns=['Breadth'])
    df_final.index.name = 'Date'
    df_final.to_csv("market_breadth.csv")
    print("market_breadth.csv saved successfully.")

if __name__ == "__main__":
    fetch_and_calculate()
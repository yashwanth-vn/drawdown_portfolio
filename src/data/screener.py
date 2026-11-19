import requests
import pandas as pd
import yfinance as yf
from typing import List, Dict

class AssetScreener:
    """
    Fetches live asset lists from Yahoo Finance Screener endpoints.
    Minimizes dependency on static lists by querying 'most active' or sector-based scanners.
    """
    
    # Pre-defined fallback lists to ensure UI never shows empty
    FALLBACK_ASSETS = {
        'equity': ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "JPM", "V"],
        'etf': ["SPY", "IVV", "VOO", "QQQ", "IWM", "EFA", "VEA", "VWO", "AGG", "GLD"],
        'crypto': ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD"],
        'forex': ["EURUSD=X", "JPY=X", "GBPUSD=X", "AUDUSD=X", "NZDUSD=X", "EURJPY=X", "GBPJPY=X"],
        'commodity': ["GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "ZC=F", "ZW=F", "ZS=F"],
        'index': ["^GSPC", "^DJI", "^IXIC", "^RUT", "^FTSE", "^N225", "^HSI"],
        'fixed_income': ["TLT", "IEF", "SHY", "LQD", "HYG", "JNK", "BND"]
    }

    @staticmethod
    def fetch_assets(asset_type: str) -> List[Dict[str, str]]:
        """
        Fetch top assets for a given type.
        Returns list of dicts: {'symbol': 'AAPL', 'name': 'Apple Inc.'}
        """
        results = []
        try:
            # 1. Try Live Screener First
            if asset_type == 'crypto':
                results = AssetScreener._query_screener("day_gainers", count=100, scrIds="all_cryptocurrencies_us")
            elif asset_type == 'etf':
                results = AssetScreener._query_screener("top_etfs_us", count=100)
            elif asset_type == 'index':
                results = AssetScreener._get_major_indices()
            elif asset_type == 'forex':
                results = AssetScreener._query_screener("all_currencies_us", count=100)
            elif asset_type == 'commodity':
                results = AssetScreener._get_commodities()
            elif asset_type == 'fixed_income':
                 # Yahoo doesn't have a simple public "top fixed income" screener ID easily accessible
                 # We rely on fallback or specific ETF query if possible (using ETFs for fixed income usually)
                 results = [] 
            else: # Equity default
                results = AssetScreener._query_most_active_equities()
                
            # 2. Check if valid
            if results and len(results) > 5:
                return results
                
        except Exception as e:
            print(f"Screener Error ({asset_type}): {e}")
            
        # 3. Fallback if empty or failed
        print(f"Using fallback assets for {asset_type}")
        return AssetScreener._get_fallback(asset_type)

    @staticmethod
    def _query_most_active_equities():
        # "day_gainers" is okay, but "most_actives" is better for liquidity
        return AssetScreener._query_screener("day_gainers", count=100)

    @staticmethod
    def _query_screener(scrId: str, count: int = 50, scrIds: str = None) -> List[Dict]:
        """
        Hit Yahoo Finance Screener API.
        """
        params = {
            "count": count,
            "scrIds": scrIds or scrId
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved/screener/{scrId}"
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            data = resp.json()
            
            quotes = data.get('finance', {}).get('result', [])[0].get('quotes', [])
            return [{'symbol': q['symbol'], 'name': q.get('shortName', q['symbol'])} for q in quotes]
            
        except Exception:
            return []

    @staticmethod
    def _get_major_indices():
         # Manual list but validated structure
         symbols = [
             {"symbol": "^GSPC", "name": "S&P 500"},
             {"symbol": "^DJI", "name": "Dow Jones Industrial Average"},
             {"symbol": "^IXIC", "name": "NASDAQ Composite"},
             {"symbol": "^RUT", "name": "Russell 2000"},
             {"symbol": "^FTSE", "name": "FTSE 100"},
             {"symbol": "^N225", "name": "Nikkei 225"},
             {"symbol": "^HSI", "name": "Hang Seng Index"}
         ]
         return symbols

    @staticmethod
    def _get_commodities():
         symbols = [
             {"symbol": "GC=F", "name": "Gold"},
             {"symbol": "SI=F", "name": "Silver"},
             {"symbol": "CL=F", "name": "Crude Oil"},
             {"symbol": "NG=F", "name": "Natural Gas"},
             {"symbol": "HG=F", "name": "Copper"},
             {"symbol": "ZC=F", "name": "Corn"},
             {"symbol": "ZW=F", "name": "Wheat"},
             {"symbol": "ZS=F", "name": "Soybean"}
         ]
         return symbols

    @staticmethod
    def _get_fallback(asset_type: str) -> List[Dict]:
        tickers = AssetScreener.FALLBACK_ASSETS.get(asset_type, AssetScreener.FALLBACK_ASSETS['equity'])
        # Return simple dicts
        return [{'symbol': t, 'name': t} for t in tickers]

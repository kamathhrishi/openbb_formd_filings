# Import required libraries
import json
import os
import requests
from datetime import datetime
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Initialize FastAPI application
app = FastAPI(
    title="S&P 500 Data Hub",
    description="Simple S&P 500 chart widget",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "Info": "S&P 500 Data Hub",
        "status": "running",
        "symbol": "^GSPC (S&P 500)",
        "data_source": "yfinance + fallbacks"
    }

@app.get("/widgets.json")
def get_widgets():
    """S&P 500 widget configuration"""
    widgets_config = {
        "sp500_1y": {
            "name": "S&P 500 Chart",
            "description": "S&P 500 index 1-year historical data with volume",
            "category": "Market Data",
            "type": "chart",
            "endpoint": "sp500_1y",
            "gridData": {"w": 1200, "h": 600},
            "source": "Yahoo Finance"
        }
    }
    
    return JSONResponse(content=widgets_config)

@app.get("/apps.json")
def get_apps():
    """Simple app with S&P 500 widget"""
    apps_config = [
        {
            "name": "S&P 500 Dashboard",
            "img": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=250&h=200&fit=crop",
            "img_dark": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=250&h=200&fit=crop",
            "img_light": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=250&h=200&fit=crop",
            "description": "S&P 500 index chart showing 1 year of market data",
            "allowCustomization": True,
            "tabs": {
                "main": {
                    "id": "main",
                    "name": "S&P 500",
                    "layout": [
                        {"i": "sp500_1y", "x": 0, "y": 0, "w": 40, "h": 20}
                    ]
                }
            },
            "groups": []
        }
    ]
    
    return JSONResponse(content=apps_config)

@app.get("/sp500_1y")
def get_sp500_1y():
    """Get S&P 500 1-year data"""
    try:
        print("=== Fetching S&P 500 Data ===")
        
        data_source = "Sample Data"
        hist = None
        
        # Try multiple S&P 500 symbols
        sp500_symbols = ["^GSPC", "SPY", "VOO"]  # S&P 500 Index, SPDR ETF, Vanguard ETF
        
        for symbol in sp500_symbols:
            try:
                print(f"Trying {symbol}...")
                
                # Create custom session
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                })
                
                # Try yfinance with session
                ticker = yf.Ticker(symbol, session=session)
                hist = ticker.history(period="1y", interval="1d", timeout=15, threads=False)
                
                if not hist.empty and len(hist) > 50:
                    print(f"✅ SUCCESS with {symbol}! Got {len(hist)} rows of real data")
                    data_source = f"Yahoo Finance ({symbol})"
                    break
                else:
                    print(f"{symbol} returned {len(hist) if hist is not None else 0} rows")
                    
            except Exception as symbol_error:
                print(f"{symbol} failed: {symbol_error}")
                continue
        
        # If all symbols failed, create sample data
        if hist is None or hist.empty:
            print("All S&P 500 symbols failed, creating realistic sample data")
            
            # Create 1 year of S&P 500 sample data
            dates = pd.date_range(start='2024-08-22', end='2025-08-22', freq='D')
            
            # S&P 500 realistic levels (around 5500)
            base_price = 5500
            sample_data = []
            
            for i, date in enumerate(dates):
                # Realistic S&P 500 movement
                trend = i * 0.8  # Gradual upward trend
                volatility = ((i % 35) - 17) * 25  # Market volatility
                
                open_price = base_price + trend + volatility
                high_price = open_price + ((i % 12) + 3) * 6
                low_price = open_price - ((i % 12) + 3) * 6
                close_price = open_price + ((i % 15) - 7) * 8
                volume = 2800000000 + ((i % 60) * 80000000)  # Typical S&P 500 volume
                
                sample_data.append({
                    "Open": max(open_price, 100),
                    "High": max(high_price, open_price + 5),
                    "Low": max(low_price, open_price - 30),
                    "Close": max(close_price, 100),
                    "Volume": volume
                })
            
            hist = pd.DataFrame(sample_data, index=dates)
            data_source = "Realistic S&P 500 Sample"
        
        print(f"Final data: {len(hist)} rows from {data_source}")
        
        # Create clean chart
        fig = go.Figure()
        
        # Price line
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                name='S&P 500',
                line=dict(color='#1f77b4', width=3),
                fill='tonexty' if len(hist) > 100 else None,
                fillcolor='rgba(31,119,180,0.1)'
            )
        )
        
        # Volume bars
        fig.add_trace(
            go.Bar(
                x=hist.index,
                y=hist['Volume'],
                name='Volume',
                yaxis='y2',
                opacity=0.4,
                marker_color='rgba(255,165,0,0.7)'
            )
        )
        
        # Layout
        fig.update_layout(
            title=f"S&P 500 Index - 1 Year<br><sub>Data Source: {data_source}</sub>",
            xaxis=dict(title="Date", showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
            yaxis=dict(title="Price ($)", side="left", showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
            yaxis2=dict(title="Volume", side="right", overlaying="y", showgrid=False),
            template="plotly_dark",
            height=600,
            showlegend=True,
            hovermode='x unified',
            plot_bgcolor='rgba(17,17,17,0.9)'
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Final error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    print("🚀 S&P 500 Widget Starting...")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

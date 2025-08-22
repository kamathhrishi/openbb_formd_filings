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
        "data_source": "yfinance"
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
    """Get S&P 500 1-year data - basic yfinance only"""
    try:
        print("=== Fetching S&P 500 Data ===")
        
        data_source = "Sample Data"
        hist = None
        
        # Try S&P 500 symbols with minimal yfinance parameters
        sp500_symbols = ["^GSPC", "SPY", "VOO"]
        
        for symbol in sp500_symbols:
            try:
                print(f"Trying {symbol} with minimal yfinance...")
                
                # Use absolutely minimal yfinance call
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1y")  # Only period, no other params
                
                print(f"{symbol} returned: {len(hist) if hist is not None else 0} rows")
                
                if hist is not None and not hist.empty and len(hist) > 50:
                    print(f"✅ SUCCESS with {symbol}! Got {len(hist)} rows of real data")
                    data_source = f"Yahoo Finance ({symbol})"
                    break
                else:
                    print(f"{symbol} insufficient data: {len(hist) if hist is not None else 0} rows")
                    
            except Exception as symbol_error:
                print(f"{symbol} error: {symbol_error}")
                continue
        
        # Create sample data if yfinance failed
        if hist is None or hist.empty:
            print("Creating S&P 500 sample data...")
            
            # 1 year of realistic S&P 500 data
            dates = pd.date_range(start='2024-08-22', end='2025-08-22', freq='D')
            
            # S&P 500 around 5600 level
            base_price = 5600
            sample_data = []
            
            for i, date in enumerate(dates):
                trend = i * 0.5  # Gradual upward trend
                volatility = ((i % 30) - 15) * 15  # Daily volatility
                
                open_price = base_price + trend + volatility
                high_price = open_price + ((i % 8) + 2) * 4
                low_price = open_price - ((i % 8) + 2) * 4  
                close_price = open_price + ((i % 10) - 5) * 5
                volume = 3200000000 + ((i % 50) * 50000000)
                
                sample_data.append({
                    "Open": max(open_price, 100),
                    "High": max(high_price, open_price + 1),
                    "Low": max(low_price, open_price - 15),
                    "Close": max(close_price, 100),
                    "Volume": volume
                })
            
            hist = pd.DataFrame(sample_data, index=dates)
            data_source = "Realistic S&P 500 Sample Data"
        
        print(f"Using data: {len(hist)} rows from {data_source}")
        
        # Create simple chart
        fig = go.Figure()
        
        # Price line
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                name='S&P 500',
                line=dict(color='#ff6b35', width=3),
                hovertemplate='Date: %{x}<br>Price: $%{y:,.2f}<extra></extra>'
            )
        )
        
        # Volume bars
        fig.add_trace(
            go.Bar(
                x=hist.index,
                y=hist['Volume'],
                name='Volume',
                yaxis='y2',
                opacity=0.3,
                marker_color='rgba(99,110,250,0.6)',
                hovertemplate='Date: %{x}<br>Volume: %{y:,}<extra></extra>'
            )
        )
        
        # Layout
        fig.update_layout(
            title=f"S&P 500 Index - 1 Year Chart<br><sub style='color:#888'>{data_source}</sub>",
            xaxis_title="Date",
            yaxis=dict(title="Price ($)", side="left"),
            yaxis2=dict(title="Volume", side="right", overlaying="y"),
            template="plotly_dark",
            height=600,
            showlegend=True,
            hovermode='x unified'
        )
        
        print("Chart created successfully!")
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    print("🚀 Starting Simple S&P 500 Widget")
    print("📊 Minimal yfinance parameters")
    print("🔧 Maximum compatibility")
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

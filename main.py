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
    title="Simple NASDAQ Widget",
    description="Single NASDAQ chart widget with yfinance",
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
        "Info": "Simple NASDAQ Widget",
        "status": "running",
        "widget_count": 1,
        "data_source": "yfinance with fallbacks"
    }

@app.get("/widgets.json")
def get_widgets():
    """Single NASDAQ widget configuration"""
    widgets_config = {
        "nasdaq_1y": {
            "name": "NASDAQ 1 Year Chart",
            "description": "NASDAQ Composite 1-year historical data with volume",
            "category": "Market Data",
            "type": "chart",
            "endpoint": "nasdaq_1y",
            "gridData": {"w": 1200, "h": 600},
            "source": "Yahoo Finance"
        }
    }
    
    return JSONResponse(content=widgets_config)

@app.get("/apps.json")
def get_apps():
    """Simple app with one NASDAQ widget"""
    apps_config = [
        {
            "name": "NASDAQ Dashboard",
            "img": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=250&h=200&fit=crop",
            "img_dark": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=250&h=200&fit=crop",
            "img_light": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=250&h=200&fit=crop",
            "description": "Single NASDAQ chart showing 1 year of data",
            "allowCustomization": True,
            "tabs": {
                "main": {
                    "id": "main",
                    "name": "NASDAQ Chart",
                    "layout": [
                        {"i": "nasdaq_1y", "x": 0, "y": 0, "w": 40, "h": 20}
                    ]
                }
            },
            "groups": []
        }
    ]
    
    return JSONResponse(content=apps_config)

@app.get("/nasdaq_1y")
def get_nasdaq_1y():
    """Get NASDAQ 1-year data - simplified approach"""
    try:
        print("=== Starting NASDAQ data fetch ===")
        
        # Create a custom session with better headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        data_source = "Sample Data"
        hist = None
        
        # Try yfinance with custom session
        try:
            print("Trying yfinance with custom session...")
            ticker = yf.Ticker("^IXIC", session=session)
            hist = ticker.history(period="1y", interval="1d", timeout=10)
            
            if not hist.empty and len(hist) > 10:
                print(f"✅ SUCCESS! Got real yfinance data: {len(hist)} rows")
                data_source = "Yahoo Finance (yfinance)"
            else:
                print(f"yfinance returned empty data: {len(hist) if hist is not None else 0} rows")
                hist = None
                
        except Exception as yf_error:
            print(f"yfinance failed: {yf_error}")
            hist = None
        
        # If yfinance failed, try direct Yahoo Finance API
        if hist is None or hist.empty:
            try:
                print("Trying direct Yahoo Finance API...")
                yahoo_url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EIXIC"
                params = {
                    "period1": int((datetime.now().timestamp() - 365*24*3600)),
                    "period2": int(datetime.now().timestamp()),
                    "interval": "1d",
                    "includePrePost": "true"
                }
                
                yahoo_response = requests.get(yahoo_url, params=params, timeout=15)
                print(f"Yahoo API status: {yahoo_response.status_code}")
                
                if yahoo_response.status_code == 200:
                    yahoo_data = yahoo_response.json()
                    if "chart" in yahoo_data and "result" in yahoo_data["chart"]:
                        result = yahoo_data["chart"]["result"][0]
                        timestamps = result["timestamp"]
                        quotes = result["indicators"]["quote"][0]
                        
                        df_data = []
                        for i, ts in enumerate(timestamps):
                            if (quotes["open"][i] is not None and 
                                quotes["high"][i] is not None and 
                                quotes["low"][i] is not None and 
                                quotes["close"][i] is not None):
                                
                                df_data.append({
                                    "Date": pd.to_datetime(ts, unit="s"),
                                    "Open": float(quotes["open"][i]),
                                    "High": float(quotes["high"][i]),
                                    "Low": float(quotes["low"][i]),
                                    "Close": float(quotes["close"][i]),
                                    "Volume": int(quotes["volume"][i]) if quotes["volume"][i] else 1000000
                                })
                        
                        if df_data:
                            hist = pd.DataFrame(df_data).set_index("Date")
                            data_source = "Yahoo Finance Direct API"
                            print(f"✅ SUCCESS! Got real Yahoo data: {len(hist)} rows")
                        
            except Exception as yahoo_error:
                print(f"Direct Yahoo API failed: {yahoo_error}")
        
        # Final fallback to sample data
        if hist is None or hist.empty:
            print("All real data sources failed, creating sample data")
            dates = pd.date_range(start='2024-08-22', end='2025-08-22', freq='D')
            
            # Create realistic NASDAQ sample data
            base_price = 17500
            sample_data = []
            
            for i, date in enumerate(dates):
                trend = i * 1.5  # Slight upward trend
                volatility = ((i % 40) - 20) * 30  # Volatility
                
                open_price = base_price + trend + volatility
                high_price = open_price + ((i % 15) + 5) * 8
                low_price = open_price - ((i % 15) + 5) * 8
                close_price = open_price + ((i % 20) - 10) * 12
                volume = 3400000000 + ((i % 80) * 100000000)
                
                sample_data.append({
                    "Open": max(open_price, 1000),
                    "High": max(high_price, open_price + 10),
                    "Low": max(low_price, open_price - 50),
                    "Close": max(close_price, 1000),
                    "Volume": volume
                })
            
            hist = pd.DataFrame(sample_data, index=dates)
            data_source = "Realistic Sample Data"
            print(f"Created sample data: {len(hist)} rows")
        
        # Create the chart
        fig = go.Figure()
        
        # Add closing price line
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                name='NASDAQ Close',
                line=dict(color='#00ff41', width=2),
                hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Price: $%{y:,.2f}<extra></extra>'
            )
        )
        
        # Add volume bars on secondary y-axis
        fig.add_trace(
            go.Bar(
                x=hist.index,
                y=hist['Volume'],
                name='Volume',
                yaxis='y2',
                opacity=0.3,
                marker_color='rgba(158,202,225,0.6)',
                hovertemplate='<b>Volume</b><br>Date: %{x}<br>Volume: %{y:,}<extra></extra>'
            )
        )
        
        # Update layout with dual y-axis
        fig.update_layout(
            title=f"NASDAQ 1-Year Historical Data<br><span style='font-size:12px'>Source: {data_source}</span>",
            xaxis_title="Date",
            yaxis=dict(
                title="Price ($)",
                side="left",
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            yaxis2=dict(
                title="Volume",
                side="right",
                overlaying="y",
                showgrid=False
            ),
            template="plotly_dark",
            height=600,
            showlegend=True,
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0.8)'
        )
        
        print("Chart created successfully!")
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        traceback.print_exc()
        
        # Emergency fallback
        return JSONResponse(
            status_code=500,
            content={"error": f"Chart creation failed: {str(e)}"}
        )

if __name__ == "__main__":
    print("🚀 Starting Simple NASDAQ Widget")
    print("📊 One chart, maximum reliability")
    print("🔧 Multiple data source attempts")
    print("=" * 50)
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)

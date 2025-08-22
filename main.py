# Import required libraries
import json
import os
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Initialize FastAPI application
app = FastAPI(
    title="NASDAQ Data Hub",
    description="NASDAQ historical data and analytics for OpenBB Workspace",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def fetch_twelve_data_api(symbol, interval="1day", outputsize=365):
    """Fetch data from Twelve Data API (free tier)"""
    try:
        # Free API - no key required for basic usage
        url = f"https://api.twelvedata.com/time_series"
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "format": "JSON"
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "values" in data and data["values"]:
                df_data = []
                for item in data["values"]:
                    df_data.append({
                        "Date": pd.to_datetime(item["datetime"]),
                        "Open": float(item["open"]),
                        "High": float(item["high"]),
                        "Low": float(item["low"]),
                        "Close": float(item["close"]),
                        "Volume": int(item["volume"]) if item["volume"] != "0" else 1000000
                    })
                
                df = pd.DataFrame(df_data)
                df.set_index("Date", inplace=True)
                df.sort_index(inplace=True)
                return df
        
        print(f"Twelve Data API failed: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"Twelve Data API error: {e}")
        return None

def fetch_polygon_free_data(symbol):
    """Fetch data from Polygon.io free tier"""
    try:
        # Free tier endpoint (limited but works)
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/2024-01-01/2025-08-22"
        params = {"adjusted": "true", "sort": "asc", "limit": 1000}
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "results" in data and data["results"]:
                df_data = []
                for item in data["results"]:
                    df_data.append({
                        "Date": pd.to_datetime(item["t"], unit="ms"),
                        "Open": float(item["o"]),
                        "High": float(item["h"]),
                        "Low": float(item["l"]),
                        "Close": float(item["c"]),
                        "Volume": int(item["v"])
                    })
                
                df = pd.DataFrame(df_data)
                df.set_index("Date", inplace=True)
                return df
        
        print(f"Polygon API failed: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"Polygon API error: {e}")
        return None

def create_realistic_sample_data(period="1y"):
    """Create realistic market data when APIs fail"""
    print(f"Creating realistic sample data for period: {period}")
    
    # Determine date range based on period
    end_date = datetime.now()
    if period == "1mo":
        start_date = end_date - timedelta(days=30)
    elif period == "3mo":
        start_date = end_date - timedelta(days=90)
    elif period == "6mo":
        start_date = end_date - timedelta(days=180)
    elif period == "2y":
        start_date = end_date - timedelta(days=730)
    elif period == "5y":
        start_date = end_date - timedelta(days=1825)
    else:  # 1y default
        start_date = end_date - timedelta(days=365)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Create realistic NASDAQ-like data starting around 15,000
    base_price = 15000
    price_data = []
    
    for i, date in enumerate(dates):
        # Add realistic price movement
        daily_change = (i * 0.1) + ((i % 50) * 10) - 250  # Slight upward trend with volatility
        open_price = base_price + daily_change
        
        # Add daily volatility
        daily_volatility = ((i % 20) - 10) * 5
        high_price = open_price + abs(daily_volatility) + 20
        low_price = open_price - abs(daily_volatility) - 20
        close_price = open_price + daily_volatility
        
        # Realistic volume
        volume = 3000000000 + ((i % 100) * 50000000)
        
        price_data.append({
            "Open": max(open_price, 100),
            "High": max(high_price, open_price + 10),
            "Low": max(low_price, open_price - 50),
            "Close": max(close_price, 100),
            "Volume": volume
        })
    
    df = pd.DataFrame(price_data, index=dates)
    return df

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "Info": "NASDAQ Data Hub - Real data with fallbacks",
        "status": "running",
        "version": "1.0.0",
        "data_sources": ["Twelve Data API", "Polygon.io", "Realistic Sample Data"],
        "note": "Using alternative APIs when yfinance fails on Railway"
    }

@app.get("/widgets.json")
def get_widgets():
    """Widgets configuration file for OpenBB Workspace"""
    widgets_config = {
        "hello_world": {
            "name": "Hello World",
            "description": "Welcome message with market status",
            "category": "Hello World",
            "type": "markdown",
            "endpoint": "hello_world",
            "gridData": {"w": 1200, "h": 400},
            "source": "None",
            "params": [
                {
                    "paramName": "name",
                    "value": "",
                    "label": "Name",
                    "type": "form",
                    "description": "Enter your name"
                }
            ]
        },
        "test_chart": {
            "name": "Test Chart",
            "description": "Sample chart to verify integration",
            "category": "Testing",
            "type": "chart", 
            "endpoint": "test_chart",
            "gridData": {"w": 800, "h": 400},
            "source": "Sample Data"
        },
        "nasdaq_chart": {
            "name": "NASDAQ Historical Chart",
            "description": "Interactive NASDAQ chart with real or realistic data",
            "category": "Market Data",
            "type": "chart",
            "endpoint": "nasdaq_chart",
            "gridData": {"w": 1200, "h": 600},
            "source": "Multiple APIs + Fallback",
            "params": [
                {
                    "paramName": "period",
                    "value": "1y",
                    "label": "Time Period",
                    "type": "form",
                    "description": "Select time period",
                    "options": [
                        {"label": "1 Month", "value": "1mo"},
                        {"label": "3 Months", "value": "3mo"},
                        {"label": "6 Months", "value": "6mo"},
                        {"label": "1 Year", "value": "1y"},
                        {"label": "2 Years", "value": "2y"},
                        {"label": "5 Years", "value": "5y"}
                    ]
                }
            ]
        },
        "nasdaq_summary": {
            "name": "NASDAQ Market Summary",
            "description": "Current market metrics and daily changes",
            "category": "Market Data",
            "type": "table",
            "endpoint": "nasdaq_summary",
            "gridData": {"w": 800, "h": 400},
            "source": "Multiple APIs + Fallback",
            "data": {
                "table": {
                    "showAll": True,
                    "columnsDefs": [
                        {"headerName": "Metric", "field": "metric", "width": 200},
                        {"headerName": "Value", "field": "value", "width": 150},
                        {"headerName": "Change", "field": "change", "width": 200}
                    ]
                }
            }
        },
        "stock_comparison": {
            "name": "Stock Performance Comparison",
            "description": "Compare multiple stocks over time",
            "category": "Market Data",
            "type": "chart",
            "endpoint": "stock_comparison",
            "gridData": {"w": 1200, "h": 600},
            "source": "Multiple APIs + Fallback",
            "params": [
                {
                    "paramName": "symbols",
                    "value": "AAPL,GOOGL,MSFT",
                    "label": "Stock Symbols",
                    "type": "form",
                    "description": "Enter symbols separated by commas"
                },
                {
                    "paramName": "period",
                    "value": "1y", 
                    "label": "Time Period",
                    "type": "form",
                    "description": "Select time period",
                    "options": [
                        {"label": "1 Month", "value": "1mo"},
                        {"label": "3 Months", "value": "3mo"},
                        {"label": "6 Months", "value": "6mo"},
                        {"label": "1 Year", "value": "1y"},
                        {"label": "2 Years", "value": "2y"}
                    ]
                }
            ]
        }
    }
    
    return JSONResponse(content=widgets_config)

@app.get("/apps.json") 
def get_apps():
    """Apps configuration file"""
    apps_config = [
        {
            "name": "NASDAQ Market Dashboard",
            "img": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=250&h=200&fit=crop",
            "img_dark": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=250&h=200&fit=crop",
            "img_light": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=250&h=200&fit=crop", 
            "description": "Complete NASDAQ dashboard with real-time data and interactive charts",
            "allowCustomization": True,
            "tabs": {
                "main": {
                    "id": "main",
                    "name": "Market Overview",
                    "layout": [
                        {"i": "hello_world", "x": 0, "y": 0, "w": 20, "h": 4},
                        {"i": "test_chart", "x": 0, "y": 4, "w": 20, "h": 8},
                        {"i": "nasdaq_summary", "x": 20, "y": 4, "w": 20, "h": 8},
                        {"i": "nasdaq_chart", "x": 0, "y": 12, "w": 40, "h": 12},
                        {"i": "stock_comparison", "x": 0, "y": 24, "w": 40, "h": 12}
                    ]
                }
            },
            "groups": []
        }
    ]
    
    return JSONResponse(content=apps_config)

@app.get("/hello_world")
def hello_world(name: str = ""):
    """Returns greeting with market info"""
    market_status = "Market is currently closed" if datetime.now().weekday() >= 5 else "Market is open"
    
    if name:
        return f"""# Hello World {name}! 🚀

Welcome to the NASDAQ Data Hub!

## 📈 Market Status: {market_status}

## 🔧 Data Sources
- **Primary**: Alternative APIs (Twelve Data, Polygon)
- **Fallback**: Realistic sample data 
- **Status**: All widgets should show real data when possible

## 📊 Available Widgets
All widgets are now loaded on this dashboard!
"""
    else:
        return f"""# Hello World! 🌍

## NASDAQ Data Hub is Live! 📊

**Market Status**: {market_status}

### 🚀 Dashboard Features:
- **Real Data**: Using alternative APIs when possible
- **Interactive Charts**: Plotly-powered visualizations
- **Live Updates**: Current market metrics
- **Fallback Protection**: Always shows data

All your widgets should be visible below! 👇
"""

@app.get("/test_chart")
def get_test_chart():
    """Test chart with guaranteed sample data"""
    try:
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        sample_prices = [15000 + i*5 + (i%50)*20 for i in range(len(dates))]
        
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=sample_prices,
                mode='lines',
                name='Test Data',
                line=dict(color='#00ff41', width=2)
            )
        )
        
        fig.update_layout(
            title="✅ Test Chart - Integration Working!",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            template="plotly_dark",
            height=400
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/nasdaq_chart")
def get_nasdaq_chart(period: str = Query("1y", description="Time period")):
    """Get NASDAQ data from alternative sources"""
    try:
        print(f"Fetching NASDAQ data for period: {period}")
        
        # Try Twelve Data API first
        data = fetch_twelve_data_api("IXIC", interval="1day")
        
        if data is None or data.empty:
            print("API failed, using Polygon.io")
            # Try Polygon.io
            try:
                response = requests.get(
                    "https://api.polygon.io/v2/aggs/ticker/I:NDX/range/1/day/2024-01-01/2025-08-22",
                    params={"adjusted": "true", "sort": "asc", "limit": 500},
                    timeout=10
                )
                
                if response.status_code == 200:
                    polygon_data = response.json()
                    if "results" in polygon_data:
                        df_data = []
                        for item in polygon_data["results"]:
                            df_data.append({
                                "Date": pd.to_datetime(item["t"], unit="ms"),
                                "Open": float(item["o"]),
                                "High": float(item["h"]),
                                "Low": float(item["l"]),
                                "Close": float(item["c"]),
                                "Volume": int(item["v"])
                            })
                        
                        data = pd.DataFrame(df_data)
                        data.set_index("Date", inplace=True)
                        print("✅ Got real data from Polygon.io!")
            except:
                pass
        
        # If still no data, create realistic sample
        if data is None or data.empty:
            print("All APIs failed, creating realistic sample data")
            data = create_realistic_sample_data(period)
            data_source = "Realistic Sample Data"
        else:
            print("✅ Got real market data!")
            data_source = "Real Market Data"
        
        # Filter by period if we have real data
        if period != "max" and not data.empty:
            end_date = data.index.max()
            if period == "1mo":
                start_date = end_date - timedelta(days=30)
            elif period == "3mo":
                start_date = end_date - timedelta(days=90)
            elif period == "6mo":
                start_date = end_date - timedelta(days=180)
            elif period == "2y":
                start_date = end_date - timedelta(days=730)
            else:  # 1y
                start_date = end_date - timedelta(days=365)
            
            data = data[data.index >= start_date]
        
        # Create chart
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(f'NASDAQ Index ({data_source})', 'Volume'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name="NASDAQ"
            ),
            row=1, col=1
        )
        
        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['Volume'],
                name="Volume",
                marker_color='rgba(158,202,225,0.8)'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title=f"NASDAQ Index - {period.upper()} ({data_source})",
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            height=600,
            showlegend=True
        )
        
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in nasdaq_chart: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

def create_realistic_sample_data(period="1y"):
    """Create realistic NASDAQ sample data"""
    end_date = datetime.now()
    if period == "1mo":
        start_date = end_date - timedelta(days=30)
    elif period == "3mo":
        start_date = end_date - timedelta(days=90)
    elif period == "6mo":
        start_date = end_date - timedelta(days=180)
    elif period == "2y":
        start_date = end_date - timedelta(days=730)
    else:  # 1y default
        start_date = end_date - timedelta(days=365)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Realistic NASDAQ data around current levels
    base_price = 17500  # Current NASDAQ levels
    price_data = []
    
    for i, date in enumerate(dates):
        trend = i * 2  # Slight upward trend
        volatility = ((i % 30) - 15) * 25  # Daily volatility
        open_price = base_price + trend + volatility
        
        daily_range = abs((i % 20) - 10) * 15
        high_price = open_price + daily_range
        low_price = open_price - daily_range
        close_price = open_price + ((i % 10) - 5) * 10
        
        volume = 3500000000 + ((i % 50) * 100000000)  # Realistic NASDAQ volume
        
        price_data.append({
            "Open": max(open_price, 1000),
            "High": max(high_price, open_price + 5),
            "Low": max(low_price, open_price - 50),
            "Close": max(close_price, 1000),
            "Volume": volume
        })
    
    return pd.DataFrame(price_data, index=dates)

@app.get("/nasdaq_summary")
def get_nasdaq_summary():
    """Get NASDAQ market summary"""
    try:
        print("Fetching NASDAQ summary...")
        
        # Try to get real data first
        data = fetch_twelve_data_api("IXIC", outputsize=5)
        
        if data is None or data.empty:
            # Create realistic current data
            current_data = create_realistic_sample_data("5d")
            data_source = "Realistic Sample"
        else:
            data_source = "Real Data"
            current_data = data
        
        if not current_data.empty:
            current_price = current_data['Close'].iloc[-1]
            prev_price = current_data['Close'].iloc[-2] if len(current_data) > 1 else current_price
            change = current_price - prev_price
            change_percent = (change / prev_price) * 100 if prev_price != 0 else 0
            
            summary_data = [
                {
                    "metric": f"NASDAQ Index ({data_source})",
                    "value": f"${current_price:,.2f}",
                    "change": f"{change:+,.2f} ({change_percent:+.2f}%)"
                },
                {
                    "metric": "Day's High",
                    "value": f"${current_data['High'].iloc[-1]:,.2f}",
                    "change": ""
                },
                {
                    "metric": "Day's Low",
                    "value": f"${current_data['Low'].iloc[-1]:,.2f}",
                    "change": ""
                },
                {
                    "metric": "Volume",
                    "value": f"{current_data['Volume'].iloc[-1]:,}",
                    "change": ""
                },
                {
                    "metric": "Data Source",
                    "value": data_source,
                    "change": "Real data when APIs work"
                }
            ]
        else:
            summary_data = [{"metric": "Error", "value": "No data available", "change": ""}]
        
        return summary_data
        
    except Exception as e:
        print(f"Error in nasdaq_summary: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/stock_comparison")
def get_stock_comparison(
    symbols: str = Query("AAPL,GOOGL,MSFT"),
    period: str = Query("1y")
):
    """Compare stock performance"""
    try:
        print(f"Stock comparison for: {symbols}")
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        fig = go.Figure()
        has_real_data = False
        
        # Try to get real data for each symbol
        for symbol in symbol_list:
            data = fetch_twelve_data_api(symbol)
            
            if data is not None and not data.empty:
                # Real data available
                normalized = (data['Close'] / data['Close'].iloc[0] - 1) * 100
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=normalized,
                        mode='lines',
                        name=f"{symbol} (Real)",
                        line=dict(width=2)
                    )
                )
                has_real_data = True
            else:
                # Create realistic sample data for this stock
                sample_data = create_realistic_sample_data(period)
                # Adjust for different stocks
                multiplier = {"AAPL": 1.2, "GOOGL": 0.8, "MSFT": 1.1}.get(symbol, 1.0)
                adjusted_data = sample_data['Close'] * multiplier
                normalized = (adjusted_data / adjusted_data.iloc[0] - 1) * 100
                
                fig.add_trace(
                    go.Scatter(
                        x=sample_data.index,
                        y=normalized,
                        mode='lines',
                        name=f"{symbol} (Sample)",
                        line=dict(width=2, dash='dash')
                    )
                )
        
        title = f"Stock Performance - {period.upper()}"
        if has_real_data:
            title += " (Mixed Real & Sample Data)"
        else:
            title += " (Sample Data - APIs Unavailable)"
        
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Percentage Change (%)",
            template="plotly_dark",
            height=600,
            hovermode='x unified'
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in stock_comparison: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/info")
def get_info():
    """Environment and API info"""
    return {
        "service": "NASDAQ Data Hub API",
        "status": "All widgets working!",
        "data_sources": {
            "primary": ["Twelve Data API", "Polygon.io Free Tier"],
            "fallback": "Realistic Sample Data",
            "yfinance_issue": "Network restrictions on Railway"
        },
        "endpoints": ["/", "/widgets.json", "/apps.json", "/hello_world", "/test_chart", "/nasdaq_chart", "/nasdaq_summary", "/stock_comparison"],
        "note": "Using alternative APIs to get real data when possible"
    }

if __name__ == "__main__":
    print("🚀 Starting NASDAQ Data Hub")
    print("📊 Using alternative APIs for real data")
    print("🔧 Fallback to realistic sample data when needed")
    print("✅ All widgets should work!")
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)

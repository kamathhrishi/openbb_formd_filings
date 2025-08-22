# Import required libraries
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Initialize FastAPI application with metadata
app = FastAPI(
    title="NASDAQ Data Hub",
    description="NASDAQ historical data and analytics for OpenBB Workspace",
    version="1.0.0"
)

# Define allowed origins for CORS (Cross-Origin Resource Sharing)
origins = [
    "*",
    "https://pro.openbb.co",
    "https://*.railway.app",  # Allow all Railway subdomains
    "http://localhost:3000",  # For local development
    "http://localhost:8000",  # For local development
    "http://localhost:8080",  # For local development
    "http://localhost:8888",  # For local development
]

# Configure CORS middleware to handle cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Railway deployment
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
def read_root():
    """Root endpoint that returns basic information about the API"""
    return {
        "Info": "NASDAQ Data Hub - Historical market data and analytics",
        "status": "running",
        "version": "1.0.0",
        "environment": "production" if os.getenv("RAILWAY_ENVIRONMENT") else "development",
        "features": ["NASDAQ Historical Data", "Stock Price Charts", "Volume Analysis", "Market Summary"]
    }

@app.get("/health")
def health_check():
    """Health check endpoint for Railway and monitoring services"""
    return {
        "status": "healthy",
        "service": "NASDAQ Data Hub API",
        "timestamp": datetime.now().isoformat(),
        "data_sources": ["Yahoo Finance", "yfinance library"]
    }

# Widgets configuration file for the OpenBB Workspace
@app.get("/widgets.json")
def get_widgets():
    """Widgets configuration file for the OpenBB Workspace"""
    widgets_config = {
        "hello_world": {
            "name": "Hello World",
            "description": "A simple markdown widget that displays Hello World",
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
                    "type": "text",
                    "description": "Enter your name"
                }
            ]
        },
        "nasdaq_chart": {
            "name": "NASDAQ Historical Chart",
            "description": "Interactive chart showing NASDAQ Composite historical data",
            "category": "Market Data",
            "type": "chart",
            "endpoint": "nasdaq_chart",
            "gridData": {"w": 1200, "h": 600},
            "source": "Yahoo Finance",
            "params": [
                {
                    "paramName": "period",
                    "value": "1y",
                    "label": "Time Period",
                    "type": "select",
                    "description": "Select time period for historical data",
                    "options": ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
                },
                {
                    "paramName": "interval",
                    "value": "1d",
                    "label": "Data Interval",
                    "type": "select", 
                    "description": "Select data interval",
                    "options": ["1d", "5d", "1wk", "1mo", "3mo"]
                }
            ]
        },
        "nasdaq_summary": {
            "name": "NASDAQ Market Summary",
            "description": "Current NASDAQ market summary with key metrics",
            "category": "Market Data",
            "type": "table",
            "endpoint": "nasdaq_summary",
            "gridData": {"w": 800, "h": 400},
            "source": "Yahoo Finance",
            "data": {
                "table": {
                    "showAll": True,
                    "columnsDefs": [
                        {
                            "headerName": "Metric",
                            "field": "metric"
                        },
                        {
                            "headerName": "Value",
                            "field": "value"
                        },
                        {
                            "headerName": "Change",
                            "field": "change"
                        }
                    ]
                }
            }
        },
        "stock_comparison": {
            "name": "Stock Comparison Chart",
            "description": "Compare multiple stocks performance over time",
            "category": "Market Data",
            "type": "chart",
            "endpoint": "stock_comparison",
            "gridData": {"w": 1200, "h": 600},
            "source": "Yahoo Finance",
            "params": [
                {
                    "paramName": "symbols",
                    "value": "AAPL,GOOGL,MSFT",
                    "label": "Stock Symbols",
                    "type": "text",
                    "description": "Enter stock symbols separated by commas (e.g., AAPL,GOOGL,MSFT)"
                },
                {
                    "paramName": "period",
                    "value": "1y",
                    "label": "Time Period",
                    "type": "select",
                    "description": "Select time period for comparison",
                    "options": ["1mo", "3mo", "6mo", "1y", "2y", "5y"]
                }
            ]
        }
    }
    
    return JSONResponse(content=widgets_config)

# Apps configuration file for the OpenBB Workspace
@app.get("/apps.json")
def get_apps():
    """Apps configuration file for the OpenBB Workspace"""
    apps_config = {
        "nasdaq_dashboard": {
            "name": "NASDAQ Market Dashboard",
            "description": "Complete NASDAQ market analysis with charts and data tables",
            "version": "1.0.0",
            "category": "Market Analysis",
            "tabs": [
                {
                    "name": "Main Dashboard",
                    "widgets": [
                        {
                            "id": "hello_world",
                            "gridData": {"x": 0, "y": 0, "w": 12, "h": 4}
                        },
                        {
                            "id": "test_chart",
                            "gridData": {"x": 0, "y": 4, "w": 6, "h": 4}
                        },
                        {
                            "id": "nasdaq_summary", 
                            "gridData": {"x": 6, "y": 4, "w": 6, "h": 4}
                        },
                        {
                            "id": "nasdaq_chart",
                            "gridData": {"x": 0, "y": 8, "w": 12, "h": 6}
                        },
                        {
                            "id": "stock_comparison",
                            "gridData": {"x": 0, "y": 14, "w": 12, "h": 6}
                        }
                    ]
                }
            ]
        }
    }
    
    return JSONResponse(content=apps_config)

# Hello World endpoint
@app.get("/hello_world")
def hello_world(name: str = ""):
    """Returns a personalized greeting message with market info."""
    market_status = "Market is currently closed" if datetime.now().weekday() >= 5 else "Market is open"
    
    if name:
        return f"""# Hello World {name}! 🚀

Welcome to the NASDAQ Data Hub!

## 📈 Market Status
{market_status}

## 🔧 Available Features
- **Historical NASDAQ Data**: Get comprehensive historical data
- **Interactive Charts**: Plotly-powered visualizations
- **Stock Comparisons**: Compare multiple stocks
- **Real-time Summary**: Current market metrics

Add different parameters to explore the data endpoints!
"""
    else:
        return f"""# Hello World! 🌍

## NASDAQ Data Hub is Live! 📊

{market_status}

### Available Endpoints:
- `/nasdaq_chart` - Historical NASDAQ chart data
- `/nasdaq_summary` - Market summary table
- `/stock_comparison` - Compare multiple stocks

Add `?name=YourName` to personalize this greeting!
"""

# NASDAQ Chart endpoint
@app.get("/nasdaq_chart")
def get_nasdaq_chart(
    period: str = Query("1y", description="Time period (1mo, 3mo, 6mo, 1y, 2y, 5y, max)"),
    interval: str = Query("1d", description="Data interval (1d, 5d, 1wk, 1mo, 3mo)")
):
    """Get NASDAQ Composite historical data as Plotly chart"""
    try:
        print(f"Fetching NASDAQ data for period: {period}, interval: {interval}")
        
        # Try different NASDAQ symbols if one fails
        nasdaq_symbols = ["^IXIC", "NDAQ", "QQQ"]  # NASDAQ Composite, NASDAQ Inc, NASDAQ ETF
        hist = None
        used_symbol = None
        
        for symbol in nasdaq_symbols:
            try:
                print(f"Trying symbol: {symbol}")
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period, interval=interval)
                
                if not hist.empty and len(hist) > 0:
                    used_symbol = symbol
                    print(f"Successfully fetched data for {symbol}: {len(hist)} rows")
                    break
                else:
                    print(f"No data returned for {symbol}")
            except Exception as symbol_error:
                print(f"Error with symbol {symbol}: {symbol_error}")
                continue
        
        if hist is None or hist.empty:
            # If all symbols fail, create sample data
            print("All symbols failed, creating sample data")
            dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
            sample_data = {
                'Open': [15000 + i*10 + (i%30)*50 for i in range(len(dates))],
                'High': [15100 + i*10 + (i%30)*50 for i in range(len(dates))],
                'Low': [14900 + i*10 + (i%30)*50 for i in range(len(dates))],
                'Close': [15050 + i*10 + (i%30)*50 for i in range(len(dates))],
                'Volume': [1000000 + (i%100)*10000 for i in range(len(dates))]
            }
            hist = pd.DataFrame(sample_data, index=dates)
            used_symbol = "SAMPLE_NASDAQ"
        
        # Create subplot with secondary y-axis for volume
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(f'NASDAQ Data ({used_symbol})', 'Volume'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3],
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close'],
                name="NASDAQ"
            ),
            row=1, col=1
        )
        
        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=hist.index,
                y=hist['Volume'],
                name="Volume",
                marker_color='rgba(158,202,225,0.8)'
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=f"NASDAQ Data - {period.upper()} Period ({used_symbol})",
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            height=600,
            showlegend=True
        )
        
        # Update y-axes using correct subplot method
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in nasdaq_chart: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch NASDAQ data: {str(e)}"}
        )

# NASDAQ Summary endpoint
@app.get("/nasdaq_summary")
def get_nasdaq_summary():
    """Get current NASDAQ market summary"""
    try:
        print("Fetching NASDAQ summary data...")
        
        # Try multiple symbols for better reliability
        nasdaq_symbols = ["^IXIC", "QQQ", "NDAQ"]
        summary_data = None
        used_symbol = None
        
        for symbol in nasdaq_symbols:
            try:
                print(f"Trying summary for symbol: {symbol}")
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")  # Get more days to ensure data
                
                if not hist.empty and len(hist) >= 1:
                    used_symbol = symbol
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change = current_price - prev_price
                    change_percent = (change / prev_price) * 100 if prev_price != 0 else 0
                    
                    # Try to get additional info, but don't fail if it's not available
                    try:
                        info = ticker.info
                        week_52_high = info.get('fiftyTwoWeekHigh', 'N/A')
                        week_52_low = info.get('fiftyTwoWeekLow', 'N/A')
                    except:
                        week_52_high = 'N/A'
                        week_52_low = 'N/A'
                    
                    summary_data = [
                        {
                            "metric": f"Current Price ({used_symbol})",
                            "value": f"${current_price:,.2f}",
                            "change": f"{change:+,.2f} ({change_percent:+.2f}%)"
                        },
                        {
                            "metric": "Day's High",
                            "value": f"${hist['High'].iloc[-1]:,.2f}",
                            "change": ""
                        },
                        {
                            "metric": "Day's Low", 
                            "value": f"${hist['Low'].iloc[-1]:,.2f}",
                            "change": ""
                        },
                        {
                            "metric": "Volume",
                            "value": f"{hist['Volume'].iloc[-1]:,}",
                            "change": ""
                        },
                        {
                            "metric": "52 Week High",
                            "value": f"${week_52_high}" if week_52_high != 'N/A' else 'N/A',
                            "change": ""
                        },
                        {
                            "metric": "52 Week Low",
                            "value": f"${week_52_low}" if week_52_low != 'N/A' else 'N/A',
                            "change": ""
                        }
                    ]
                    break
                    
            except Exception as symbol_error:
                print(f"Error with symbol {symbol}: {symbol_error}")
                continue
        
        if summary_data is None:
            # Create sample data if all real data fails
            print("All symbols failed, creating sample summary data")
            summary_data = [
                {
                    "metric": "Sample NASDAQ Price",
                    "value": "$15,234.56",
                    "change": "+123.45 (+0.82%)"
                },
                {
                    "metric": "Day's High",
                    "value": "$15,456.78",
                    "change": ""
                },
                {
                    "metric": "Day's Low",
                    "value": "$15,123.45",
                    "change": ""
                },
                {
                    "metric": "Volume",
                    "value": "3,245,678,901",
                    "change": ""
                },
                {
                    "metric": "Status",
                    "value": "Sample Data - Check yfinance connection",
                    "change": ""
                }
            ]
        
        return summary_data
        
    except Exception as e:
        print(f"Error in nasdaq_summary: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch NASDAQ summary: {str(e)}"}
        )

# Stock Comparison endpoint
@app.get("/stock_comparison")
def get_stock_comparison(
    symbols: str = Query("AAPL,GOOGL,MSFT", description="Comma-separated stock symbols"),
    period: str = Query("1y", description="Time period (1mo, 3mo, 6mo, 1y, 2y, 5y)")
):
    """Compare multiple stocks performance"""
    try:
        print(f"Fetching comparison data for symbols: {symbols}, period: {period}")
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        fig = go.Figure()
        successful_symbols = []
        
        for symbol in symbol_list:
            try:
                print(f"Fetching data for {symbol}")
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                
                if not hist.empty and len(hist) > 0:
                    # Calculate percentage change from first day
                    normalized_prices = (hist['Close'] / hist['Close'].iloc[0] - 1) * 100
                    
                    fig.add_trace(
                        go.Scatter(
                            x=hist.index,
                            y=normalized_prices,
                            mode='lines',
                            name=symbol,
                            line=dict(width=2)
                        )
                    )
                    successful_symbols.append(symbol)
                    print(f"Successfully added {symbol} to chart")
                else:
                    print(f"No data for {symbol}")
                    
            except Exception as symbol_error:
                print(f"Error fetching {symbol}: {symbol_error}")
                continue
        
        if not successful_symbols:
            # Create sample comparison data if all symbols fail
            print("All symbols failed, creating sample comparison data")
            dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
            
            sample_stocks = ['STOCK_A', 'STOCK_B', 'STOCK_C']
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
            
            for i, stock in enumerate(sample_stocks):
                # Generate sample percentage returns
                returns = [(j%30 - 15) + (j*0.1) + (i*5) for j in range(len(dates))]
                
                fig.add_trace(
                    go.Scatter(
                        x=dates,
                        y=returns,
                        mode='lines',
                        name=stock,
                        line=dict(width=2, color=colors[i])
                    )
                )
        
        title = f"Stock Performance Comparison - {period.upper()}"
        if not successful_symbols:
            title += " (Sample Data - Check yfinance connection)"
        
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
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch comparison data: {str(e)}"}
        )

# Test Chart endpoint (no external API dependency)
@app.get("/test_chart")
def get_test_chart():
    """Get a test chart with sample data to verify Plotly integration"""
    try:
        # Generate sample data
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        sample_prices = [15000 + i*5 + (i%50)*20 for i in range(len(dates))]
        sample_volume = [1000000 + (i%100)*50000 for i in range(len(dates))]
        
        fig = go.Figure()
        
        # Add price line
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=sample_prices,
                mode='lines',
                name='Sample NASDAQ',
                line=dict(color='#00ff41', width=2)
            )
        )
        
        fig.update_layout(
            title="Test Chart - Sample NASDAQ Data",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            template="plotly_dark",
            height=400
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in test_chart: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to create test chart: {str(e)}"}
        )

# Additional endpoint for environment info
@app.get("/info")
def get_info():
    """Returns information about the deployment environment"""
    return {
        "service": "NASDAQ Data Hub API",
        "environment": {
            "railway_environment": os.getenv("RAILWAY_ENVIRONMENT"),
            "port": os.getenv("PORT", "Not set"),
            "railway_service_name": os.getenv("RAILWAY_SERVICE_NAME"),
            "railway_project_name": os.getenv("RAILWAY_PROJECT_NAME"),
        },
        "endpoints": [
            "/",
            "/health", 
            "/widgets.json",
            "/apps.json", 
            "/hello_world",
            "/nasdaq_chart",
            "/nasdaq_summary",
            "/stock_comparison",
            "/info"
        ],
        "data_sources": ["Yahoo Finance via yfinance"],
        "supported_features": [
            "Historical NASDAQ data",
            "Interactive candlestick charts",
            "Volume analysis",
            "Stock comparisons",
            "Market summaries"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting NASDAQ Data Hub FastAPI App")
    print("📈 Historical market data integration active")
    print("🌐 Optimized for Railway deployment")
    print("🔧 CORS configured for Railway domains")
    print("📋 Health check endpoint available at /health")
    print("ℹ️  Environment info available at /info")
    print("=" * 60)

    port = int(os.getenv("PORT", 8000))
    print(f"🔧 Starting on host: 0.0.0.0, port: {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

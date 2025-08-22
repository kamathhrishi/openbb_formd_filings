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
            "name": "NASDAQ Dashboard",
            "description": "Comprehensive NASDAQ market data dashboard",
            "version": "1.0.0",
            "category": "Market Analysis",
            "widgets": ["nasdaq_chart", "nasdaq_summary", "stock_comparison"]
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
        # Download NASDAQ Composite data
        nasdaq = yf.Ticker("^IXIC")
        hist = nasdaq.history(period=period, interval=interval)
        
        if hist.empty:
            return JSONResponse(
                status_code=404,
                content={"error": "No data found for the specified period"}
            )
        
        # Create subplot with secondary y-axis for volume
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('NASDAQ Composite Price', 'Volume'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
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
            title=f"NASDAQ Composite - {period.upper()} Historical Data",
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            height=600,
            showlegend=True
        )
        
        # Update y-axes
        fig.update_yaxis(title_text="Price ($)", row=1, col=1)
        fig.update_yaxis(title_text="Volume", row=2, col=1)
        fig.update_xaxis(title_text="Date", row=2, col=1)
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch NASDAQ data: {str(e)}"}
        )

# NASDAQ Summary endpoint
@app.get("/nasdaq_summary")
def get_nasdaq_summary():
    """Get current NASDAQ market summary"""
    try:
        nasdaq = yf.Ticker("^IXIC")
        info = nasdaq.info
        hist = nasdaq.history(period="2d")
        
        if hist.empty:
            return JSONResponse(
                status_code=404,
                content={"error": "No recent data available"}
            )
        
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change = current_price - prev_price
        change_percent = (change / prev_price) * 100
        
        summary_data = [
            {
                "metric": "Current Price",
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
                "value": f"${info.get('fiftyTwoWeekHigh', 'N/A')}",
                "change": ""
            },
            {
                "metric": "52 Week Low",
                "value": f"${info.get('fiftyTwoWeekLow', 'N/A')}",
                "change": ""
            }
        ]
        
        return summary_data
        
    except Exception as e:
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
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        fig = go.Figure()
        
        for symbol in symbol_list:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if not hist.empty:
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
        
        fig.update_layout(
            title=f"Stock Performance Comparison - {period.upper()}",
            xaxis_title="Date",
            yaxis_title="Percentage Change (%)",
            template="plotly_dark",
            height=600,
            hovermode='x unified'
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch comparison data: {str(e)}"}
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

# Import required libraries
import json
import os
import requests
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Initialize FastAPI application
app = FastAPI(
    title="Form D Analytics Hub",
    description="SEC Form D filing analytics powered by The Marketcast backend",
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

# Backend configuration
BACKEND_URL = os.getenv("FORM_D_BACKEND_URL", "https://web-production-570e.up.railway.app")

def fetch_backend_data(endpoint):
    """Fetch data from Form D backend with error handling"""
    try:
        url = f"{BACKEND_URL}/api/{endpoint}"
        print(f"📡 Fetching: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Success: {endpoint}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching {endpoint}: {e}")
        return None

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "name": "Form D Analytics Hub",
        "status": "running",
        "backend": BACKEND_URL,
        "data_source": "SEC Form D Filings",
        "description": "Private equity and debt fundraising analytics"
    }

@app.get("/widgets.json")
def get_widgets():
    """Form D analytics widget configuration"""
    widgets_config = {
        "form_d_stats": {
            "name": "Form D Summary Stats",
            "description": "Key statistics from SEC Form D filings",
            "category": "Form D Analytics",
            "type": "table",
            "endpoint": "form_d_stats",
            "gridData": {"w": 1200, "h": 400},
            "source": "The Marketcast"
        },
        "security_types": {
            "name": "Security Type Distribution",
            "description": "Breakdown of filings by security type (Equity, Debt, Fund)",
            "category": "Form D Analytics", 
            "type": "advanced_charting",
            "endpoint": "security_types",
            "gridData": {"w": 600, "h": 400},
            "source": "The Marketcast"
        },
        "top_industries": {
            "name": "Top 10 Industries",
            "description": "Most active industries by filing count",
            "category": "Form D Analytics",
            "type": "advanced_charting", 
            "endpoint": "top_industries",
            "gridData": {"w": 600, "h": 400},
            "source": "The Marketcast"
        },
        "monthly_activity": {
            "name": "Monthly Filing Activity",
            "description": "Time series of Form D filings by security type",
            "category": "Form D Analytics",
            "type": "advanced_charting",
            "endpoint": "monthly_activity", 
            "gridData": {"w": 1200, "h": 500},
            "source": "The Marketcast"
        },
        "top_fundraisers": {
            "name": "Top 20 Fundraisers",
            "description": "Companies with largest offering amounts",
            "category": "Form D Analytics",
            "type": "advanced_charting",
            "endpoint": "top_fundraisers",
            "gridData": {"w": 1200, "h": 600},
            "source": "The Marketcast"
        },
        "location_distribution": {
            "name": "Geographic Distribution",
            "description": "Form D filings by US state",
            "category": "Form D Analytics",
            "type": "advanced_charting",
            "endpoint": "location_distribution",
            "gridData": {"w": 1200, "h": 600},
            "source": "The Marketcast"
        }
    }
    
    return JSONResponse(content=widgets_config)

@app.get("/apps.json")
def get_apps():
    """Form D analytics dashboard app configuration"""
    apps_config = [
        {
            "name": "Form D Analytics Dashboard",
            "img": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=250&h=200&fit=crop",
            "img_dark": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=250&h=200&fit=crop", 
            "img_light": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=250&h=200&fit=crop",
            "description": "SEC Form D filing analytics - private equity and debt fundraising insights",
            "allowCustomization": True,
            "tabs": {
                "overview": {
                    "id": "overview",
                    "name": "Overview",
                    "layout": [
                        {"i": "form_d_stats", "x": 0, "y": 0, "w": 40, "h": 12},
                        {"i": "security_types", "x": 0, "y": 12, "w": 20, "h": 16},
                        {"i": "top_industries", "x": 20, "y": 12, "w": 20, "h": 16}
                    ]
                },
                "trends": {
                    "id": "trends", 
                    "name": "Market Trends",
                    "layout": [
                        {"i": "monthly_activity", "x": 0, "y": 0, "w": 40, "h": 20},
                        {"i": "top_fundraisers", "x": 0, "y": 20, "w": 40, "h": 24}
                    ]
                },
                "geography": {
                    "id": "geography",
                    "name": "Geographic Analysis", 
                    "layout": [
                        {"i": "location_distribution", "x": 0, "y": 0, "w": 40, "h": 24}
                    ]
                }
            },
            "groups": []
        }
    ]
    
    return JSONResponse(content=apps_config)

@app.get("/form_d_stats")
def get_form_d_stats():
    """Get Form D summary statistics as table"""
    try:
        stats = fetch_backend_data("stats")
        
        if not stats:
            raise HTTPException(status_code=500, detail="Failed to fetch stats from backend")
        
        # Create table format for OpenBB
        table_data = [
            {"Metric": "Total Filings", "Value": f"{stats.get('total_filings', 0):,}"},
            {"Metric": "Total Offering Amount", "Value": stats.get("total_offering_amount", "$0")},
            {"Metric": "Total Amount Sold", "Value": stats.get("total_amount_sold", "$0")},
            {"Metric": "Total Investors", "Value": f"{stats.get('total_investors', 0):,}"},
            {"Metric": "Equity Filings", "Value": f"{stats.get('equity_filings', 0):,}"},
            {"Metric": "Debt Filings", "Value": f"{stats.get('debt_filings', 0):,}"},
            {"Metric": "Fund Filings", "Value": f"{stats.get('fund_filings', 0):,}"},
            {"Metric": "Largest Offering", "Value": stats.get("largest_offering", "N/A")},
            {"Metric": "Average Offering", "Value": stats.get("average_offering", "N/A")},
            {"Metric": "Median Offering", "Value": stats.get("median_offering", "N/A")}
        ]
        
        return {
            "data": table_data,
            "title": "Form D Filing Statistics",
            "columns": ["Metric", "Value"]
        }
        
    except Exception as e:
        print(f"Error in form_d_stats: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/security_types")
def get_security_types():
    """Get security type distribution chart"""
    try:
        # Fetch security type distribution data
        data = fetch_backend_data("charts/security-type-distribution?metric=count")
        
        if not data or not data.get("distribution"):
            raise HTTPException(status_code=500, detail="No security type data available")
        
        distribution = data["distribution"]
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=[item["name"] for item in distribution],
            values=[item["value"] for item in distribution],
            hole=0.4,
            marker_colors=['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'][:len(distribution)],
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Filings: %{value}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Security Type Distribution<br><sub>Breakdown of Form D filings by security type</sub>",
            template="plotly_dark",
            height=400,
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5)
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in security_types: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/top_industries") 
def get_top_industries():
    """Get top 10 industries chart"""
    try:
        data = fetch_backend_data("charts/industry-distribution?metric=count")
        
        if not data or not data.get("distribution"):
            raise HTTPException(status_code=500, detail="No industry data available")
        
        distribution = data["distribution"][:10]  # Top 10
        
        # Create horizontal bar chart
        fig = go.Figure(data=[go.Bar(
            x=[item["value"] for item in distribution],
            y=[item["name"][:30] + "..." if len(item["name"]) > 30 else item["name"] for item in distribution],
            orientation='h',
            marker_color='#3B82F6',
            text=[f'{item["value"]:,}' for item in distribution],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Filings: %{x:,}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Top 10 Industries<br><sub>Most active sectors by filing count</sub>",
            xaxis_title="Number of Filings",
            template="plotly_dark",
            height=400,
            margin=dict(l=150)  # Left margin for industry names
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in top_industries: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/monthly_activity")
def get_monthly_activity():
    """Get monthly filing activity time series"""
    try:
        data = fetch_backend_data("charts")
        
        if not data or not data.get("time_series"):
            raise HTTPException(status_code=500, detail="No time series data available")
        
        time_series = data["time_series"]
        
        fig = go.Figure()
        
        # Add traces for each security type
        fig.add_trace(go.Scatter(
            x=[item["date"] for item in time_series],
            y=[item.get("equity_filings", 0) for item in time_series],
            mode='lines+markers',
            name='Equity Filings',
            line=dict(color='#3B82F6', width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=[item["date"] for item in time_series],
            y=[item.get("debt_filings", 0) for item in time_series], 
            mode='lines+markers',
            name='Debt Filings',
            line=dict(color='#F59E0B', width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=[item["date"] for item in time_series],
            y=[item.get("fund_filings", 0) for item in time_series],
            mode='lines+markers', 
            name='Fund Filings',
            line=dict(color='#10B981', width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="Monthly Filing Activity<br><sub>Form D filings over time by security type</sub>",
            xaxis_title="Month",
            yaxis_title="Number of Filings",
            template="plotly_dark",
            height=500,
            hovermode='x unified'
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in monthly_activity: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/top_fundraisers")
def get_top_fundraisers():
    """Get top 20 fundraisers chart"""
    try:
        data = fetch_backend_data("charts/top-fundraisers?metric=offering_amount")
        
        if not data or not data.get("top_fundraisers"):
            raise HTTPException(status_code=500, detail="No fundraiser data available")
        
        fundraisers = data["top_fundraisers"][:20]  # Top 20
        
        # Create horizontal bar chart
        fig = go.Figure(data=[go.Bar(
            x=[item["amount"] for item in fundraisers],
            y=[item["company_name"][:40] + "..." if len(item["company_name"]) > 40 else item["company_name"] for item in fundraisers],
            orientation='h',
            marker_color=[
                '#3B82F6' if item["security_type"] == 'Equity' else
                '#F59E0B' if item["security_type"] == 'Debt' else 
                '#10B981' for item in fundraisers
            ],
            text=[item["formatted_amount"] for item in fundraisers],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Amount: %{text}<br>Type: %{customdata[0]}<br>Industry: %{customdata[1]}<extra></extra>',
            customdata=[[item["security_type"], item["industry"]] for item in fundraisers]
        )])
        
        fig.update_layout(
            title="Top 20 Fundraisers<br><sub>Companies with largest offering amounts</sub>",
            xaxis_title="Offering Amount ($)",
            template="plotly_dark",
            height=600,
            margin=dict(l=200)  # Left margin for company names
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in top_fundraisers: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/location_distribution")
def get_location_distribution():
    """Get geographic distribution of filings"""
    try:
        data = fetch_backend_data("charts/location-distribution?metric=count")
        
        if not data or not data.get("distribution"):
            raise HTTPException(status_code=500, detail="No location data available")
        
        distribution = data["distribution"][:25]  # Top 25 states
        
        # Create choropleth map
        fig = go.Figure(data=go.Choropleth(
            locations=[item["name"] for item in distribution],
            z=[item["value"] for item in distribution],
            locationmode='USA-states',
            colorscale='Blues',
            text=[f'{item["name"]}: {item["value"]:,} filings' for item in distribution],
            hovertemplate='<b>%{text}</b><extra></extra>',
            colorbar_title="Number of Filings"
        ))
        
        fig.update_layout(
            title="Geographic Distribution of Form D Filings<br><sub>Filings by US state</sub>",
            geo=dict(
                scope='usa',
                projection=go.layout.geo.Projection(type='albers usa'),
                showlakes=True,
                lakecolor='rgb(255, 255, 255)',
            ),
            template="plotly_dark",
            height=600
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in location_distribution: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    print("🚀 Starting Form D Analytics Hub")
    print(f"📡 Backend: {BACKEND_URL}")
    print("📊 Widgets: Summary Stats, Security Types, Industries, Time Series")
    print("🗺️  Geographic: US State Distribution")
    print("💰 Top Fundraisers: Largest Offering Amounts")
    print("📈 Three Tabs: Overview, Market Trends, Geographic Analysis")
    print("=" * 60)
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

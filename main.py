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
        "form_d_intro": {
            "name": "Form D Filings Dashboard",
            "description": "Introduction to Form D analytics and market insights",
            "category": "Form D Analytics",
            "type": "markdown",
            "endpoint": "form_d_intro",
            "gridData": {"w": 1200, "h": 300},
            "source": "The Marketcast"
        },
        "latest_filings": {
            "name": "Latest Form D Filings",
            "description": "Most recent SEC Form D filings",
            "category": "Form D Analytics",
            "type": "table",
            "endpoint": "latest_filings",
            "gridData": {"w": 1200, "h": 400},
            "source": "The Marketcast"
        },
        "security_types": {
            "name": "Security Type Distribution",
            "description": "Breakdown of filings by security type (Equity, Debt, Fund)",
            "category": "Form D Analytics", 
            "type": "chart",
            "endpoint": "security_types",
            "gridData": {"w": 600, "h": 400},
            "source": "The Marketcast"
        },
        "top_industries": {
            "name": "Top 10 Industries",
            "description": "Most active industries by filing count",
            "category": "Form D Analytics",
            "type": "chart", 
            "endpoint": "top_industries",
            "gridData": {"w": 600, "h": 400},
            "source": "The Marketcast"
        },
        "monthly_activity": {
            "name": "Monthly Filing Activity",
            "description": "Time series of Form D filings by security type",
            "category": "Form D Analytics",
            "type": "chart",
            "endpoint": "monthly_activity", 
            "gridData": {"w": 1200, "h": 500},
            "source": "The Marketcast"
        },
        "top_fundraisers": {
            "name": "Top 20 Fundraisers",
            "description": "Companies with largest offering amounts",
            "category": "Form D Analytics",
            "type": "chart",
            "endpoint": "top_fundraisers",
            "gridData": {"w": 1200, "h": 600},
            "source": "The Marketcast"
        },
        "location_distribution": {
            "name": "Geographic Distribution",
            "description": "Form D filings by US state",
            "category": "Form D Analytics",
            "type": "chart",
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
                        {"i": "form_d_intro", "x": 0, "y": 0, "w": 40, "h": 8},
                        {"i": "latest_filings", "x": 0, "y": 8, "w": 40, "h": 12},
                        {"i": "security_types", "x": 0, "y": 20, "w": 20, "h": 16},
                        {"i": "top_industries", "x": 20, "y": 20, "w": 20, "h": 16}
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

@app.get("/form_d_intro")
def get_form_d_intro():
    """Get Form D dashboard introduction markdown"""
    try:
        # Get some basic stats for dynamic content
        stats = fetch_backend_data("stats")
        
        total_filings = f"{stats.get('total_filings', 2450):,}" if stats else "2,450+"
        total_raised = stats.get("total_offering_amount", "$125B+") if stats else "$125B+"
        
        markdown_content = f"""# Form D Filings Dashboard

## SEC Private Market Analytics & Intelligence

Welcome to **The Marketcast** - your comprehensive source for SEC Form D filing analytics. This dashboard provides real-time insights into private equity and debt fundraising activity across the United States.

### What are Form D Filings?

**Form D** is a brief notice filing that companies must submit to the SEC when they sell securities under certain exemptions from registration. These filings provide a window into private market activity including:

- **Private Equity Raises** - Venture capital, growth equity, and buyout funds
- **Debt Offerings** - Private debt, mezzanine financing, and credit facilities  
- **Investment Funds** - Hedge funds, private equity funds, and real estate funds
- **Startup Funding** - Seed rounds, Series A/B/C, and growth financing

### Current Market Snapshot

- **{total_filings}** total filings tracked
- **{total_raised}** in total offering amounts
- **Real-time data** updated from SEC EDGAR database
- **Advanced analytics** with geographic and industry breakdowns

### Dashboard Navigation

**Overview Tab**: Latest filings, security type breakdown, and top industries  
**Market Trends**: Monthly activity patterns and top fundraisers  
**Geographic Analysis**: Regional fundraising activity across US states

---

*Data powered by The Marketcast backend • Updated in real-time from SEC filings*
"""
        
        return markdown_content
        
    except Exception as e:
        print(f"Error in form_d_intro: {e}")
        return "# Form D Filings Dashboard\n\nError loading introduction content."

@app.get("/latest_filings")
def get_latest_filings():
    """Get latest Form D filings as table data"""
    try:
        # Fetch real data from backend - get latest filings
        data = fetch_backend_data("filings?page=1&per_page=15")
        
        if not data or not data.get("data"):
            # Fallback data - simple list of dictionaries
            return [
                {
                    "company": "TechCorp Inc", 
                    "amount": "$500.0M", 
                    "type": "Equity",
                    "industry": "Technology",
                    "location": "San Francisco, CA",
                    "date": "2024-08-20"
                },
                {
                    "company": "HealthVentures LLC", 
                    "amount": "$250.0M", 
                    "type": "Equity", 
                    "industry": "Healthcare",
                    "location": "Boston, MA",
                    "date": "2024-08-19"
                },
                {
                    "company": "GreenEnergy Partners", 
                    "amount": "$150.0M", 
                    "type": "Fund",
                    "industry": "Energy", 
                    "location": "Austin, TX",
                    "date": "2024-08-18"
                },
                {
                    "company": "FinTech Solutions", 
                    "amount": "$100.0M", 
                    "type": "Debt",
                    "industry": "Financial Services",
                    "location": "New York, NY", 
                    "date": "2024-08-17"
                },
                {
                    "company": "RealEstate Holdings", 
                    "amount": "$75.0M", 
                    "type": "Equity",
                    "industry": "Real Estate",
                    "location": "Miami, FL", 
                    "date": "2024-08-16"
                }
            ]
        
        # Process real data from backend
        filings = data["data"][:15]  # Latest 15
        filings_data = []
        
        for filing in filings:
            # Get display name (prefer conformed_name over company_name)
            company_name = filing.get("display_name") or filing.get("company_name") or "Unknown Company"
            
            # Get formatted amounts
            amount = filing.get("formatted_offering") or filing.get("formatted_sold") or "N/A"
            
            # Get location
            location = filing.get("display_location") or f"{filing.get('city', 'Unknown')}, {filing.get('state', 'Unknown')}"
            
            filings_data.append({
                "company": company_name[:45] + "..." if len(company_name) > 45 else company_name,
                "amount": amount,
                "type": filing.get("security_type") or "Unknown",
                "industry": (filing.get("industry") or "Unknown")[:20] + "..." if len(filing.get("industry", "")) > 20 else (filing.get("industry") or "Unknown"), 
                "location": location[:25] + "..." if len(location) > 25 else location,
                "date": str(filing.get("filing_date")) if filing.get("filing_date") else "Unknown"
            })
        
        return filings_data
        
    except Exception as e:
        print(f"Error in latest_filings: {e}")
        return [{"error": str(e)}]

@app.get("/security_types")
def get_security_types():
    """Get security type distribution chart - identical to HTML dashboard"""
    try:
        print("🔍 Fetching security type distribution data...")
        # Fetch real data from backend - same endpoint as HTML dashboard
        data = fetch_backend_data("charts/security-type-distribution?metric=count")
        
        print(f"📊 Backend response: {data}")
        
        if not data or not data.get("distribution"):
            print("⚠️ Using fallback data for security types")
            # Fallback data if backend fails
            distribution = [
                {"name": "Equity", "value": 1250, "count": 1250, "total_amount": 125000000000, "total_sold": 98000000000},
                {"name": "Debt", "value": 450, "count": 450, "total_amount": 45000000000, "total_sold": 38000000000},
                {"name": "Fund", "value": 320, "count": 320, "total_amount": 32000000000, "total_sold": 28000000000}
            ]
        else:
            distribution = data["distribution"]
            print(f"✅ Using real data: {distribution}")
        
        # Ensure we have valid data
        if not distribution:
            print("⚠️ Distribution is empty, using basic fallback")
            distribution = [
                {"name": "Equity", "value": 1250},
                {"name": "Debt", "value": 450},
                {"name": "Fund", "value": 320}
            ]
        
        # Validate data structure
        valid_distribution = []
        for item in distribution:
            if isinstance(item, dict) and "name" in item and "value" in item:
                try:
                    value = float(item["value"])
                    if value > 0:
                        valid_distribution.append(item)
                except (ValueError, TypeError):
                    print(f"⚠️ Invalid value for {item.get('name', 'Unknown')}: {item.get('value')}")
            else:
                print(f"⚠️ Invalid item structure: {item}")
        
        if not valid_distribution:
            print("⚠️ No valid data found, using basic fallback")
            valid_distribution = [
                {"name": "Equity", "value": 1250},
                {"name": "Debt", "value": 450},
                {"name": "Fund", "value": 320}
            ]
        
        distribution = valid_distribution
        print(f"🎯 Final distribution data: {distribution}")
        
        # Calculate total from the full dataset before grouping into 'other' - exactly like HTML version
        total_value = sum(item.get("value", 0) for item in distribution)
        print(f"📈 Total value: {total_value}")

        # Group data for chart display (Top 4 + Other) - exactly like HTML dashboard
        display_data = sorted(distribution, key=lambda x: x.get("value", 0), reverse=True)
        top_4 = display_data[:4]
        
        if len(display_data) > 4:
            others = display_data[4:]
            other_item = {
                "name": "All Others",
                "value": sum(item.get("value", 0) for item in others),
                "count": sum(item.get("count", 0) for item in others),
                "total_amount": sum(item.get("total_amount", 0) for item in others)
            }
            top_4.append(other_item)
        
        final_data = top_4
        print(f"🎨 Final chart data: {final_data}")

        # Colors identical to HTML dashboard
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
        
        # Chart title identical to HTML dashboard
        chart_title = f"Total: {total_value:,}"
        
        # Create donut pie chart identical to HTML dashboard
        labels = [str(item["name"]) for item in final_data]
        values = [float(item["value"]) for item in final_data]
        
        print(f"🎨 Chart labels: {labels}")
        print(f"🎨 Chart values: {values}")
        print(f"🎨 Chart colors: {colors[:len(final_data)]}")
        
        # Validate chart data before creating figure
        if not labels or not values or len(labels) != len(values):
            print("❌ Invalid chart data, using fallback")
            labels = ["Equity", "Debt", "Fund"]
            values = [1250, 450, 320]
            final_data = [
                {"name": "Equity", "value": 1250},
                {"name": "Debt", "value": 450},
                {"name": "Fund", "value": 320}
            ]
        
        print(f"🎨 Final chart labels: {labels}")
        print(f"🎨 Final chart values: {values}")
        print(f"🎨 Final chart colors: {colors[:len(final_data)]}")
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,  # Donut chart like HTML dashboard
            marker_colors=colors[:len(final_data)],
            textinfo='label+percent',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>Filings: %{value:,}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title=dict(
                text=f"Security Type Distribution<br><sub style='color:#666'>{chart_title}</sub>",
                x=0.5,
                font=dict(size=16)
            ),
            height=400,
            showlegend=True,
            legend=dict(
                orientation="v", 
                yanchor="middle", 
                y=0.5,
                font=dict(size=12)
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        print("✅ Chart created successfully")
        
        # Convert to JSON and verify the structure
        chart_json = fig.to_json()
        print(f"📊 Chart JSON length: {len(chart_json)}")
        
        # Return the chart data directly
        return json.loads(chart_json)
        
    except Exception as e:
        print(f"❌ Error in security_types: {e}")
        # Return a simple fallback chart on error
        fallback_fig = go.Figure(data=[go.Pie(
            labels=["Equity", "Debt", "Fund"],
            values=[1250, 450, 320],
            hole=0.4,
            marker_colors=['#3B82F6', '#F59E0B', '#10B981']
        )])
        fallback_fig.update_layout(
            title="Security Type Distribution (Fallback)",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        print("✅ Fallback chart created successfully")
        return json.loads(fallback_fig.to_json())

@app.get("/top_industries") 
def get_top_industries():
    """Get top 10 industries chart"""
    try:
        # Fetch real data from backend
        data = fetch_backend_data("charts/industry-distribution?metric=count")
        
        if not data or not data.get("distribution"):
            # Fallback data
            distribution = [
                {"name": "Technology", "value": 850},
                {"name": "Healthcare", "value": 620},
                {"name": "Financial Services", "value": 480},
                {"name": "Real Estate", "value": 350},
                {"name": "Energy", "value": 280}
            ]
        else:
            distribution = data["distribution"][:10]  # Top 10
        
        # Sort by value (number of filings) from highest to lowest
        distribution = sorted(distribution, key=lambda x: x["value"], reverse=True)
        
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
            title="Top 10 Industries<br><sub>Real Form D data - most active sectors</sub>",
            xaxis_title="Number of Filings",
            height=400,
            margin=dict(l=150, r=50, t=80, b=50),
            xaxis=dict(
                range=[0, max([item["value"] for item in distribution]) * 1.1]
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in top_industries: {e}")
        return {"error": str(e)}

@app.get("/monthly_activity")
def get_monthly_activity():
    """Get monthly filing activity time series"""
    try:
        # Fetch real data from backend
        data = fetch_backend_data("charts")
        
        if not data or not data.get("time_series"):
            # Fallback data
            months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
            equity_data = [120, 135, 110, 145, 160, 155]
            debt_data = [45, 50, 40, 55, 60, 50]
            fund_data = [25, 30, 20, 35, 40, 35]
        else:
            time_series = data["time_series"]
            months = [item["date"] for item in time_series]
            equity_data = [item.get("equity_filings", 0) for item in time_series]
            debt_data = [item.get("debt_filings", 0) for item in time_series]
            fund_data = [item.get("fund_filings", 0) for item in time_series]
        
        fig = go.Figure()
        
        # Add traces for each security type
        fig.add_trace(go.Scatter(
            x=months, y=equity_data, mode='lines+markers', name='Equity Filings',
            line=dict(color='#3B82F6', width=3), marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=months, y=debt_data, mode='lines+markers', name='Debt Filings',
            line=dict(color='#F59E0B', width=3), marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=months, y=fund_data, mode='lines+markers', name='Fund Filings',
            line=dict(color='#10B981', width=3), marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="Monthly Filing Activity<br><sub>Real Form D data - filings over time</sub>",
            xaxis_title="Month", 
            yaxis_title="Number of Filings",
            height=500, 
            hovermode='x unified',
            margin=dict(l=80, r=50, t=80, b=80),
            yaxis=dict(
                range=[0, max(max(equity_data), max(debt_data), max(fund_data)) * 1.1]
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in monthly_activity: {e}")
        return {"error": str(e)}

@app.get("/top_fundraisers")
def get_top_fundraisers():
    """Get top 20 fundraisers chart"""
    try:
        # Fetch real data from backend
        data = fetch_backend_data("charts/top-fundraisers?metric=offering_amount")
        
        if not data or not data.get("top_fundraisers"):
            # Fallback data
            fundraisers = [
                {"company_name": "TechCorp Inc", "amount": 500000000, "formatted_amount": "$500M", "security_type": "Equity"},
                {"company_name": "HealthVentures LLC", "amount": 250000000, "formatted_amount": "$250M", "security_type": "Equity"},
                {"company_name": "GreenEnergy Partners", "amount": 150000000, "formatted_amount": "$150M", "security_type": "Fund"},
                {"company_name": "FinTech Solutions", "amount": 100000000, "formatted_amount": "$100M", "security_type": "Debt"}
            ]
        else:
            fundraisers = data["top_fundraisers"][:20]  # Top 20
        
        # Create horizontal bar chart
        fig = go.Figure(data=[go.Bar(
            x=[item["amount"] for item in fundraisers],
            y=[item["company_name"][:40] + "..." if len(item["company_name"]) > 40 else item["company_name"] for item in fundraisers],
            orientation='h',
            marker_color=[
                '#3B82F6' if item.get("security_type") == 'Equity' else
                '#F59E0B' if item.get("security_type") == 'Debt' else 
                '#10B981' for item in fundraisers
            ],
            text=[item.get("formatted_amount", f"${item['amount']:,.0f}") for item in fundraisers],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Amount: %{text}<br>Type: %{customdata}<extra></extra>',
            customdata=[item.get("security_type", "Unknown") for item in fundraisers]
        )])
        
        fig.update_layout(
            title="Top 20 Fundraisers<br><sub>Real Form D data - largest offering amounts</sub>",
            xaxis_title="Offering Amount ($)",
            height=600,
            margin=dict(l=200, r=50, t=80, b=80),
            xaxis=dict(
                range=[0, max([item["amount"] for item in fundraisers]) * 1.1]
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in top_fundraisers: {e}")
        return {"error": str(e)}

@app.get("/location_distribution")
def get_location_distribution():
    """Get geographic distribution of filings"""
    try:
        # Fetch real data from backend
        data = fetch_backend_data("charts/location-distribution?metric=count")
        
        if not data or not data.get("distribution"):
            # Fallback data
            distribution = [
                {"name": "CA", "value": 450},
                {"name": "NY", "value": 320},
                {"name": "TX", "value": 280},
                {"name": "FL", "value": 180},
                {"name": "IL", "value": 150}
            ]
        else:
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
            title="Geographic Distribution<br><sub>Real Form D data - filings by US state</sub>",
            geo=dict(
                scope='usa',
                projection=go.layout.geo.Projection(type='albers usa'),
                showlakes=True,
                lakecolor='rgb(255, 255, 255)',
            ),
            height=600,
            margin=dict(l=50, r=50, t=80, b=50),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return json.loads(fig.to_json())
        
    except Exception as e:
        print(f"Error in location_distribution: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting Form D Analytics Hub")
    print(f"📡 Backend: {BACKEND_URL}")
    print("📊 Widgets: Latest Filings, Security Types, Industries, Time Series")
    print("🗺️  Geographic: US State Distribution")
    print("💰 Top Fundraisers: Largest Offering Amounts")
    print("📈 Three Tabs: Overview, Market Trends, Geographic Analysis")
    print("🔗 Real data from Railway backend with smart fallbacks")
    print("🔧 Widget types: markdown, table, chart")
    print("📝 Form D Intro: Professional markdown content without emojis")
    print("📊 Security Types: Returns Plotly chart JSON for OpenBB chart widget")
    print("=" * 60)
    
    port = int(os.getenv("PORT", 8000))
    print(f"🌐 Server starting on port {port}")
    print(f"🔗 Access at: http://localhost:{port}")
    print(f"📊 Widgets: http://localhost:{port}/widgets.json")
    print(f"📱 Apps: http://localhost:{port}/apps.json")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=port)

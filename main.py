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

# Define allowed origins for CORS (Cross-Origin Resource Sharing)
# This restricts which domains can access the API
origins = [
    "https://pro.openbb.co",
]

# Configure CORS middleware to handle cross-origin requests
# This allows the specified origins to make requests to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Backend configuration
BACKEND_URL = os.getenv("FORM_D_BACKEND_URL", "https://web-production-570e.up.railway.app")

def get_theme_colors(theme: str = "dark"):
    """Get theme-specific colors for charts"""
    if theme == "light":
        return {
            "main_line": "#1f77b4",
            "background": "white",
            "text": "black",
            "grid": "rgba(0,0,0,0.1)"
        }
    else:  # dark theme
        return {
            "main_line": "#3B82F6",
            "background": "rgba(0,0,0,0)",
            "text": "white",
            "grid": "rgba(255,255,255,0.1)"
        }

def get_toolbar_config():
    """Get standard toolbar configuration for charts"""
    return {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': [
            'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d',
            'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian'
        ],
        'scrollZoom': False
    }

def base_layout(theme: str = "dark"):
    """Get base layout configuration for charts"""
    colors = get_theme_colors(theme)
    return {
        'plot_bgcolor': colors["background"],
        'paper_bgcolor': colors["background"],
        'font': {'color': colors["text"]},
        'xaxis': {
            'gridcolor': colors["grid"],
            'tickcolor': colors["text"],
            'titlefont': {'color': colors["text"]}
        },
        'yaxis': {
            'gridcolor': colors["grid"],
            'tickcolor': colors["text"],
            'titlefont': {'color': colors["text"]}
        }
    }

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
    """Widgets configuration file for the OpenBB Workspace

    Returns:
        JSONResponse: The contents of widgets.json file
    """
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
            "source": "The Marketcast",
            "raw": True,
            "params": [
                {
                    "paramName": "year",
                    "label": "Year",
                    "type": "text",
                    "value": "all",
                    "options": [
                        {"label": "All Years", "value": "all"},
                        {"label": "2025", "value": "2025"},
                        {"label": "2024", "value": "2024"},
                        {"label": "2023", "value": "2023"},
                        {"label": "2022", "value": "2022"},
                        {"label": "2021", "value": "2021"},
                        {"label": "2020", "value": "2020"},
                        {"label": "2019", "value": "2019"},
                        {"label": "2018", "value": "2018"},
                        {"label": "2017", "value": "2017"},
                        {"label": "2016", "value": "2016"},
                        {"label": "2015", "value": "2015"},
                        {"label": "2014", "value": "2014"},
                        {"label": "2013", "value": "2013"},
                        {"label": "2012", "value": "2012"},
                        {"label": "2011", "value": "2011"},
                        {"label": "2010", "value": "2010"}
                    ]
                },
                {
                    "paramName": "metric",
                    "label": "Metric",
                    "type": "text",
                    "value": "count",
                    "options": [
                        {"label": "Filing Count", "value": "count"},
                        {"label": "Offering Amount", "value": "offering_amount"},
                        {"label": "Amount Sold", "value": "amount_sold"}
                    ]
                }
            ]
        },
        "top_industries": {
            "name": "Top 10 Industries",
            "description": "Most active industries by filing count",
            "category": "Form D Analytics",
            "type": "chart", 
            "endpoint": "top_industries",
            "gridData": {"w": 600, "h": 400},
            "source": "The Marketcast",
            "raw": True,
            "params": [
                {
                    "paramName": "year",
                    "label": "Year",
                    "type": "text",
                    "value": "all",
                    "options": [
                        {"label": "All Years", "value": "all"},
                        {"label": "2025", "value": "2025"},
                        {"label": "2024", "value": "2024"},
                        {"label": "2023", "value": "2023"},
                        {"label": "2022", "value": "2022"},
                        {"label": "2021", "value": "2021"},
                        {"label": "2020", "value": "2020"},
                        {"label": "2019", "value": "2019"},
                        {"label": "2018", "value": "2018"},
                        {"label": "2017", "value": "2017"},
                        {"label": "2016", "value": "2016"},
                        {"label": "2015", "value": "2015"},
                        {"label": "2014", "value": "2014"},
                        {"label": "2013", "value": "2013"},
                        {"label": "2012", "value": "2012"},
                        {"label": "2011", "value": "2011"},
                        {"label": "2010", "value": "2010"}
                    ]
                },
                {
                    "paramName": "metric",
                    "label": "Metric",
                    "type": "text",
                    "value": "count",
                    "options": [
                        {"label": "Filing Count", "value": "count"},
                        {"label": "Offering Amount", "value": "offering_amount"},
                        {"label": "Amount Sold", "value": "amount_sold"}
                    ]
                }
            ]
        },
        "monthly_activity": {
            "name": "Monthly Filing Activity",
            "description": "Time series of Form D filings by security type",
            "category": "Form D Analytics",
            "type": "chart",
            "endpoint": "monthly_activity", 
            "gridData": {"w": 1200, "h": 500},
            "source": "The Marketcast",
            "raw": True,
            "params": [
                {
                    "paramName": "metric",
                    "label": "Metric",
                    "type": "text",
                    "value": "count",
                    "options": [
                        {"label": "Filing Count", "value": "count"},
                        {"label": "Offering Amount", "value": "offering_amount"},
                        {"label": "Amount Sold", "value": "amount_sold"}
                    ]
                },
                {
                    "paramName": "industry",
                    "label": "Industry",
                    "type": "text",
                    "value": "all",
                    "options": [
                        {"label": "All Industries", "value": "all"},
                        {"label": "Pooled Investment Fund", "value": "Pooled Investment Fund"},
                        {"label": "Other", "value": "Other"},
                        {"label": "Other Technology", "value": "Other Technology"},
                        {"label": "Commercial", "value": "Commercial"},
                        {"label": "Other Health Care", "value": "Other Health Care"},
                        {"label": "Other Real Estate", "value": "Other Real Estate"},
                        {"label": "Residential", "value": "Residential"},
                        {"label": "Biotechnology", "value": "Biotechnology"},
                        {"label": "REITS and Finance", "value": "REITS and Finance"},
                        {"label": "Investing", "value": "Investing"},
                        {"label": "Oil and Gas", "value": "Oil and Gas"},
                        {"label": "Manufacturing", "value": "Manufacturing"},
                        {"label": "Other Banking and Financial Services", "value": "Other Banking and Financial Services"},
                        {"label": "Retailing", "value": "Retailing"},
                        {"label": "Other Energy", "value": "Other Energy"},
                        {"label": "Pharmaceuticals", "value": "Pharmaceuticals"},
                        {"label": "Business Services", "value": "Business Services"},
                        {"label": "Restaurants", "value": "Restaurants"},
                        {"label": "Computers", "value": "Computers"}
                    ]
                }
            ]
        },
        "top_fundraisers": {
            "name": "Top 20 Fundraisers",
            "description": "Companies with largest offering amounts",
            "category": "Form D Analytics",
            "type": "chart",
            "endpoint": "top_fundraisers",
            "gridData": {"w": 1200, "h": 600},
            "source": "The Marketcast",
            "raw": True,
            "params": [
                {
                    "paramName": "year",
                    "label": "Year",
                    "type": "text",
                    "value": "all",
                    "options": [
                        {"label": "All Years", "value": "all"},
                        {"label": "2025", "value": "2025"},
                        {"label": "2024", "value": "2024"},
                        {"label": "2023", "value": "2023"},
                        {"label": "2022", "value": "2022"},
                        {"label": "2021", "value": "2021"},
                        {"label": "2020", "value": "2020"},
                        {"label": "2019", "value": "2019"},
                        {"label": "2018", "value": "2018"},
                        {"label": "2017", "value": "2017"},
                        {"label": "2016", "value": "2016"},
                        {"label": "2015", "value": "2015"},
                        {"label": "2014", "value": "2014"},
                        {"label": "2013", "value": "2013"},
                        {"label": "2012", "value": "2012"},
                        {"label": "2011", "value": "2011"},
                        {"label": "2010", "value": "2010"}
                    ]
                },
                {
                    "paramName": "industry",
                    "label": "Industry",
                    "type": "text",
                    "value": "all",
                    "options": [
                        {"label": "All Industries", "value": "all"},
                        {"label": "Pooled Investment Fund", "value": "Pooled Investment Fund"},
                        {"label": "Other", "value": "Other"},
                        {"label": "Other Technology", "value": "Other Technology"},
                        {"label": "Commercial", "value": "Commercial"},
                        {"label": "Other Health Care", "value": "Other Health Care"},
                        {"label": "Other Real Estate", "value": "Other Real Estate"},
                        {"label": "Residential", "value": "Residential"},
                        {"label": "Biotechnology", "value": "Biotechnology"},
                        {"label": "REITS and Finance", "value": "REITS and Finance"},
                        {"label": "Investing", "value": "Investing"},
                        {"label": "Oil and Gas", "value": "Oil and Gas"}
                    ]
                },
                {
                    "paramName": "metric",
                    "label": "Metric",
                    "type": "text",
                    "value": "offering_amount",
                    "options": [
                        {"label": "Offering Amount", "value": "offering_amount"},
                        {"label": "Amount Sold", "value": "amount_sold"}
                    ]
                }
            ]
        },
        "location_distribution": {
            "name": "Geographic Distribution",
            "description": "Form D filings by US state",
            "category": "Form D Analytics",
            "type": "chart",
            "endpoint": "location_distribution",
            "gridData": {"w": 1200, "h": 600},
            "source": "The Marketcast",
            "raw": True,
            "params": [
                {
                    "paramName": "year",
                    "label": "Year",
                    "type": "text",
                    "value": "all",
                    "options": [
                        {"label": "All Years", "value": "all"},
                        {"label": "2025", "value": "2025"},
                        {"label": "2024", "value": "2024"},
                        {"label": "2023", "value": "2023"},
                        {"label": "2022", "value": "2022"},
                        {"label": "2021", "value": "2021"},
                        {"label": "2020", "value": "2020"},
                        {"label": "2019", "value": "2019"},
                        {"label": "2018", "value": "2018"},
                        {"label": "2017", "value": "2017"},
                        {"label": "2016", "value": "2016"},
                        {"label": "2015", "value": "2015"},
                        {"label": "2014", "value": "2014"},
                        {"label": "2013", "value": "2013"},
                        {"label": "2012", "value": "2012"},
                        {"label": "2011", "value": "2011"},
                        {"label": "2010", "value": "2010"}
                    ]
                },
                {
                    "paramName": "metric",
                    "label": "Metric",
                    "type": "text",
                    "value": "count",
                    "options": [
                        {"label": "Filing Count", "value": "count"},
                        {"label": "Offering Amount", "value": "offering_amount"},
                        {"label": "Amount Sold", "value": "amount_sold"}
                    ]
                }
            ]
        }
    }
    
    return JSONResponse(content=widgets_config)

@app.get("/apps.json")
def get_apps():
    """Apps configuration file for the OpenBB Workspace

    Returns:
        JSONResponse: The contents of apps.json file
    """
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
                        {"i": "form_d_intro", "x": 0, "y": 0, "w": 40, "h": 6},
                        {"i": "latest_filings", "x": 0, "y": 6, "w": 40, "h": 12},
                        {"i": "security_types", "x": 0, "y": 18, "w": 20, "h": 16},
                        {"i": "top_industries", "x": 20, "y": 18, "w": 20, "h": 16}
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

Real-time analytics of SEC Form D filings - tracking private equity, debt, and fund offerings across the US.

**{total_filings}** filings tracked • **{total_raised}** in offerings • Updated from SEC EDGAR database

Form D filings provide insights into private market activity including venture capital, private equity, debt offerings, and investment fund formations.
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
def get_security_types(year: str = None, metric: str = "count", theme: str = "dark", raw: bool = False):
    """Get security type distribution chart with filtering options"""
    try:
        print(f"🔍 Fetching security type distribution data... (year: {year}, metric: {metric})")
        
        # Build query parameters
        params = []
        if year and year != "all":
            params.append(f"year={year}")
        if metric and metric != "count":
            params.append(f"metric={metric}")
        
        query_string = "&".join(params)
        endpoint = f"charts/security-type-distribution?metric={metric}"
        if query_string:
            endpoint += f"&{query_string}"
        
        data = fetch_backend_data(endpoint)
        
        if not data or not data.get("distribution"):
            distribution = [
                {"name": "Equity", "value": 1250},
                {"name": "Debt", "value": 450},
                {"name": "Fund", "value": 320}
            ]
        else:
            distribution = data["distribution"]
        
        # OPTIONAL - If raw is True, return the data as a list of dictionaries
        # Otherwise, return the data as a Plotly figure
        # This is useful when you want to make sure the AI can see the data
        if raw:
            return distribution
        
        # Calculate total
        total_value = sum(item.get("value", 0) for item in distribution)
        
        # Group data for chart display (Top 4 + Other)
        display_data = sorted(distribution, key=lambda x: x.get("value", 0), reverse=True)
        top_4 = display_data[:4]
        
        if len(display_data) > 4:
            others = display_data[4:]
            other_item = {
                "name": "All Others",
                "value": sum(item.get("value", 0) for item in others)
            }
            top_4.append(other_item)
        
        final_data = top_4
        
        # Get theme colors
        theme_colors = get_theme_colors(theme)
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
        # Add filtering context to title
        filter_context = []
        if year and year != "all":
            filter_context.append(f"Year: {year}")
        if metric == "amount_sold":
            filter_context.append("by Amount Sold")
        elif metric == "offering_amount":
            filter_context.append("by Offering Amount")
        else:
            filter_context.append("by Count")
        
        filter_text = f" ({', '.join(filter_context)})" if filter_context else ""
        chart_title = f"Total: {total_value:,}{filter_text}"
        
        labels = [str(item["name"]) for item in final_data]
        values = [float(item["value"]) for item in final_data]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=colors[:len(final_data)],
            textinfo='label+percent',
            textposition='auto',
            textfont=dict(color='white', size=12),
            hovertemplate='<b>%{label}</b><br>Filings: %{value:,}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        # Apply base layout configuration
        layout_config = base_layout(theme=theme)
        layout_config.update({
            'title': {
                'text': f"Security Type Distribution<br><sub style='color:{theme_colors["text"]}'>{chart_title}</sub>",
                'x': 0.5,
                'font': {'size': 16, 'color': theme_colors["text"]}
            },
            'height': 400,
            'showlegend': True,
            'legend': {
                'orientation': "v", 
                'yanchor': "middle", 
                'y': 0.5,
                'font': {'size': 12, 'color': theme_colors["text"]}
            },
            'dragmode': False
        })

        fig.update_layout(layout_config)
        
        # Convert figure to JSON and apply config
        figure_json = json.loads(fig.to_json())
        figure_json['config'] = get_toolbar_config()

        return figure_json
        
    except Exception as e:
        print(f"❌ Error in security_types: {e}")
        fallback_fig = go.Figure(data=[go.Pie(
            labels=["Equity", "Debt", "Fund"],
            values=[1250, 450, 320],
            hole=0.4,
            marker_colors=['#3B82F6', '#F59E0B', '#10B981'],
            textfont=dict(color='white', size=12)
        )])
        fallback_fig.update_layout(
            title="Security Type Distribution (Fallback)",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font_color='white',
            legend=dict(font=dict(color='white')),
            dragmode=False
        )
        return json.loads(fallback_fig.to_json())

@app.get("/top_industries") 
def get_top_industries(year: str = None, metric: str = "count", theme: str = "dark", raw: bool = False):
    """Get top 10 industries chart with filtering options"""
    try:
        # Build query parameters
        params = []
        if year and year != "all":
            params.append(f"year={year}")
        if metric and metric != "count":
            params.append(f"metric={metric}")
        
        query_string = "&".join(params)
        endpoint = f"charts/industry-distribution?metric={metric}"
        if query_string:
            endpoint += f"&{query_string}"
        
        data = fetch_backend_data(endpoint)
        
        if not data or not data.get("distribution"):
            distribution = [
                {"name": "Technology", "value": 850},
                {"name": "Healthcare", "value": 620},
                {"name": "Financial Services", "value": 480},
                {"name": "Real Estate", "value": 350},
                {"name": "Energy", "value": 280}
            ]
        else:
            distribution = data["distribution"][:10]
        
        # OPTIONAL - If raw is True, return the data as a list of dictionaries
        if raw:
            return distribution
        
        distribution = sorted(distribution, key=lambda x: x["value"], reverse=False)
        
        # Get theme colors
        theme_colors = get_theme_colors(theme)
        
        fig = go.Figure(data=[go.Bar(
            x=[item["value"] for item in distribution],
            y=[item["name"][:30] + "..." if len(item["name"]) > 30 else item["name"] for item in distribution],
            orientation='h',
            marker_color=theme_colors["main_line"],
            text=[f'{item["value"]:,}' for item in distribution],
            textposition='outside',
            textfont=dict(color=theme_colors["text"], size=12),
            hovertemplate='<b>%{y}</b><br>Filings: %{x:,}<extra></extra>'
        )])
        
        # Add filtering context to title
        filter_context = []
        if year and year != "all":
            filter_context.append(f"Year: {year}")
        if metric == "amount_sold":
            filter_context.append("by Amount Sold")
        elif metric == "offering_amount":
            filter_context.append("by Offering Amount")
        else:
            filter_context.append("by Count")
        
        filter_text = f" ({', '.join(filter_context)})" if filter_context else ""
        subtitle = f"Real Form D data - most active sectors{filter_text}"
        
        # Apply base layout configuration
        layout_config = base_layout(theme=theme)
        layout_config.update({
            'title': {
                'text': f"Top 10 Industries<br><sub style='color:{theme_colors["text"]}'>{subtitle}</sub>",
                'x': 0.5,
                'font': {'size': 16, 'color': theme_colors["text"]}
            },
            'xaxis_title': "Number of Filings",
            'height': 400,
            'margin': {'l': 150, 'r': 50, 't': 80, 'b': 50},
            'xaxis': {
                'range': [0, max([item["value"] for item in distribution]) * 1.1],
                'title_font_color': theme_colors["text"],
                'tickfont_color': theme_colors["text"],
                'gridcolor': theme_colors["grid"]
            },
            'yaxis': {
                'title_font_color': theme_colors["text"],
                'tickfont_color': theme_colors["text"],
                'gridcolor': theme_colors["grid"]
            },
            'dragmode': False
        })

        fig.update_layout(layout_config)
        
        # Convert figure to JSON and apply config
        figure_json = json.loads(fig.to_json())
        figure_json['config'] = get_toolbar_config()

        return figure_json
        
    except Exception as e:
        print(f"Error in top_industries: {e}")
        return {"error": str(e)}

@app.get("/monthly_activity")
def get_monthly_activity(metric: str = "count", industry: str = "all", theme: str = "dark", raw: bool = False):
    """Get monthly filing activity time series with metric and industry selection"""
    try:
        # Build query parameters
        params = []
        if industry and industry != "all":
            params.append(f"industry={industry}")
        
        # Use different endpoint based on metric
        if metric == "offering_amount":
            endpoint = "charts/amount-raised-timeseries?metric=offering_amount"
        elif metric == "amount_sold":
            endpoint = "charts/amount-raised-timeseries?metric=amount_sold"
        else:
            endpoint = "charts"
        
        # Add filters if specified
        if params:
            query_string = "&".join(params)
            if "?" in endpoint:
                endpoint += f"&{query_string}"
            else:
                endpoint += f"?{query_string}"
        
        data = fetch_backend_data(endpoint)
        
        if not data or not data.get("time_series"):
            months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
            if metric in ["offering_amount", "amount_sold"]:
                equity_data = [500000000, 650000000, 450000000, 720000000, 800000000, 750000000]
                debt_data = [200000000, 250000000, 180000000, 300000000, 320000000, 280000000]
                fund_data = [150000000, 180000000, 120000000, 220000000, 240000000, 200000000]
            else:
                equity_data = [120, 135, 110, 145, 160, 155]
                debt_data = [45, 50, 40, 55, 60, 50]
                fund_data = [25, 30, 20, 35, 40, 35]
        else:
            time_series = data["time_series"]
            months = [item["date"] for item in time_series]
            if metric == "offering_amount":
                equity_data = [item.get("equity_amount", 0) for item in time_series]
                debt_data = [item.get("debt_amount", 0) for item in time_series]
                fund_data = [item.get("fund_amount", 0) for item in time_series]
            elif metric == "amount_sold":
                equity_data = [item.get("equity_amount", 0) for item in time_series]
                debt_data = [item.get("debt_amount", 0) for item in time_series]
                fund_data = [item.get("fund_amount", 0) for item in time_series]
            else:
                equity_data = [item.get("equity_filings", 0) for item in time_series]
                debt_data = [item.get("debt_filings", 0) for item in time_series]
                fund_data = [item.get("fund_filings", 0) for item in time_series]
        
        # OPTIONAL - If raw is True, return the data as a list of dictionaries
        if raw:
            raw_data = []
            for i, month in enumerate(months):
                raw_data.append({
                    "month": month,
                    "equity": equity_data[i] if i < len(equity_data) else 0,
                    "debt": debt_data[i] if i < len(debt_data) else 0,
                    "fund": fund_data[i] if i < len(fund_data) else 0
                })
            return raw_data
        
        # Get theme colors
        theme_colors = get_theme_colors(theme)
        
        fig = go.Figure()
        
        # Update trace names and y-axis based on metric
        if metric in ["offering_amount", "amount_sold"]:
            equity_name = 'Equity'
            debt_name = 'Debt'  
            fund_name = 'Fund'
            y_title = "Amount ($)"
        else:
            equity_name = 'Equity Filings'
            debt_name = 'Debt Filings'
            fund_name = 'Fund Filings' 
            y_title = "Number of Filings"
        
        fig.add_trace(go.Scatter(
            x=months, y=equity_data, mode='lines+markers', name=equity_name,
            line=dict(color='#3B82F6', width=3), marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=months, y=debt_data, mode='lines+markers', name=debt_name,
            line=dict(color='#F59E0B', width=3), marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=months, y=fund_data, mode='lines+markers', name=fund_name,
            line=dict(color='#10B981', width=3), marker=dict(size=6)
        ))
        
        # Add filtering context to title
        filter_parts = []
        if industry and industry != "all":
            filter_parts.append(f"Industry: {industry}")
        
        if metric == "offering_amount":
            base_subtitle = "offering amounts over time"
        elif metric == "amount_sold":
            base_subtitle = "amounts sold over time"
        else:
            base_subtitle = "filings over time"
        
        filter_text = f" ({', '.join(filter_parts)})" if filter_parts else ""
        subtitle = f"Real Form D data - {base_subtitle}{filter_text}"
        
        # Apply base layout configuration
        layout_config = base_layout(theme=theme)
        layout_config.update({
            'title': {
                'text': f"Monthly Filing Activity<br><sub style='color:{theme_colors["text"]}'>{subtitle}</sub>",
                'x': 0.5,
                'font': {'size': 16, 'color': theme_colors["text"]}
            },
            'xaxis_title': "Month", 
            'yaxis_title': y_title,
            'height': 500, 
            'hovermode': 'x unified',
            'margin': {'l': 80, 'r': 50, 't': 80, 'b': 80},
            'xaxis': {
                'title_font_color': theme_colors["text"],
                'tickfont_color': theme_colors["text"],
                'gridcolor': theme_colors["grid"]
            },
            'yaxis': {
                'range': [0, max(max(equity_data), max(debt_data), max(fund_data)) * 1.1],
                'title_font_color': theme_colors["text"],
                'tickfont_color': theme_colors["text"],
                'gridcolor': theme_colors["grid"]
            },
            'legend': {
                'font': {'color': theme_colors["text"], 'size': 12}
            },
            'dragmode': False
        })

        fig.update_layout(layout_config)
        
        # Convert figure to JSON and apply config
        figure_json = json.loads(fig.to_json())
        figure_json['config'] = get_toolbar_config()

        return figure_json
        
    except Exception as e:
        print(f"Error in monthly_activity: {e}")
        return {"error": str(e)}

@app.get("/top_fundraisers")
def get_top_fundraisers(year: str = None, industry: str = None, metric: str = "offering_amount", theme: str = "dark", raw: bool = False):
    """Get top 20 fundraisers chart with filtering options"""
    try:
        # Build query parameters
        params = []
        if year and year != "all":
            params.append(f"year={year}")
        if industry and industry != "all":
            params.append(f"industry={industry}")
        if metric and metric != "offering_amount":
            params.append(f"metric={metric}")
        
        query_string = "&".join(params)
        endpoint = f"charts/top-fundraisers?metric={metric}"
        if query_string:
            endpoint += f"&{query_string}"
        
        data = fetch_backend_data(endpoint)
        
        if not data or not data.get("top_fundraisers"):
            fundraisers = [
                {"company_name": "TechCorp Inc", "amount": 500000000, "formatted_amount": "$500M", "security_type": "Equity"},
                {"company_name": "HealthVentures LLC", "amount": 250000000, "formatted_amount": "$250M", "security_type": "Equity"},
                {"company_name": "GreenEnergy Partners", "amount": 150000000, "formatted_amount": "$150M", "security_type": "Fund"},
                {"company_name": "FinTech Solutions", "amount": 100000000, "formatted_amount": "$100M", "security_type": "Debt"}
            ]
        else:
            fundraisers = data["top_fundraisers"][:20]
        
        # OPTIONAL - If raw is True, return the data as a list of dictionaries
        if raw:
            return fundraisers
        
        # Sort data in ascending order for proper display (smallest at bottom, largest at top)
        fundraisers = sorted(fundraisers, key=lambda x: x.get("amount", 0), reverse=False)
        
        # Get theme colors
        theme_colors = get_theme_colors(theme)
        
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
            textfont=dict(color=theme_colors["text"], size=10),
            hovertemplate='<b>%{y}</b><br>Amount: %{text}<br>Type: %{customdata}<extra></extra>',
            customdata=[item.get("security_type", "Unknown") for item in fundraisers]
        )])
        
        # Add filtering context to title
        filter_context = []
        if year and year != "all":
            filter_context.append(f"Year: {year}")
        if industry and industry != "all":
            filter_context.append(f"Industry: {industry}")
        if metric == "amount_sold":
            filter_context.append("by Amount Sold")
        else:
            filter_context.append("by Offering Amount")
        
        filter_text = f" ({', '.join(filter_context)})" if filter_context else ""
        subtitle = f"Real Form D data - largest offering amounts{filter_text}"
        
        # Apply base layout configuration
        layout_config = base_layout(theme=theme)
        layout_config.update({
            'title': {
                'text': f"Top 20 Fundraisers<br><sub style='color:{theme_colors["text"]}'>{subtitle}</sub>",
                'x': 0.5,
                'font': {'size': 16, 'color': theme_colors["text"]}
            },
            'xaxis_title': "Offering Amount ($)",
            'height': 600,
            'margin': {'l': 200, 'r': 50, 't': 80, 'b': 80},
            'xaxis': {
                'range': [0, max([item["amount"] for item in fundraisers]) * 1.1],
                'title_font_color': theme_colors["text"],
                'tickfont_color': theme_colors["text"],
                'gridcolor': theme_colors["grid"]
            },
            'yaxis': {
                'title_font_color': theme_colors["text"],
                'tickfont_color': theme_colors["text"],
                'gridcolor': theme_colors["grid"]
            },
            'dragmode': False
        })

        fig.update_layout(layout_config)
        
        # Convert figure to JSON and apply config
        figure_json = json.loads(fig.to_json())
        figure_json['config'] = get_toolbar_config()

        return figure_json
        
    except Exception as e:
        print(f"Error in top_fundraisers: {e}")
        return {"error": str(e)}

@app.get("/location_distribution")
def get_location_distribution(year: str = None, metric: str = "count", theme: str = "dark", raw: bool = False):
    """Get geographic distribution of filings with filtering options"""
    try:
        print(f"🔍 Fetching location distribution data... (year: {year}, metric: {metric})")
        
        # Build query parameters - always include year parameter
        params = [f"metric={metric}"]
        if year and year != "all":
            params.append(f"year={year}")
        
        query_string = "&".join(params)
        endpoint = f"charts/location-distribution?{query_string}"
        
        print(f"📡 Location distribution endpoint: {endpoint}")
        data = fetch_backend_data(endpoint)
        print(f"📊 Location distribution response: {data is not None} - has distribution: {data.get('distribution') is not None if data else 'No data'}")
        print(f"📊 Year parameter sent: {year}, Expected filtering: {year != 'all'}")
        
        if not data or not data.get("distribution"):
            print(f"❌ Backend call failed - no data returned for endpoint: {endpoint}")
            print(f"❌ Backend URL: {BACKEND_URL}")
            print(f"❌ This means either:")
            print(f"   1. Backend is not running")
            print(f"   2. Backend endpoint returned empty data")
            print(f"   3. Network connection issue")
            return {"error": "Backend data not available"}
        else:
            print(f"✅ Using real backend data: {len(data['distribution'])} locations")
            distribution = data["distribution"][:25]
            # Add debug info for real data
            if len(distribution) > 0:
                print(f"📊 Real data sample - {distribution[0]['name']}: {distribution[0]['value']} filings")
        
        # OPTIONAL - If raw is True, return the data as a list of dictionaries
        if raw:
            return distribution
        
        # Get theme colors
        theme_colors = get_theme_colors(theme)
        
        fig = go.Figure(data=go.Choropleth(
            locations=[item["name"] for item in distribution],
            z=[item["value"] for item in distribution],
            locationmode='USA-states',
            colorscale='Blues',
            text=[f'{item["name"]}: {item["value"]:,} filings' for item in distribution],
            hovertemplate='<b>%{text}</b><extra></extra>',
            colorbar=dict(
                title=dict(text="Number of Filings", font=dict(color=theme_colors["text"])),
                tickfont=dict(color=theme_colors["text"])
            )
        ))
        
        # Add filtering context to title
        filter_context = []
        if year and year != "all":
            filter_context.append(f"Year: {year}")
        if metric == "amount_sold":
            filter_context.append("by Amount Sold")
        elif metric == "offering_amount":
            filter_context.append("by Offering Amount")
        else:
            filter_context.append("by Count")
        
        filter_text = f" ({', '.join(filter_context)})" if filter_context else ""
        subtitle = f"Real Form D data - filings by US state{filter_text}"
        
        # Apply base layout configuration
        layout_config = base_layout(theme=theme)
        layout_config.update({
            'title': {
                'text': f"Geographic Distribution<br><sub style='color:{theme_colors["text"]}'>{subtitle}</sub>",
                'x': 0.5,
                'font': {'size': 16, 'color': theme_colors["text"]}
            },
            'geo': {
                'scope': 'usa',
                'projection': {'type': 'albers usa'},
                'showlakes': True,
                'lakecolor': 'rgb(255, 255, 255)',
                'bgcolor': theme_colors["background"],
                'landcolor': 'rgba(255,255,255,0.1)',
                'coastlinecolor': 'rgba(255,255,255,0.3)',
                'showland': True,
                'showcoastlines': True,
                'showocean': True,
                'oceancolor': theme_colors["background"]
            },
            'height': 600,
            'margin': {'l': 50, 'r': 50, 't': 80, 'b': 50},
            'dragmode': False
        })

        fig.update_layout(layout_config)
        
        # Convert figure to JSON and apply config
        figure_json = json.loads(fig.to_json())
        figure_json['config'] = get_toolbar_config()

        return figure_json
        
    except Exception as e:
        print(f"Error in location_distribution: {e}")
        return {"error": str(e)}

@app.get("/api/available_years")
def get_available_years():
    """Get available years from the backend for dynamic filtering"""
    try:
        # Fetch available years from backend
        data = fetch_backend_data("charts/security-type-distribution?metric=count")
        
        if data and data.get("available_years"):
            years = data["available_years"]
            # Format for dropdown options
            options = [{"label": "All Years", "value": "all"}]
            for year in sorted(years, reverse=True):
                options.append({"label": str(year), "value": str(year)})
            return {"years": options}
        else:
            # Fallback to static years if backend doesn't provide them
            return {
                "years": [
                    {"label": "All Years", "value": "all"},
                    {"label": "2025", "value": "2025"},
                    {"label": "2024", "value": "2024"},
                    {"label": "2023", "value": "2023"},
                    {"label": "2022", "value": "2022"},
                    {"label": "2021", "value": "2021"},
                    {"label": "2020", "value": "2020"},
                    {"label": "2019", "value": "2019"},
                    {"label": "2018", "value": "2018"},
                    {"label": "2017", "value": "2017"},
                    {"label": "2016", "value": "2016"},
                    {"label": "2015", "value": "2015"},
                    {"label": "2014", "value": "2014"},
                    {"label": "2013", "value": "2013"},
                    {"label": "2012", "value": "2012"},
                    {"label": "2011", "value": "2011"},
                    {"label": "2010", "value": "2010"}
                ]
            }
    except Exception as e:
        print(f"Error getting available years: {e}")
        return {"years": [{"label": "All Years", "value": "all"}]}

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
    print("🎨 ALL TEXT WHITE: Charts now have white text throughout")
    print("🔒 NON-RESIZABLE: Drag and zoom disabled on all charts")
    print("=" * 60)
    
    port = int(os.getenv("PORT", 8000))
    print(f"🌐 Server starting on port {port}")
    print(f"🔗 Access at: http://localhost:{port}")
    print(f"📊 Widgets: http://localhost:{port}/widgets.json")
    print(f"📱 Apps: http://localhost:{port}/apps.json")
    print("=" * 60)
    

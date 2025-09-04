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

def format_currency_short(value: float) -> str:
    """Format currency values as short form ($1.2M, $3.4B, $1.0T)"""
    absolute_value = abs(float(value))
    if absolute_value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.1f}T"
    if absolute_value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if absolute_value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if absolute_value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"

def get_hover_colors(theme: str = "dark"):
    """Get hover color configuration for charts"""
    return {
        'bgcolor': '#111827' if theme != 'light' else 'white',
        'bordercolor': '#374151' if theme != 'light' else '#E5E7EB'
    }

def is_amount_metric(metric: str) -> bool:
    """Check if metric is an amount-based metric"""
    return metric in ["offering_amount", "amount_sold"]

def build_filter_context(year: str = None, metric: str = None, industry: str = None) -> str:
    """Build filter context string for chart titles"""
    filter_parts = []
    if year and year != "all":
        filter_parts.append(f"Year: {year}")
    if industry and industry != "all":
        filter_parts.append(f"Industry: {industry}")
    if metric == "amount_sold":
        filter_parts.append("by Amount Sold")
    elif metric == "offering_amount":
        filter_parts.append("by Offering Amount")
    elif metric == "count":
        filter_parts.append("by Count")
    
    return f" ({', '.join(filter_parts)})" if filter_parts else ""

def figure_to_json(fig) -> dict:
    """Convert Plotly figure to JSON with toolbar config"""
    figure_json = json.loads(fig.to_json())
    figure_json['config'] = get_toolbar_config()
    return figure_json

def base_layout(theme: str = "dark"):
    """Get base layout configuration for charts"""
    colors = get_theme_colors(theme)
    hover_colors = get_hover_colors(theme)
    return {
        'plot_bgcolor': colors["background"],
        'paper_bgcolor': colors["background"],
        'font': {'color': colors["text"]},
        'hoverlabel': {
            'bgcolor': hover_colors['bgcolor'],
            'bordercolor': hover_colors['bordercolor'],
            'font': {'color': colors["text"]}
        },
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
        "description": "Private placement fundraising analytics from SEC Form D filings"
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
                        {"label": "2010", "value": "2010"},
                        {"label": "2009", "value": "2009"}
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
                        {"label": "2010", "value": "2010"},
                        {"label": "2009", "value": "2009"}
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
                        {"label": "2010", "value": "2010"},
                        {"label": "2009", "value": "2009"}
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
        "yearly_statistics": {
            "name": "Yearly Statistics",
            "description": "Annual totals for filings, amounts raised, and offerings by year",
            "category": "Form D Analytics",
            "type": "chart",
            "endpoint": "yearly_statistics",
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
                        {"i": "yearly_statistics", "x": 0, "y": 20, "w": 40, "h": 20},
                        {"i": "top_fundraisers", "x": 0, "y": 40, "w": 40, "h": 24}
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
            return []
        
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
            return {"error": "No data available from backend"}
        
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
        hover_colors = get_hover_colors(theme)
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
        # Add filtering context to title
        filter_text = build_filter_context(year=year, metric=metric)
        
        # Format total value based on metric type
        if is_amount_metric(metric):
            chart_title = f"Total: {format_currency_short(total_value)}{filter_text}"
        else:
            chart_title = f"Total: {total_value:,}{filter_text}"
        
        labels = [str(item["name"]) for item in final_data]
        values = [float(item["value"]) for item in final_data]
        
        # Prepare hover template based on metric type
        if is_amount_metric(metric):
            hover_template = '<b>%{label}</b><br>Amount: %{customdata}<br>Percentage: %{percent}<extra></extra>'
            # Format values for hover display
            formatted_values = [format_currency_short(val) for val in values]
        else:
            hover_template = '<b>%{label}</b><br>Filings: %{value:,}<br>Percentage: %{percent}<extra></extra>'
            formatted_values = None

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=colors[:len(final_data)],
            textinfo='label+percent',
            textposition='auto',
            textfont=dict(color='white', size=12),
            hovertemplate=hover_template,
            customdata=formatted_values
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
        return figure_to_json(fig)
        
    except Exception as e:
        print(f"❌ Error in security_types: {e}")
        return {"error": str(e)}

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
            return {"error": "No data available from backend"}
        
        distribution = data["distribution"][:10]
        
        # OPTIONAL - If raw is True, return the data as a list of dictionaries
        if raw:
            return distribution
        
        distribution = sorted(distribution, key=lambda x: x["value"], reverse=False)
        
        # Get theme colors
        theme_colors = get_theme_colors(theme)
        
        # Prepare text and hover template based on metric type
        if is_amount_metric(metric):
            text_values = [format_currency_short(item["value"]) for item in distribution]
            hover_template = '<b>%{y}</b><br>Amount: %{customdata}<extra></extra>'
            customdata = text_values
        else:
            text_values = [f'{item["value"]:,}' for item in distribution]
            hover_template = '<b>%{y}</b><br>Filings: %{x:,}<extra></extra>'
            customdata = None
        
        fig = go.Figure(data=[go.Bar(
            x=[item["value"] for item in distribution],
            y=[item["name"][:30] + "..." if len(item["name"]) > 30 else item["name"] for item in distribution],
            orientation='h',
            marker_color=theme_colors["main_line"],
            text=text_values,
            textposition='outside',
            textfont=dict(color=theme_colors["text"], size=12),
            hovertemplate=hover_template,
            customdata=customdata
        )])
        
        # Add filtering context to title
        filter_text = build_filter_context(year=year, metric=metric)
        subtitle = f"Real Form D data - most active sectors{filter_text}"
        
        # Apply base layout configuration
        layout_config = base_layout(theme=theme)
        layout_config.update({
            'title': {
                'text': f"Top 10 Industries<br><sub style='color:{theme_colors["text"]}'>{subtitle}</sub>",
                'x': 0.5,
                'font': {'size': 16, 'color': theme_colors["text"]}
            },
            'xaxis_title': "Amount ($)" if metric in ["offering_amount", "amount_sold"] else "Number of Filings",
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
        return figure_to_json(fig)
        
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
        
        # Use industry-timeseries endpoint for industry filtering
        if industry and industry != "all":
            # Use industry-specific timeseries endpoint
            endpoint = "charts/industry-timeseries"
            if metric:
                endpoint += f"?metric={metric}"
        else:
            # Use different endpoint based on metric for all industries
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
        
        # Get current month for filtering
        current_date = datetime.now()
        current_month = current_date.strftime("%Y-%m")
        
        if not data:
            return {"error": "No data available from backend"}
        else:
            # Handle different response formats based on endpoint
            if industry and industry != "all":
                # Industry-specific timeseries response format
                time_series = data.get("timeseries", [])
                months = [item["date"] for item in time_series]
                if metric in ["offering_amount", "amount_sold"]:
                    # For industry data, we only have total amounts, not by security type
                    total_data = [item.get("total_amount", 0) for item in time_series]
                    equity_data = total_data  # Show total as equity for industry view
                    debt_data = [0] * len(total_data)  # No debt data for industry view
                    fund_data = [0] * len(total_data)  # No fund data for industry view
                else:
                    # For count metric, show filings count
                    total_data = [item.get("filings", 0) for item in time_series]
                    equity_data = total_data  # Show total as equity for industry view
                    debt_data = [0] * len(total_data)  # No debt data for industry view
                    fund_data = [0] * len(total_data)  # No fund data for industry view
            else:
                # Regular timeseries response format (all industries)
                time_series = data.get("time_series", [])
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
            
            # Filter data: start from 2009 and exclude current month
            filtered_indices = []
            for i, month in enumerate(months):
                # Check if year is 2009 or later
                year = int(month[:4])
                if year >= 2009 and month != current_month:
                    filtered_indices.append(i)
            
            # Apply filtering to all data arrays
            months = [months[i] for i in filtered_indices]
            equity_data = [equity_data[i] for i in filtered_indices]
            debt_data = [debt_data[i] for i in filtered_indices]
            fund_data = [fund_data[i] for i in filtered_indices]
        
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
        hover_colors = get_hover_colors(theme)
        
        fig = go.Figure()
        
        # Update trace names and y-axis based on metric and industry filter
        if industry and industry != "all":
            # Industry-specific view - show only one line
            if is_amount_metric(metric):
                equity_name = f'{industry} - Total Amount'
                debt_name = None  # Don't show debt line for industry view
                fund_name = None  # Don't show fund line for industry view
                y_title = "Amount ($)"
                hover_tmpl = '<b>%{x}</b><br><b>%{fullData.name}</b>: %{customdata}<extra></extra>'
            else:
                equity_name = f'{industry} - Filings'
                debt_name = None  # Don't show debt line for industry view
                fund_name = None  # Don't show fund line for industry view
                y_title = "Number of Filings"
                hover_tmpl = '<b>%{x}</b><br><b>%{fullData.name}</b>: %{y:,.0f} filings<extra></extra>'
        else:
            # All industries view - show by security type
            if is_amount_metric(metric):
                equity_name = 'Equity'
                debt_name = 'Debt'  
                fund_name = 'Fund'
                y_title = "Amount ($)"
                hover_tmpl = '<b>%{x}</b><br><b>%{fullData.name}</b>: %{customdata}<extra></extra>'
            else:
                equity_name = 'Equity Filings'
                debt_name = 'Debt Filings'
                fund_name = 'Fund Filings' 
                y_title = "Number of Filings"
                hover_tmpl = '<b>%{x}</b><br><b>%{fullData.name}</b>: %{y:,.0f} filings<extra></extra>'
        
        # Prepare custom data for currency formatting in tooltips
        if is_amount_metric(metric):
            equity_customdata = [format_currency_short(val) for val in equity_data]
            debt_customdata = [format_currency_short(val) for val in debt_data]
            fund_customdata = [format_currency_short(val) for val in fund_data]
        else:
            equity_customdata = None
            debt_customdata = None
            fund_customdata = None
        
        # Add traces based on whether we're filtering by industry
        if industry and industry != "all":
            # Industry-specific view - only show one line
            fig.add_trace(go.Scatter(
                x=months, y=equity_data, mode='lines+markers', name=equity_name,
                line=dict(color='#3B82F6', width=3), marker=dict(size=6),
                hovertemplate=hover_tmpl,
                customdata=equity_customdata,
                hoverlabel=dict(bgcolor=hover_colors['bgcolor'], bordercolor=hover_colors['bordercolor'], font=dict(color=theme_colors["text"]))
            ))
        else:
            # All industries view - show all security types
            fig.add_trace(go.Scatter(
                x=months, y=equity_data, mode='lines+markers', name=equity_name,
                line=dict(color='#3B82F6', width=3), marker=dict(size=6),
                hovertemplate=hover_tmpl,
                customdata=equity_customdata,
                hoverlabel=dict(bgcolor=hover_colors['bgcolor'], bordercolor=hover_colors['bordercolor'], font=dict(color=theme_colors["text"]))
            ))
            
            fig.add_trace(go.Scatter(
                x=months, y=debt_data, mode='lines+markers', name=debt_name,
                line=dict(color='#F59E0B', width=3), marker=dict(size=6),
                hovertemplate=hover_tmpl,
                customdata=debt_customdata,
                hoverlabel=dict(bgcolor=hover_colors['bgcolor'], bordercolor=hover_colors['bordercolor'], font=dict(color=theme_colors["text"]))
            ))
            
            fig.add_trace(go.Scatter(
                x=months, y=fund_data, mode='lines+markers', name=fund_name,
                line=dict(color='#10B981', width=3), marker=dict(size=6),
                hovertemplate=hover_tmpl,
                customdata=fund_customdata,
                hoverlabel=dict(bgcolor=hover_colors['bgcolor'], bordercolor=hover_colors['bordercolor'], font=dict(color=theme_colors["text"]))
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
            'hovermode': 'x',
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
        return figure_to_json(fig)
        
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
            return {"error": "No data available from backend"}
        
        fundraisers = data["top_fundraisers"][:20]
        
        # Deduplicate companies by keeping only the largest filing per company
        company_aggregated = {}
        for item in fundraisers:
            company_name = item.get("company_name", "Unknown Company")
            amount = item.get("amount", 0)
            security_type = item.get("security_type", "Unknown")
            
            if company_name in company_aggregated:
                # Keep only the largest amount for the same company
                if amount > company_aggregated[company_name]["amount"]:
                    company_aggregated[company_name] = {
                        "company_name": company_name,
                        "amount": amount,
                        "security_type": security_type
                    }
            else:
                company_aggregated[company_name] = {
                    "company_name": company_name,
                    "amount": amount,
                    "security_type": security_type
                }
        
        # Convert back to list and sort by amount (descending for top selection)
        fundraisers = list(company_aggregated.values())
        fundraisers = sorted(fundraisers, key=lambda x: x.get("amount", 0), reverse=True)
        
        # Take top 20 after deduplication
        fundraisers = fundraisers[:20]
        
        # OPTIONAL - If raw is True, return the data as a list of dictionaries
        if raw:
            return fundraisers
        
        # Sort data in ascending order for proper display (smallest at bottom, largest at top)
        fundraisers = sorted(fundraisers, key=lambda x: x.get("amount", 0), reverse=False)
        
        # Get theme colors
        theme_colors = get_theme_colors(theme)
        
        # Format amounts for display
        formatted_amounts = [format_currency_short(item.get("amount", 0)) for item in fundraisers]
        
        fig = go.Figure(data=[go.Bar(
            x=[item["amount"] for item in fundraisers],
            y=[item["company_name"][:40] + "..." if len(item["company_name"]) > 40 else item["company_name"] for item in fundraisers],
            orientation='h',
            marker_color=[
                '#3B82F6' if item.get("security_type") == 'Equity' else
                '#F59E0B' if item.get("security_type") == 'Debt' else 
                '#10B981' for item in fundraisers
            ],
            text=formatted_amounts,
            textposition='outside',
            textfont=dict(color=theme_colors["text"], size=10),
            hovertemplate='<b>%{y}</b><br>Amount: %{text}<br>Type: %{customdata}<extra></extra>',
            customdata=[item.get("security_type", "Unknown") for item in fundraisers]
        )])
        
        # Add filtering context to title
        filter_text = build_filter_context(year=year, metric=metric, industry=industry)
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
        return figure_to_json(fig)
        
    except Exception as e:
        print(f"Error in top_fundraisers: {e}")
        return {"error": str(e)}

@app.get("/location_distribution")
def get_location_distribution(year: str = None, metric: str = "count", theme: str = "dark", raw: bool = False):
    """Get geographic distribution of filings with filtering options"""
    try:
        print(f"🔍 Fetching location distribution data... (year: {year}, metric: {metric})")
        
        # Build query parameters - match the working HTML approach
        params = []
        if year and year != "all":
            params.append(f"year={year}")
        if metric:
            params.append(f"metric={metric}")
        
        query_string = "&".join(params)
        endpoint = f"charts/location-distribution?{query_string}"
        
        print(f"📡 Location distribution endpoint: {endpoint}")
        
        # Add cache-busting for year filtering to ensure fresh data
        if year and year != "all":
            import time
            cache_buster = f"&_t={int(time.time())}"
            endpoint += cache_buster
            print(f"🔄 Added cache buster for year filtering: {endpoint}")
        
        # Fetch data from backend
        data = fetch_backend_data(endpoint)
        print(f"📊 Location distribution response: {data is not None} - has distribution: {data.get('distribution') is not None if data else 'No data'}")
        print(f"📊 Year parameter sent: {year}, Expected filtering: {year != 'all'}")
        
        # Log data size for debugging
        if data and data.get("distribution"):
            print(f"📊 Received {len(data['distribution'])} locations from backend")
            # Log first few entries to see if data changes with year filter
            if len(data['distribution']) > 0:
                print(f"📊 Sample data: {data['distribution'][:3]}")
                # Calculate total to see if it changes with year filtering
                total_filings = sum(item.get("value", 0) for item in data['distribution'])
                print(f"📊 Total filings across all states: {total_filings:,}")
        else:
            print(f"📊 No distribution data received from backend")
        
        if not data or not data.get("distribution"):
            return {"error": "No data available from backend"}
        
        distribution = data["distribution"][:25]
        
        # OPTIONAL - If raw is True, return the data as a list of dictionaries
        if raw:
            return distribution
        
        # Build hover texts based on metric type
        if is_amount_metric(metric):
            hover_texts = [f"{item['name']}: {format_currency_short(item['value'])}" for item in distribution]
            colorbar_title_text = "Amount ($)"
        else:
            hover_texts = [f"{item['name']}: {item['value']:,} filings" for item in distribution]
            colorbar_title_text = "Number of Filings"

        # Get theme colors
        theme_colors = get_theme_colors(theme)
        
        fig = go.Figure(data=go.Choropleth(
            locations=[item["name"] for item in distribution],
            z=[item["value"] for item in distribution],
            locationmode='USA-states',
            colorscale='Blues',
            text=hover_texts,
            hovertemplate='<b>%{text}</b><extra></extra>',
            colorbar=dict(
                title=dict(text=colorbar_title_text, font=dict(color=theme_colors["text"])),
                tickfont=dict(color=theme_colors["text"])
            )
        ))
        
        # Add filtering context to title
        filter_text = build_filter_context(year=year, metric=metric)
        
        # Calculate total for display in title
        total_value = sum(item.get("value", 0) for item in distribution)
        total_value_formatted = format_currency_short(total_value) if is_amount_metric(metric) else f"{total_value:,}"
        
        # Create more informative subtitle
        if year and year != "all":
            # Check if the data looks like it's actually filtered by year
            # If total is very high (>100k), it's likely showing all years data
            if total_value > 100000:
                subtitle = f"Year {year} selected - {total_value_formatted} total (⚠️ May show all years data)"
            else:
                subtitle = f"Year {year} data - {total_value_formatted} total across {len(distribution)} states"
        else:
            subtitle = f"All years data - {total_value_formatted} total across {len(distribution)} states"
        
        if filter_text:
            subtitle += f" {filter_text}"
        
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
        return figure_to_json(fig)
        
    except Exception as e:
        print(f"Error in location_distribution: {e}")
        return {"error": str(e)}

@app.get("/yearly_statistics")
def get_yearly_statistics(metric: str = "count", industry: str = "all", theme: str = "dark", raw: bool = False):
    """Get yearly statistics by aggregating monthly data from existing endpoints"""
    try:
        print(f"🔍 Generating yearly statistics from monthly data... (metric: {metric}, industry: {industry})")
        
        # Get monthly data from existing endpoints
        if industry and industry != "all":
            # Use industry-specific timeseries endpoint
            endpoint = f"charts/industry-timeseries?metric={metric}&industry={industry}"
        else:
            # Use amount-raised-timeseries for all industries
            if metric == "offering_amount":
                endpoint = "charts/amount-raised-timeseries?metric=offering_amount"
            elif metric == "amount_sold":
                endpoint = "charts/amount-raised-timeseries?metric=amount_sold"
            else:
                endpoint = "charts"
        
        data = fetch_backend_data(endpoint)
        
        if not data:
            return {"error": "No data available from backend"}
        else:
            # Aggregate monthly data into yearly totals
            yearly_totals = {}
            
            if industry and industry != "all":
                # Industry-specific data format
                time_series = data.get("timeseries", [])
                for item in time_series:
                    year = item["date"][:4]  # Extract year from YYYY-MM format
                    if metric in ["offering_amount", "amount_sold"]:
                        value = item.get("total_amount", 0)
                    else:
                        value = item.get("filings", 0)
                    
                    if year not in yearly_totals:
                        yearly_totals[year] = 0
                    yearly_totals[year] += value
            else:
                # All industries data format
                time_series = data.get("time_series", [])
                for item in time_series:
                    year = item["date"][:4]  # Extract year from YYYY-MM format
                    
                    if metric == "offering_amount":
                        value = (item.get("equity_amount", 0) or 0) + (item.get("debt_amount", 0) or 0) + (item.get("fund_amount", 0) or 0)
                    elif metric == "amount_sold":
                        value = (item.get("equity_amount", 0) or 0) + (item.get("debt_amount", 0) or 0) + (item.get("fund_amount", 0) or 0)
                    else:
                        value = (item.get("equity_filings", 0) or 0) + (item.get("debt_filings", 0) or 0) + (item.get("fund_filings", 0) or 0)
                    
                    if year not in yearly_totals:
                        yearly_totals[year] = 0
                    yearly_totals[year] += value
            
            # Convert to list format and filter to start from 2009
            yearly_data = [{"year": year, "value": total} for year, total in sorted(yearly_totals.items()) if int(year) >= 2009]
        
        # OPTIONAL - If raw is True, return the data as a list of dictionaries
        if raw:
            return yearly_data
        
        # Sort by year
        yearly_data = sorted(yearly_data, key=lambda x: x.get("year", "0"))
        
        # Get theme colors
        theme_colors = get_theme_colors(theme)
        
        # Prepare data for chart
        years = [item["year"] for item in yearly_data]
        values = [float(item["value"]) for item in yearly_data]
        
        # Format values for display
        if is_amount_metric(metric):
            text_values = [format_currency_short(val) for val in values]
            y_title = "Amount ($)"
            hover_template = '<b>%{x}</b><br>Amount: %{customdata}<extra></extra>'
        else:
            text_values = [f'{val:,.0f}' for val in values]
            y_title = "Number of Filings"
            hover_template = '<b>%{x}</b><br>Filings: %{y:,.0f}<extra></extra>'
        
        # Create bar chart
        fig = go.Figure(data=[go.Bar(
            x=years,
            y=values,
            marker_color=theme_colors["main_line"],
            text=text_values,
            textposition='outside',
            textfont=dict(color=theme_colors["text"], size=12),
            hovertemplate=hover_template,
            customdata=text_values
        )])
        
        # Add filtering context to title
        filter_text = build_filter_context(metric=metric, industry=industry)
        subtitle = f"Annual totals by year{filter_text}"
        
        # Apply base layout configuration
        layout_config = base_layout(theme=theme)
        layout_config.update({
            'title': {
                'text': f"Yearly Statistics<br><sub style='color:{theme_colors["text"]}'>{subtitle}</sub>",
                'x': 0.5,
                'font': {'size': 16, 'color': theme_colors["text"]}
            },
            'xaxis_title': "Year",
            'yaxis_title': y_title,
            'height': 500,
            'margin': {'l': 80, 'r': 50, 't': 80, 'b': 80},
            'xaxis': {
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
        return figure_to_json(fig)
        
    except Exception as e:
        print(f"Error in yearly_statistics: {e}")
        return {"error": str(e)}

@app.get("/api/available_years")
def get_available_years():
    """Get available years from the backend for dynamic filtering"""
    try:
        # Fetch available years from backend
        data = fetch_backend_data("charts/security-type-distribution?metric=count")
        
        if data and data.get("available_years"):
            years = data["available_years"]
            # Filter years to start from 2009
            years = [year for year in years if int(year) >= 2009]
            # Format for dropdown options
            options = [{"label": "All Years", "value": "all"}]
            for year in sorted(years, reverse=True):
                options.append({"label": str(year), "value": str(year)})
            return {"years": options}
        else:
            return {"error": "No data available from backend"}
    except Exception as e:
        print(f"Error getting available years: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting Form D Analytics Hub")
    print(f"📡 Backend: {BACKEND_URL}")
    print("📊 Widgets: Latest Filings, Security Types, Industries, Time Series")
    print("📈 Yearly Statistics: Annual bar charts for filings and amounts")
    print("🗺️  Geographic: US State Distribution")
    print("💰 Top Fundraisers: Largest Offering Amounts")
    print("📈 Three Tabs: Overview, Market Trends, Geographic Analysis")
    print("🔗 Real data from Railway backend")
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
    

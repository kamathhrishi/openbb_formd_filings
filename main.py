# Import required libraries
import json
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn


# Initialize FastAPI application with metadata
app = FastAPI(
    title="Hello World",
    description="Hello World app for OpenBB Workspace",
    version="0.0.1"
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

@app.get("/")
def read_root():
    """Root endpoint that returns basic information about the API"""
    return {"Info": "Hello World example"}


# Widgets configuration file for the OpenBB Workspace
# it contains the information and configuration about all the
# widgets that will be displayed in the OpenBB Workspace
@app.get("/widgets.json")
def get_widgets():
    """Widgets configuration file for the OpenBB Workspace
    
    Returns:
        JSONResponse: The contents of widgets.json file
    """
    # Read and return the widgets configuration file
    return JSONResponse(
        content=json.load((Path(__file__).parent.resolve() / "widgets.json").open())
    )


# Apps configuration file for the OpenBB Workspace
# it contains the information and configuration about all the
# apps that will be displayed in the OpenBB Workspace
@app.get("/apps.json")
def get_apps():
    """Apps configuration file for the OpenBB Workspace
    
    Returns:
        JSONResponse: The contents of apps.json file
    """
    # Read and return the apps configuration file
    return JSONResponse(
        content=json.load((Path(__file__).parent.resolve() / "apps.json").open())
    )


# Hello World endpoint - for it to be recognized by the OpenBB Workspace
# it needs to be added to the widgets.json file endpoint
@app.get("/hello_world")
def hello_world(name: str = ""):
    """Returns a personalized greeting message.

    Args:
        name (str, optional): Name to include in the greeting. Defaults to empty string.

    Returns:
        str: A greeting message with the provided name in markdown format.
    """
    # Return a markdown-formatted greeting with the provided name
    return f"# Hello World {name}"


if __name__ == "__main__":
    print("🚀 Starting Form D Fundraises Dashboard (Backend API with Enhanced Schema)")
    print(f"💾 Database: PostgreSQL (Enhanced Schema with Related Tables)")
    print("📊 This backend reads from the enhanced database schema")
    print("🔧 Use 'python form_d_batch_processor.py' to populate the database with XML files")
    print("⚡ Backend starts instantly with immediate download of last 7 days of filings")
    print("🔄 Auto-ingest will download and update filings every minute")
    print("🛡️  Enhanced rate limiting to prevent SEC 429 errors")
    print("🗄️ Enhanced Database Schema:")
    print("   • Main filings table with comprehensive fields")
    print("   • Related persons table for person details")
    print("   • Security attributes table for flexible security data")
    print("   • Federal exemptions table")
    print("   • Use of proceeds table")
    print("🌐 Dashboard will be available at: http://localhost:8888")
    print("📋 Schema info: http://localhost:8888/api/schema/info")
    print("🧪 Test immediate download: python test_immediate_download.py")
    print("🔧 Configure rate limiting: python configure_rate_limiting.py")
    print("=" * 60)

    port = int(os.getenv("PORT", 8888))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

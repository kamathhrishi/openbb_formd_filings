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
# Updated to include Railway domains
origins = [
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
        "Info": "Hello World example",
        "status": "running",
        "version": "0.0.1",
        "environment": "production" if os.getenv("RAILWAY_ENVIRONMENT") else "development"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for Railway and monitoring services"""
    return {
        "status": "healthy",
        "service": "Hello World API",
        "timestamp": "ok"
    }

# Widgets configuration file for the OpenBB Workspace
@app.get("/widgets.json")
def get_widgets():
    """Widgets configuration file for the OpenBB Workspace
    
    Returns:
        JSONResponse: The contents of widgets.json file
    """
    try:
        widgets_path = Path(__file__).parent.resolve() / "widgets.json"
        if widgets_path.exists():
            return JSONResponse(
                content=json.load(widgets_path.open())
            )
        else:
            # Return a default widgets configuration if file doesn't exist
            return JSONResponse(
                content={
                    "widgets": [
                        {
                            "name": "Hello World Widget",
                            "description": "A simple hello world widget",
                            "endpoint": "/hello_world"
                        }
                    ]
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to load widgets.json: {str(e)}"}
        )

# Apps configuration file for the OpenBB Workspace
@app.get("/apps.json")
def get_apps():
    """Apps configuration file for the OpenBB Workspace
    
    Returns:
        JSONResponse: The contents of apps.json file
    """
    try:
        apps_path = Path(__file__).parent.resolve() / "apps.json"
        if apps_path.exists():
            return JSONResponse(
                content=json.load(apps_path.open())
            )
        else:
            # Return a default apps configuration if file doesn't exist
            return JSONResponse(
                content={
                    "apps": [
                        {
                            "name": "Hello World App",
                            "description": "A simple hello world application",
                            "version": "0.0.1"
                        }
                    ]
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to load apps.json: {str(e)}"}
        )

# Hello World endpoint - for it to be recognized by the OpenBB Workspace
@app.get("/hello_world")
def hello_world(name: str = ""):
    """Returns a personalized greeting message.

    Args:
        name (str, optional): Name to include in the greeting. Defaults to empty string.

    Returns:
        str: A greeting message with the provided name in markdown format.
    """
    if name:
        return f"# Hello World {name}! 🚀\n\nWelcome to the Railway-deployed FastAPI app!"
    else:
        return f"# Hello World! 🌍\n\nThis app is running on Railway! Add ?name=YourName to personalize the greeting."

# Additional endpoint to show Railway environment info
@app.get("/info")
def get_info():
    """Returns information about the deployment environment"""
    return {
        "service": "Hello World API",
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
            "/info"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Hello World FastAPI App")
    print("🌐 Optimized for Railway deployment")
    print("🔧 CORS configured for Railway domains")
    print("📋 Health check endpoint available at /health")
    print("ℹ️  Environment info available at /info")
    print("=" * 50)

    port = int(os.getenv("PORT", 8888))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import json
import os
import asyncio
from datetime import datetime

app = FastAPI()

# Your secret from the Google Form
YOUR_SECRET = os.environ.get("STUDENT_SECRET", "your-secret-here")

# Store for background processing (in production, use a queue)
pending_tasks = []

@app.post("/api/receive-task")
async def receive_task(request: Request):
    """
    Main endpoint that receives task requests from instructors
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ["email", "secret", "task", "round", "nonce", "brief", "checks", "evaluation_url"]
        for field in required_fields:
            if field not in data:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Missing required field: {field}"}
                )
        
        # Verify secret
        if data["secret"] != YOUR_SECRET:
            return JSONResponse(
                status_code=403,
                content={"error": "Invalid secret"}
            )
        
        # Log the task
        print(f"[{datetime.now()}] Received task: {data['task']} Round {data['round']}")
        print(f"Brief: {data['brief']}")
        
        # Add to pending tasks (in production, use a proper queue/database)
        pending_tasks.append(data)
        
        # Trigger background processing
        asyncio.create_task(process_task(data))
        
        # Return 200 immediately
        return JSONResponse(
            status_code=200,
            content={"status": "accepted", "task": data["task"], "round": data["round"]}
        )
        
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON"}
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

async def process_task(task_data):
    """
    Background task processor
    This should be called after returning 200 to the instructor
    """
    try:
        # Import here to avoid loading heavy modules on every request
        from builder import build_and_deploy
        
        print(f"Starting background processing for task: {task_data['task']}")
        
        # Build and deploy the app
        result = await build_and_deploy(task_data)
        
        print(f"Task {task_data['task']} completed: {result}")
        
    except Exception as e:
        print(f"Background processing error: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pending_tasks": len(pending_tasks),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Student API Endpoint - Ready to receive tasks",
        "endpoints": {
            "receive_task": "/api/receive-task",
            "health": "/api/health"
        }
    }

# Vercel serverless handler
handler = app

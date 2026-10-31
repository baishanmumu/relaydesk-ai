from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import uuid
import os
import sys

# Add the relaydesk directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from relaydesk.app.services.chat_service import process_user_message
from .core.user_data_manager import (
    get_user_session, 
    update_user_chat_history, 
    get_pending_action, 
    get_operation_log,
    delete_user_session,
)

# Load environment variables
load_dotenv()

app = FastAPI(title="RelayDesk AI", version="0.1.0")

# Set up Jinja2 templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

class ChatMessage(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

def get_session_data(request: Request):
    """Get or create session data for the current user."""
    raw_session_id = request.cookies.get("session_id", "")
    try:
        session_id = str(uuid.UUID(raw_session_id))
    except (ValueError, AttributeError):
        session_id = str(uuid.uuid4())
    
    # Get the user session data
    session_data = get_user_session(session_id)
    
    # Ensure config exists in session_data
    if "config" not in session_data:
        session_data["config"] = {
            "thread_id": session_id,
            "passenger_id": os.environ.get("DEMO_PASSENGER_ID", ""),
        }
    
    return {
        "session_id": session_id,
        "config": session_data["config"],
        "user_data": session_data
    }


def set_session_cookie(response, session_id: str):
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request, session_data: dict = Depends(get_session_data)):
    """Serve the chat interface."""
    # Set the session cookie
    response = templates.TemplateResponse("chat.html", {
        "request": request, 
        "session_id": session_data["session_id"],
        "chat_history": session_data["user_data"].get("chat_history", [])
    })
    set_session_cookie(response, session_data["session_id"])
    return response


@app.post("/reset-session")
async def reset_session(session_data: dict = Depends(get_session_data)):
    """Clear the caller's saved chat and issue a fresh conversation ID."""
    delete_user_session(session_data["session_id"])
    new_session_id = str(uuid.uuid4())
    response = JSONResponse(content={"response": "已开始新对话。"})
    set_session_cookie(response, new_session_id)
    return response

@app.post("/chat")
async def chat(chat_message: ChatMessage, session_data: dict = Depends(get_session_data)):
    """Process a chat message and return the AI response."""
    try:
        # Process the user message
        ai_response = await process_user_message(session_data, chat_message.message)
        
        # Update the user's chat history
        update_user_chat_history(session_data["session_id"], chat_message.message, ai_response)
        
        # Return the AI response
        return JSONResponse(content={"response": ai_response})
        
    except Exception as e:
        print(f"Chat request failed ({type(e).__name__}).")
        # Return a user-friendly error message
        return JSONResponse(content={"error": "An unexpected error occurred. Please try again later."}, status_code=500)

# HITL (Human-in-the-Loop) endpoints

@app.get("/pending-action")
async def get_pending_action_endpoint(session_data: dict = Depends(get_session_data)):
    """Check if there is a pending action requiring user approval."""
    try:
        pending_action = get_pending_action(session_data["session_id"])
        if pending_action:
            return JSONResponse(content={"pending_action": pending_action})
        else:
            return JSONResponse(content={"pending_action": None})
    except Exception as e:
        print(f"Pending action check failed ({type(e).__name__}).")
        return JSONResponse(content={"error": "An unexpected error occurred. Please try again later."}, status_code=500)


@app.post("/approve-action")
async def approve_action(request: Request, session_data: dict = Depends(get_session_data)):
    """Approve a pending action."""
    if not get_pending_action(session_data["session_id"]):
        return JSONResponse(content={"error": "没有等待确认的操作。"}, status_code=409)
    try:
        # Process the user's approval decision
        from relaydesk.app.services.chat_service import process_user_decision
        ai_response = await process_user_decision(session_data, "approve")
        
        # Update the user's chat history
        update_user_chat_history(session_data["session_id"], "[User approved action]", ai_response)
        
        # Return the AI response
        return JSONResponse(content={"response": ai_response})
        
    except Exception as e:
        # Log the error for debugging
        print(f"Approval request failed ({type(e).__name__}).")
        # Return a user-friendly error message
        return JSONResponse(content={"error": "An unexpected error occurred. Please try again later."}, status_code=500)


@app.post("/reject-action")
async def reject_action(request: Request, session_data: dict = Depends(get_session_data)):
    """Reject a pending action."""
    if not get_pending_action(session_data["session_id"]):
        return JSONResponse(content={"error": "没有等待确认的操作。"}, status_code=409)
    try:
        # Process the user's rejection decision
        from relaydesk.app.services.chat_service import process_user_decision
        ai_response = await process_user_decision(session_data, "reject")
        
        # Update the user's chat history
        update_user_chat_history(session_data["session_id"], "[User rejected action]", ai_response)
        
        # Return the AI response
        return JSONResponse(content={"response": ai_response})
        
    except Exception as e:
        # Log the error for debugging
        print(f"Rejection request failed ({type(e).__name__}).")
        # Return a user-friendly error message
        return JSONResponse(content={"error": "An unexpected error occurred. Please try again later."}, status_code=500)

@app.get("/operation-log")
async def get_operation_log_endpoint(session_data: dict = Depends(get_session_data)):
    """Get the operation log for the current session."""
    try:
        # Get only the most recent 20 log entries to reduce data transfer
        operation_log = get_operation_log(session_data["session_id"], limit=20)
        return JSONResponse(content={"operation_log": operation_log})
    except Exception as e:
        print(f"Operation log retrieval failed ({type(e).__name__}).")
        return JSONResponse(content={"error": "An unexpected error occurred. Please try again later."}, status_code=500)

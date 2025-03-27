from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import threading
# Import the function from your original file
from main import make_vapi_call
from supabase_general import schedule

app = FastAPI(title="VAPI Call API", description="API for making automated voice calls")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define request model
class CallRequest(BaseModel):
    name: str
    phone: str
    email: str 
    countryCode: str # Added contact_id field
    call_id: str


# Define response models
class CallResponse(BaseModel):
    id: Optional[str] = None
    status: Optional[str] = None
    customer: Optional[dict] = None
    created_at: Optional[str] = None
    error: Optional[str] = None

def run_scheduler():
    thread = threading.Thread(target=schedule, daemon=True)
    thread.start()

@app.on_event("startup")
async def startup_event():
    run_scheduler()

@app.post("/doctor", response_model=CallResponse)
async def api_make_call(call_request: CallRequest = Body(...)):
    """
    Make an outbound phone call using VAPI.ai
    
    - **name**: Name of the person to call
    - **number**: Phone number to call (with country code)
    - **mail**: Email address for notifications
    - **contact_id**: Optional Supabase contact ID
    """
    number=call_request.countryCode + call_request.phone
    try:
        result = make_vapi_call(call_request.name, number, call_request.email, call_request.call_id)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
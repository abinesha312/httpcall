"""FastAPI application for httpcall."""

import uuid
from datetime import datetime, timedelta
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.twiml.voice_response import VoiceResponse, Dial

from httpcall.config import get_settings
from httpcall.validation import validate_e164


app = FastAPI(
    title="httpcall",
    description="Clone-and-run internet phone app using Twilio Voice",
    version="0.1.0"
)


def _get_settings():
    """Get settings instance (lazy loading for testing)."""
    return get_settings()


class TokenRequest(BaseModel):
    """Request model for token endpoint."""
    identity: str | None = None


class CallRequest(BaseModel):
    """Request model for initiating a call."""
    to: str


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main application page."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>httpcall - Internet Phone</title>
    <script src="https://sdk.twilio.com/js/client/releases/1.14/twilio.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 500px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            font-size: 32px;
            margin-bottom: 8px;
            text-align: center;
        }
        
        .subtitle {
            color: #666;
            font-size: 14px;
            text-align: center;
            margin-bottom: 32px;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            color: #555;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.2s;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .button-group {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }
        
        button {
            flex: 1;
            padding: 14px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-call {
            background: #667eea;
            color: white;
        }
        
        .btn-call:hover:not(:disabled) {
            background: #5568d3;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn-hangup {
            background: #ef4444;
            color: white;
        }
        
        .btn-hangup:hover:not(:disabled) {
            background: #dc2626;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
        }
        
        .status {
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            text-align: center;
            margin-bottom: 20px;
            font-weight: 500;
        }
        
        .status.idle {
            background: #f3f4f6;
            color: #6b7280;
        }
        
        .status.connecting {
            background: #fef3c7;
            color: #92400e;
        }
        
        .status.active {
            background: #d1fae5;
            color: #065f46;
        }
        
        .status.error {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .notice {
            background: #fef9e7;
            border-left: 4px solid #f39c12;
            padding: 16px;
            border-radius: 4px;
            font-size: 13px;
            color: #7d6608;
            line-height: 1.5;
        }
        
        .notice strong {
            display: block;
            margin-bottom: 4px;
            color: #7d6608;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📞 httpcall</h1>
        <p class="subtitle">Internet phone using Twilio Voice</p>
        
        <div class="input-group">
            <label for="phoneNumber">Phone Number (E.164 format)</label>
            <input 
                type="text" 
                id="phoneNumber" 
                placeholder="+12345678900"
                value="+1"
            >
        </div>
        
        <div class="status idle" id="status">Ready to call</div>
        
        <div class="button-group">
            <button class="btn-call" id="callBtn" onclick="makeCall()">Call</button>
            <button class="btn-hangup" id="hangupBtn" onclick="hangUp()" disabled>Hang Up</button>
        </div>
        
        <div class="notice">
            <strong>⚠️ Important:</strong>
            This app uses your Twilio account. Calls are billed per minute. 
            Trial accounts can only call verified numbers. 
            You are responsible for ensuring compliance with applicable laws.
        </div>
    </div>
    
    <script>
        let device;
        let currentCall;
        
        const statusEl = document.getElementById('status');
        const callBtn = document.getElementById('callBtn');
        const hangupBtn = document.getElementById('hangupBtn');
        const phoneInput = document.getElementById('phoneNumber');
        
        function setStatus(message, type = 'idle') {
            statusEl.textContent = message;
            statusEl.className = `status ${type}`;
        }
        
        async function initializeDevice() {
            try {
                const response = await fetch('/token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
                
                if (!response.ok) {
                    throw new Error('Failed to get access token');
                }
                
                const data = await response.json();
                device = new Twilio.Device(data.token);
                
                device.on('ready', () => {
                    setStatus('Ready to call', 'idle');
                });
                
                device.on('error', (error) => {
                    console.error('Device error:', error);
                    setStatus(`Error: ${error.message}`, 'error');
                });
                
                device.on('connect', () => {
                    setStatus('Call connected', 'active');
                    callBtn.disabled = true;
                    hangupBtn.disabled = false;
                });
                
                device.on('disconnect', () => {
                    setStatus('Call ended', 'idle');
                    callBtn.disabled = false;
                    hangupBtn.disabled = true;
                    currentCall = null;
                });
                
            } catch (error) {
                console.error('Initialization error:', error);
                setStatus('Failed to initialize', 'error');
            }
        }
        
        async function makeCall() {
            const phoneNumber = phoneInput.value.trim();
            
            if (!phoneNumber) {
                setStatus('Please enter a phone number', 'error');
                return;
            }
            
            try {
                setStatus('Connecting...', 'connecting');
                callBtn.disabled = true;
                
                currentCall = await device.connect({
                    To: phoneNumber
                });
                
            } catch (error) {
                console.error('Call error:', error);
                setStatus(`Failed to connect: ${error.message}`, 'error');
                callBtn.disabled = false;
            }
        }
        
        function hangUp() {
            if (currentCall) {
                currentCall.disconnect();
            } else if (device) {
                device.disconnectAll();
            }
        }
        
        initializeDevice();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.post("/token")
async def get_token(request: TokenRequest) -> Dict[str, str]:
    """
    Generate a Twilio Access Token for Voice client.
    
    Returns a short-lived token that allows the browser to connect to Twilio
    and make outbound calls.
    """
    try:
        settings = _get_settings()
        identity = request.identity or f"user-{uuid.uuid4()}"
        
        token = AccessToken(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_API_KEY_SID,
            settings.TWILIO_API_KEY_SECRET,
            identity=identity,
            ttl=3600
        )
        
        voice_grant = VoiceGrant(
            outgoing_application_sid=settings.TWILIO_TWIML_APP_SID,
            incoming_allow=False
        )
        token.add_grant(voice_grant)
        
        return {
            "token": token.to_jwt(),
            "identity": identity
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")


@app.post("/voice")
async def voice_webhook(request: Request) -> Response:
    """
    TwiML webhook for handling outbound calls.
    
    Twilio calls this endpoint when a call is initiated from the browser.
    It returns TwiML instructions to dial the requested number.
    
    The caller ID is always TWILIO_FROM_NUMBER (no spoofing allowed).
    """
    try:
        settings = _get_settings()
        form_data = await request.form()
        to_number = form_data.get("To", "").strip()
        
        is_valid, error_message = validate_e164(to_number)
        if not is_valid:
            response = VoiceResponse()
            response.say(f"Invalid phone number: {error_message}")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")
        
        response = VoiceResponse()
        dial = Dial(
            caller_id=settings.TWILIO_FROM_NUMBER,
            timeout=30,
            action=f"{settings.PUBLIC_BASE_URL}/voice/status"
        )
        dial.number(to_number)
        response.append(dial)
        
        return Response(content=str(response), media_type="application/xml")
        
    except Exception as e:
        response = VoiceResponse()
        response.say("An error occurred. Please try again later.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")


@app.post("/voice/status")
async def voice_status(request: Request) -> Response:
    """
    Optional callback for call status updates.
    
    This endpoint can be used to handle call completion events.
    """
    response = VoiceResponse()
    response.hangup()
    return Response(content=str(response), media_type="application/xml")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "httpcall"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

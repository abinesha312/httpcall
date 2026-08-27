# httpcall

Clone, run, type a number, call over the internet.

A simple internet phone app using [Twilio Voice](https://www.twilio.com/voice) and WebRTC. Type any E.164 phone number, click Call, and talk through your browser microphone and speaker.

**⚠️ Important Limits:**
- **Not free.** Twilio bills per minute. Check [Twilio pricing](https://www.twilio.com/voice/pricing).
- **Not a robocaller / autodialer / SMS blaster.** This is a simple single-call app for legitimate phone calls.
- **Not caller-ID spoofing.** The caller ID is always your purchased Twilio number.
- **US/TCPA compliance.** You are responsible for ensuring you have consent to call recipients and comply with all applicable laws.
- **Twilio trial accounts** can only call verified numbers until you upgrade your account.

## Quick Start

### Prerequisites

- Python 3.8 or later
- A [Twilio account](https://www.twilio.com/try-twilio) (free trial available)
- [ngrok](https://ngrok.com/) for local development (free)

### 1. Twilio Console Setup

#### a. Get Your Account Credentials

1. Go to [Twilio Console](https://console.twilio.com)
2. Copy your **Account SID** and **Auth Token**

#### b. Create an API Key

1. Go to [API Keys](https://console.twilio.com/project/api-keys)
2. Click **Create API Key**
3. Give it a name (e.g., "httpcall")
4. Copy the **SID** and **Secret** (you won't see the secret again!)

#### c. Buy a Phone Number

1. Go to [Phone Numbers → Buy a Number](https://console.twilio.com/develop/phone-numbers/manage/search)
2. Search for a number with **Voice** capability
3. Purchase the number
4. Copy the phone number (e.g., `+15551234567`)

#### d. Create a TwiML Application

1. Go to [TwiML Apps](https://console.twilio.com/develop/voice/manage/twiml-apps)
2. Click **Create new TwiML App**
3. Give it a name (e.g., "httpcall")
4. Leave the Voice URL empty for now (we'll update it after starting ngrok)
5. Save and copy the **Application SID**

### 2. Clone and Install

```bash
git clone https://github.com/abinesha312/httpcall.git
cd httpcall
pip install -e .
```

### 3. Configure Environment

Copy the example environment file and fill in your Twilio credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_API_KEY_SID=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_KEY_SECRET=your_api_key_secret_here
TWILIO_TWIML_APP_SID=APxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+15551234567
PUBLIC_BASE_URL=https://your-ngrok-url.ngrok.io
```

### 4. Start ngrok

In a new terminal, start ngrok to expose your local server:

```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`) and:

1. Update `PUBLIC_BASE_URL` in your `.env` file
2. Go back to your [TwiML App settings](https://console.twilio.com/develop/voice/manage/twiml-apps)
3. Set the **Voice Request URL** to `https://abc123.ngrok.io/voice`
4. Set the HTTP method to **POST**
5. Save

### 5. Run the App

```bash
uvicorn httpcall.app:app --host 0.0.0.0 --port 8000
```

### 6. Make a Call

1. Open http://localhost:8000 in your browser
2. Type a phone number in E.164 format (e.g., `+12025551234`)
3. Click **Call**
4. Talk through your browser microphone and speaker
5. Click **Hang Up** when done

## Development

### Install with dev dependencies

```bash
pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Run tests with coverage

```bash
pytest --cov=httpcall --cov-report=term-missing
```

## How It Works

1. **Frontend:** Single-page HTML/JavaScript app using the [Twilio Voice JS SDK](https://www.twilio.com/docs/voice/sdks/javascript)
2. **Backend:** Python FastAPI server with three endpoints:
   - `GET /` - Serves the UI
   - `POST /token` - Issues short-lived Twilio Access Tokens for WebRTC
   - `POST /voice` - TwiML webhook that Twilio calls to get dial instructions
3. **Security:**
   - E.164 phone number validation
   - Basic premium-rate number blocking
   - Caller ID is always your purchased Twilio number (no spoofing)
   - Short-lived access tokens (1 hour TTL)

## Architecture

```
┌─────────────┐                  ┌─────────────┐                ┌─────────────┐
│   Browser   │ ◄─── WebRTC ───► │   Twilio    │ ◄─── PSTN ───► │   Phone     │
│  (Your PC)  │                  │   Servers   │                │  (Anyone)   │
└─────────────┘                  └─────────────┘                └─────────────┘
       │                                  │
       │                                  │
       ▼                                  ▼
┌─────────────────────────────────────────────┐
│        FastAPI Server (localhost)           │
│  • GET /token → Issue access token          │
│  • POST /voice → Return TwiML dial          │
└─────────────────────────────────────────────┘
```

## API Endpoints

### `GET /`

Serves the single-page application UI.

### `POST /token`

Issues a Twilio Access Token for the browser client.

**Request:**
```json
{
  "identity": "optional-user-id"
}
```

**Response:**
```json
{
  "token": "eyJ...",
  "identity": "user-12345"
}
```

### `POST /voice`

TwiML webhook called by Twilio when initiating a call.

**Request:** Form data from Twilio with `To` parameter

**Response:** TwiML XML
```xml
<Response>
  <Dial callerId="+15551234567" timeout="30">
    <Number>+12025551234</Number>
  </Dial>
</Response>
```

## Security Considerations

- **Environment variables:** All secrets are loaded from environment variables, never hardcoded
- **E.164 validation:** Phone numbers must be valid E.164 format
- **Premium rate blocking:** Basic detection and blocking of common premium rate patterns
- **No caller ID spoofing:** The `callerId` is always `TWILIO_FROM_NUMBER`
- **One call at a time:** The UI manages a single call per browser session
- **Token TTL:** Access tokens expire after 1 hour

## Troubleshooting

### "Failed to initialize" error

- Check that all environment variables in `.env` are correct
- Ensure your Twilio account is active and credentials are valid

### "Failed to connect" error

- Ensure ngrok is running and the URL in `.env` matches the ngrok URL
- Verify the TwiML App's Voice Request URL is set correctly
- Check that you're using a valid E.164 phone number

### "Trial account" limitations

- Trial accounts can only call verified numbers
- Upgrade your Twilio account to call any number
- See [Twilio trial account limitations](https://www.twilio.com/docs/usage/tutorials/how-to-use-your-free-trial-account)

### "Invalid phone number" error

- Phone numbers must be in E.164 format: `+[country code][number]`
- Example US: `+12025551234`
- Example UK: `+442071234567`

## Cost Considerations

Twilio charges for:
- **Phone number rental:** ~$1/month
- **Outbound calls:** Varies by destination (US: ~$0.013/min)
- **Inbound calls:** Not used by this app

See [Twilio Voice pricing](https://www.twilio.com/voice/pricing) for details.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

This is a simple demonstration app. Feel free to fork and customize for your needs.

## Disclaimer

This app is provided as-is for educational and legitimate personal use. Users are responsible for:
- Complying with all applicable laws and regulations (TCPA, GDPR, etc.)
- Obtaining proper consent before calling recipients
- Monitoring and paying for Twilio usage costs
- Not using this for spam, harassment, or illegal purposes

The authors are not responsible for any misuse of this software.

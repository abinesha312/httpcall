"""Tests for FastAPI application."""

import os
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from httpcall.app import app


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    from httpcall.config import Settings
    
    mock_settings_obj = Settings(
        TWILIO_ACCOUNT_SID="ACtest123",
        TWILIO_AUTH_TOKEN="test_token_123",
        TWILIO_API_KEY_SID="SKtest123",
        TWILIO_API_KEY_SECRET="test_secret_123",
        TWILIO_TWIML_APP_SID="APtest123",
        TWILIO_FROM_NUMBER="+15551234567",
        PUBLIC_BASE_URL="https://example.ngrok.io",
    )
    
    with patch('httpcall.app._get_settings', return_value=mock_settings_obj):
        yield mock_settings_obj


@pytest.fixture
def client(mock_settings):
    """Create test client."""
    return TestClient(app)


class TestIndexEndpoint:
    """Tests for the index endpoint."""
    
    def test_index_returns_html(self, client):
        """Test that index returns HTML page."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "httpcall" in response.text
        assert "Twilio" in response.text
    
    def test_index_includes_twilio_sdk(self, client):
        """Test that index includes Twilio JS SDK."""
        response = client.get("/")
        assert "twilio.min.js" in response.text
    
    def test_index_includes_call_button(self, client):
        """Test that index includes call controls."""
        response = client.get("/")
        assert "makeCall" in response.text
        assert "hangUp" in response.text


class TestTokenEndpoint:
    """Tests for the /token endpoint."""
    
    @patch('httpcall.app.AccessToken')
    def test_token_generation_success(self, mock_access_token, client):
        """Test successful token generation."""
        mock_token_instance = Mock()
        mock_token_instance.to_jwt.return_value = "test.jwt.token"
        mock_access_token.return_value = mock_token_instance
        
        response = client.post("/token", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "identity" in data
        assert data["token"] == "test.jwt.token"
    
    @patch('httpcall.app.AccessToken')
    def test_token_with_custom_identity(self, mock_access_token, client):
        """Test token generation with custom identity."""
        mock_token_instance = Mock()
        mock_token_instance.to_jwt.return_value = "test.jwt.token"
        mock_access_token.return_value = mock_token_instance
        
        response = client.post("/token", json={"identity": "custom-user-123"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["identity"] == "custom-user-123"
    
    @patch('httpcall.app.AccessToken')
    def test_token_without_identity(self, mock_access_token, client):
        """Test token generation auto-generates identity."""
        mock_token_instance = Mock()
        mock_token_instance.to_jwt.return_value = "test.jwt.token"
        mock_access_token.return_value = mock_token_instance
        
        response = client.post("/token", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert "user-" in data["identity"]


class TestVoiceWebhook:
    """Tests for the /voice webhook endpoint."""
    
    def test_voice_webhook_valid_number(self, client):
        """Test voice webhook with valid E.164 number."""
        response = client.post(
            "/voice",
            data={"To": "+12025551234"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "<Dial" in response.text
        assert "+12025551234" in response.text
        assert "+15551234567" in response.text  # caller_id (from env)
    
    def test_voice_webhook_invalid_number_no_plus(self, client):
        """Test voice webhook rejects number without +."""
        response = client.post(
            "/voice",
            data={"To": "12025551234"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        assert "<Say>" in response.text
        assert "Invalid phone number" in response.text
        assert "<Hangup" in response.text
    
    def test_voice_webhook_empty_number(self, client):
        """Test voice webhook rejects empty number."""
        response = client.post(
            "/voice",
            data={"To": ""},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        assert "<Say>" in response.text
        assert "Invalid" in response.text
    
    def test_voice_webhook_premium_number(self, client):
        """Test voice webhook rejects premium rate number."""
        response = client.post(
            "/voice",
            data={"To": "+19005551234"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        assert "<Say>" in response.text
        assert "Premium rate" in response.text
    
    def test_voice_webhook_uses_configured_caller_id(self, client):
        """Test that webhook uses configured TWILIO_FROM_NUMBER as caller ID."""
        response = client.post(
            "/voice",
            data={"To": "+12025551234"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        assert 'callerId="+15551234567"' in response.text
    
    def test_voice_webhook_number_too_short(self, client):
        """Test voice webhook rejects too-short number."""
        response = client.post(
            "/voice",
            data={"To": "+123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        assert "<Say>" in response.text
        assert "too short" in response.text.lower()
    
    def test_voice_webhook_number_too_long(self, client):
        """Test voice webhook rejects too-long number."""
        response = client.post(
            "/voice",
            data={"To": "+1234567890123456"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        assert "<Say>" in response.text
        assert "too long" in response.text.lower()


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "httpcall"

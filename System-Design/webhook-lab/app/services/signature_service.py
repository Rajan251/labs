"""
HMAC signature service for webhook security.

Provides utilities for generating and verifying HMAC-SHA256 signatures
to ensure webhook authenticity and integrity.
"""
import hmac
import hashlib
import json
from typing import Dict, Any


class SignatureService:
    """Service for generating and verifying webhook signatures."""
    
    @staticmethod
    def generate_signature(payload: Dict[str, Any], secret_key: str) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload.
        
        Args:
            payload: Event payload dictionary
            secret_key: Tenant's secret key
            
        Returns:
            Hex-encoded HMAC signature
            
        Example:
            signature = SignatureService.generate_signature(
                {"event": "user.created", "data": {...}},
                "tenant_secret_key"
            )
            # Returns: "a1b2c3d4e5f6..."
        """
        # Convert payload to JSON string with sorted keys for consistency
        payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def verify_signature(
        payload: Dict[str, Any],
        signature: str,
        secret_key: str
    ) -> bool:
        """
        Verify HMAC-SHA256 signature for webhook payload.
        
        Args:
            payload: Event payload dictionary
            signature: Signature to verify
            secret_key: Tenant's secret key
            
        Returns:
            True if signature is valid, False otherwise
            
        Example:
            is_valid = SignatureService.verify_signature(
                {"event": "user.created"},
                "a1b2c3d4e5f6...",
                "tenant_secret_key"
            )
        """
        expected_signature = SignatureService.generate_signature(payload, secret_key)
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def create_signature_header(signature: str) -> str:
        """
        Create signature header value in standard format.
        
        Args:
            signature: HMAC signature
            
        Returns:
            Formatted signature header (e.g., "sha256=a1b2c3...")
        """
        return f"sha256={signature}"
    
    @staticmethod
    def parse_signature_header(header: str) -> str:
        """
        Parse signature from header value.
        
        Args:
            header: Signature header value (e.g., "sha256=a1b2c3...")
            
        Returns:
            Extracted signature
            
        Raises:
            ValueError: If header format is invalid
        """
        if not header.startswith("sha256="):
            raise ValueError("Invalid signature header format")
        
        return header[7:]  # Remove "sha256=" prefix

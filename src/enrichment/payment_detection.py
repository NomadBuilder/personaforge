"""Payment processor detection module."""

import requests
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Import Config with fallback
try:
    from src.utils.config import Config
except ImportError:
    class Config:
        API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "10"))


def detect_payment_processors(domain: str) -> List[str]:
    """Detect payment processors used by a domain."""
    processors = []
    
    # Known payment processor indicators
    payment_indicators = {
        "stripe": ["stripe.com", "js.stripe.com", "checkout.stripe.com"],
        "paypal": ["paypal.com", "paypalobjects.com"],
        "square": ["square.com", "squareup.com"],
        "braintree": ["braintreegateway.com"],
        "coinbase": ["coinbase.com", "commerce.coinbase.com"],
        "bitpay": ["bitpay.com"],
        "crypto": ["crypto.com", "binance.com", "bitcoin.org"]
    }
    
    try:
        url = f"http://{domain}" if not domain.startswith("http") else domain
        response = requests.get(url, timeout=Config.API_TIMEOUT_SECONDS, allow_redirects=True)
        
        content = response.text.lower()
        
        # Check for payment processor references in HTML
        for processor, indicators in payment_indicators.items():
            for indicator in indicators:
                if indicator in content:
                    if processor not in processors:
                        processors.append(processor)
        
        # Check for common payment button classes/IDs
        payment_patterns = [
            "paypal-button",
            "stripe-button",
            "checkout-button",
            "payment-button"
        ]
        
        for pattern in payment_patterns:
            if pattern in content:
                if "unknown" not in processors:
                    processors.append("unknown")
    
    except Exception as e:
        print(f"Payment processor detection failed for {domain}: {e}")
    
    return processors


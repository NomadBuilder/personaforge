"""Tests for vendor detection."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.enrichment.vendor_detection import (
    detect_vendor_type,
    extract_vendor_name,
    calculate_vendor_risk_score
)


def test_detect_vendor_type_synthetic_identity():
    """Test detection of synthetic identity vendors."""
    domain = "fake-identity-kits.com"
    enrichment = {}
    
    vendor_type = detect_vendor_type(domain, enrichment)
    assert vendor_type == "synthetic_identity"


def test_detect_vendor_type_deepfake():
    """Test detection of deepfake vendors."""
    domain = "deepfake-voice-clone.com"
    enrichment = {}
    
    vendor_type = detect_vendor_type(domain, enrichment)
    assert vendor_type == "deepfake"


def test_extract_vendor_name():
    """Test vendor name extraction."""
    domain = "example-identity-shop.com"
    enrichment = {}
    
    vendor_name = extract_vendor_name(domain, enrichment)
    assert vendor_name is not None
    assert len(vendor_name) > 0


def test_calculate_risk_score():
    """Test risk score calculation."""
    domain = "fake-identity.com"
    enrichment = {
        "payment_processor": "crypto, bitcoin",
        "isp": "offshore hosting"
    }
    
    score = calculate_vendor_risk_score(domain, enrichment)
    assert 0 <= score <= 100
    assert score > 0  # Should have some risk indicators


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


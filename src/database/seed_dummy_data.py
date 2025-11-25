"""
DUMMY DATA SEEDER - FOR VISUALIZATION TESTING ONLY

⚠️⚠️⚠️ WARNING: THIS IS DUMMY/TEST DATA ⚠️⚠️⚠️
This file contains FAKE/SYNTHETIC data for testing visualizations.
DO NOT use this data for any real analysis or reporting.
This data should be REMOVED before production use.

To remove all dummy data, run:
    DELETE FROM domains WHERE source = 'DUMMY_DATA_FOR_TESTING';
    DELETE FROM domain_enrichment WHERE domain_id IN (
        SELECT id FROM domains WHERE source = 'DUMMY_DATA_FOR_TESTING'
    );
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List
from src.database.postgres_client import PostgresClient
from src.utils.logger import logger


# ⚠️ DUMMY DATA - DO NOT USE FOR REAL ANALYSIS ⚠️
DUMMY_VENDOR_DOMAINS = [
    # Synthetic Identity Vendors
    "fakeidpro.com", "syntheticidkit.net", "personapack.io", "identityforge.com",
    "fakeidvendor.org", "syntheticdocs.com", "personakit.shop", "idmaker.pro",
    "fakeidstore.net", "syntheticid.co", "personapack.store", "identitykit.io",
    
    # Deepfake Services
    "deepfakeservice.net", "faceclone.ai", "voiceforge.com", "deepfakepro.io",
    "face-swap.pro", "voiceclone.shop", "deepfakekit.com", "impersonate.ai",
    "faceforge.net", "voiceforge.io", "deepfake.store", "cloneface.com",
    
    # KYC Bypass Services
    "kycbypass.pro", "verification-bypass.com", "kycforge.io", "verify-bypass.net",
    "kycskip.com", "verificationkit.io", "kyc-bypass.shop", "verifyforge.com",
    
    # Document Forgers
    "docforge.com", "passportmaker.pro", "licenseforge.io", "documentkit.net",
    "passportgen.com", "licensegen.io", "docmaker.pro", "passportforge.net",
]

# ⚠️ DUMMY DATA - FAKE INFRASTRUCTURE DATA ⚠️
DUMMY_HOSTING_PROVIDERS = [
    "Bulletproof Hosting LLC", "Offshore Hosting Pro", "Anonymous Hosting",
    "Privacy Hosting", "Secure Hosting Inc", "Private Hosting Co"
]

DUMMY_REGISTRARS = [
    "Privacy Registrar Inc", "Anonymous Domains", "Offshore Registrar",
    "Private Domain Co", "Secure Registrar LLC"
]

DUMMY_PAYMENT_PROCESSORS = [
    "Bitcoin", "Monero", "Ethereum", "CryptoPay", "Anonymous Payment",
    "Privacy Payment", "Offshore Payment Gateway"
]

DUMMY_CDNS = [
    "Cloudflare", "Fastly", "Akamai", "Private CDN", "Anonymous CDN"
]


# Infrastructure groups for creating larger clusters
# Each group will be assigned to multiple domains to create clusters of 3-8 domains
INFRASTRUCTURE_GROUPS = [
    {
        "host": "Bulletproof Hosting LLC",
        "registrar": "Privacy Registrar Inc",
        "cdn": "Cloudflare",
        "payment": "Bitcoin"
    },
    {
        "host": "Offshore Hosting Pro",
        "registrar": "Anonymous Domains",
        "cdn": "Private CDN",
        "payment": "Monero"
    },
    {
        "host": "Anonymous Hosting",
        "registrar": "Offshore Registrar",
        "cdn": "Anonymous CDN",
        "payment": "Ethereum"
    },
    {
        "host": "Privacy Hosting",
        "registrar": "Private Domain Co",
        "cdn": "Fastly",
        "payment": "CryptoPay"
    },
    {
        "host": "Secure Hosting Inc",
        "registrar": "Secure Registrar LLC",
        "cdn": "Akamai",
        "payment": "Anonymous Payment"
    },
    {
        "host": "Private Hosting Co",
        "registrar": "Privacy Registrar Inc",
        "cdn": "Cloudflare",
        "payment": "Bitcoin"
    },
    {
        "host": "Bulletproof Hosting LLC",
        "registrar": "Anonymous Domains",
        "cdn": "Private CDN",
        "payment": "Monero"
    },
    {
        "host": "Offshore Hosting Pro",
        "registrar": "Secure Registrar LLC",
        "cdn": "Anonymous CDN",
        "payment": "Ethereum"
    }
]

def generate_dummy_enrichment_data(domain: str, vendor_type: str = None, infrastructure_group: Dict = None) -> Dict:
    """
    ⚠️ DUMMY DATA GENERATOR - FOR TESTING ONLY ⚠️
    Generates fake enrichment data for visualization testing.
    
    Args:
        domain: Domain name
        vendor_type: Optional vendor type
        infrastructure_group: Optional infrastructure group dict to create clusters
    """
    # Determine vendor type from domain if not provided
    if not vendor_type:
        if any(kw in domain.lower() for kw in ['deepfake', 'face', 'voice', 'clone']):
            vendor_type = 'deepfake'
        elif any(kw in domain.lower() for kw in ['kyc', 'verify', 'bypass']):
            vendor_type = 'kyc_bypass'
        elif any(kw in domain.lower() for kw in ['doc', 'passport', 'license']):
            vendor_type = 'document_forger'
        else:
            vendor_type = 'synthetic_identity'
    
    # Generate random but realistic-looking data
    # ⚠️ DUMMY DATA - Higher risk scores for visualization testing
    if any(kw in domain.lower() for kw in ['fake', 'deepfake', 'synthetic', 'clone']):
        risk_score = random.randint(60, 95)  # High risk for obvious vendor keywords
    elif any(kw in domain.lower() for kw in ['id', 'persona', 'doc', 'passport', 'kyc']):
        risk_score = random.randint(40, 75)  # Medium-high risk
    else:
        risk_score = random.randint(20, 50)  # Lower risk
    
    # Random dates
    days_ago = random.randint(30, 1000)
    creation_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    
    # Use infrastructure group if provided, otherwise random (for backward compatibility)
    if infrastructure_group:
        host_name = infrastructure_group.get("host")
        registrar = infrastructure_group.get("registrar")
        cdn = infrastructure_group.get("cdn")
        payment_processor = infrastructure_group.get("payment")
    else:
        host_name = random.choice(DUMMY_HOSTING_PROVIDERS)
        registrar = random.choice(DUMMY_REGISTRARS)
        cdn = random.choice(DUMMY_CDNS) if random.random() > 0.3 else None
        payment_processor = random.choice(DUMMY_PAYMENT_PROCESSORS) if random.random() > 0.4 else None
    
    return {
        "domain": domain,
        "ip_address": f"{random.randint(100, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "host_name": host_name,
        "registrar": registrar,
        "isp": host_name,  # Use same as host for consistency
        "cdn": cdn,
        "payment_processor": payment_processor,
        "cms": random.choice(["WordPress", "Custom", "Shopify", None]),
        "creation_date": creation_date,
        "vendor_type": vendor_type,
        "vendor_risk_score": risk_score,
        "vendor_name": domain.split('.')[0].capitalize(),
        "asn": f"AS{random.randint(10000, 99999)}",
        "country": random.choice(["US", "NL", "RU", "SG", "CH", "DE", "GB"]),
        "city": random.choice(["Amsterdam", "Moscow", "Singapore", "Zurich", "London", "New York"]),
    }


def seed_dummy_data(num_domains: int = 50) -> int:
    """
    ⚠️ DUMMY DATA SEEDER - FOR VISUALIZATION TESTING ONLY ⚠️
    Seeds the database with fake vendor data for testing visualizations.
    
    Args:
        num_domains: Number of dummy domains to create
        
    Returns:
        Number of domains successfully seeded
        
    WARNING: This creates FAKE data. Remove with:
        DELETE FROM domains WHERE source = 'DUMMY_DATA_FOR_TESTING';
    """
    logger.warning("⚠️ SEEDING DUMMY DATA - FOR TESTING ONLY ⚠️")
    
    client = PostgresClient()
    if not client or not client.conn:
        logger.error("Cannot seed dummy data - PostgreSQL not connected")
        return 0
    
    # Get existing domains to avoid duplicates
    existing = client.get_all_enriched_domains()
    existing_domains = {d.get('domain') for d in existing if d.get('domain')}
    
    # Select domains to seed (avoid duplicates)
    domains_to_seed = [d for d in DUMMY_VENDOR_DOMAINS if d not in existing_domains][:num_domains]
    
    if not domains_to_seed:
        logger.warning("All dummy domains already exist in database")
        return 0
    
    # Assign infrastructure groups to create clusters of 3-8 domains each
    # Each infrastructure group will be used by multiple domains
    group_assignments = {}
    
    # Distribute domains across infrastructure groups
    for i, domain in enumerate(domains_to_seed):
        # Cycle through infrastructure groups, assigning 3-8 domains per group
        group_idx = i % len(INFRASTRUCTURE_GROUPS)
        infra_group = INFRASTRUCTURE_GROUPS[group_idx]
        group_assignments[domain] = infra_group
    
    seeded_count = 0
    
    for domain in domains_to_seed:
        try:
            # Determine vendor type
            vendor_type = None
            if any(kw in domain.lower() for kw in ['deepfake', 'face', 'voice', 'clone']):
                vendor_type = 'deepfake'
            elif any(kw in domain.lower() for kw in ['kyc', 'verify', 'bypass']):
                vendor_type = 'kyc_bypass'
            elif any(kw in domain.lower() for kw in ['doc', 'passport', 'license']):
                vendor_type = 'document_forger'
            else:
                vendor_type = 'synthetic_identity'
            
            # Insert domain with DUMMY_DATA_FOR_TESTING source marker
            domain_id = client.insert_domain(
                domain=domain,
                source="DUMMY_DATA_FOR_TESTING",  # ⚠️ CLEAR MARKER FOR REMOVAL
                notes="⚠️ DUMMY DATA - FOR VISUALIZATION TESTING ONLY - REMOVE BEFORE PRODUCTION",
                vendor_type=vendor_type
            )
            
            # Generate and insert dummy enrichment data with assigned infrastructure group
            infrastructure_group = group_assignments.get(domain)
            enrichment_data = generate_dummy_enrichment_data(domain, vendor_type, infrastructure_group)
            client.insert_enrichment(domain_id, enrichment_data)
            
            seeded_count += 1
            
            if seeded_count % 10 == 0:
                logger.info(f"Seeded {seeded_count} dummy domains...")
                
        except Exception as e:
            logger.error(f"Error seeding dummy domain {domain}: {e}")
            continue
    
    logger.warning(f"⚠️ Seeded {seeded_count} DUMMY domains for testing. REMOVE BEFORE PRODUCTION!")
    logger.warning("⚠️ To remove: DELETE FROM domains WHERE source = 'DUMMY_DATA_FOR_TESTING';")
    
    return seeded_count


def remove_dummy_data() -> int:
    """
    ⚠️ REMOVE DUMMY DATA ⚠️
    Removes all dummy test data from the database.
    
    Returns:
        Number of domains removed
    """
    client = PostgresClient()
    if not client or not client.conn:
        logger.error("Cannot remove dummy data - PostgreSQL not connected")
        return 0
    
    cursor = client.conn.cursor()
    
    try:
        # Count before deletion
        cursor.execute("SELECT COUNT(*) FROM domains WHERE source = 'DUMMY_DATA_FOR_TESTING'")
        count = cursor.fetchone()[0]
        
        # Delete enrichments first (foreign key constraint)
        cursor.execute("""
            DELETE FROM domain_enrichment 
            WHERE domain_id IN (
                SELECT id FROM domains WHERE source = 'DUMMY_DATA_FOR_TESTING'
            )
        """)
        
        # Delete domains
        cursor.execute("DELETE FROM domains WHERE source = 'DUMMY_DATA_FOR_TESTING'")
        
        client.conn.commit()
        
        logger.info(f"✅ Removed {count} dummy domains from database")
        return count
        
    except Exception as e:
        logger.error(f"Error removing dummy data: {e}")
        client.conn.rollback()
        return 0
    finally:
        cursor.close()


if __name__ == "__main__":
    # ⚠️ DUMMY DATA SEEDING - FOR TESTING ONLY ⚠️
    print("⚠️⚠️⚠️ SEEDING DUMMY DATA FOR VISUALIZATION TESTING ⚠️⚠️⚠️")
    print("This will add FAKE data to the database.")
    print("Remove with: python3 -c 'from src.database.seed_dummy_data import remove_dummy_data; remove_dummy_data()'")
    
    count = seed_dummy_data(num_domains=50)
    print(f"\n✅ Seeded {count} dummy domains")
    print("⚠️ REMEMBER TO REMOVE THIS DATA BEFORE PRODUCTION!")


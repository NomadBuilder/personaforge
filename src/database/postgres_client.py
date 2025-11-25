"""PostgreSQL client for storing enriched domain and vendor metadata."""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Import Config after load_dotenv
try:
    from src.utils.config import Config
except ImportError:
    # Fallback if import fails
    class Config:
        POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
        POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
        POSTGRES_USER = os.getenv("POSTGRES_USER", "personaforge_user")
        POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "personaforge123password")
        POSTGRES_DB = os.getenv("POSTGRES_DB", "personaforge")

load_dotenv()


class PostgresClient:
    """Client for interacting with PostgreSQL database for PersonaForge."""
    
    def __init__(self):
        connect_params = {
            "host": Config.POSTGRES_HOST,
            "port": Config.POSTGRES_PORT,
            "user": Config.POSTGRES_USER,
            "password": Config.POSTGRES_PASSWORD,
            "database": Config.POSTGRES_DB
        }
        # Add SSL for Render PostgreSQL (required for external connections)
        if Config.POSTGRES_HOST.endswith(".render.com"):
            connect_params["sslmode"] = "require"
        
        try:
            self.conn = psycopg2.connect(**connect_params)
            self._create_tables()
        except psycopg2.OperationalError as e:
            print(f"⚠️  Could not connect to PostgreSQL: {e}")
            print("   Database will be optional. Start with: docker-compose up -d")
            self.conn = None
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def _ensure_connection(self):
        """Ensure database connection is alive, reconnect if needed."""
        if not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except (psycopg2.OperationalError, psycopg2.InterfaceError, AttributeError):
            print("  ⚠️  Database connection lost, attempting reconnect...")
            try:
                if self.conn:
                    self.conn.close()
            except:
                pass
            
            connect_params = {
                "host": Config.POSTGRES_HOST,
                "port": Config.POSTGRES_PORT,
                "user": Config.POSTGRES_USER,
                "password": Config.POSTGRES_PASSWORD,
                "database": Config.POSTGRES_DB
            }
            if Config.POSTGRES_HOST.endswith(".render.com"):
                connect_params["sslmode"] = "require"
            
            try:
                self.conn = psycopg2.connect(**connect_params)
                return True
            except:
                self.conn = None
                return False
    
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        if not self.conn:
            return
            
        cursor = self.conn.cursor()
        
        # Domains table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS domains (
                id SERIAL PRIMARY KEY,
                domain VARCHAR(255) UNIQUE NOT NULL,
                source VARCHAR(255),
                notes TEXT,
                vendor_type VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Domain enrichment table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS domain_enrichment (
                id SERIAL PRIMARY KEY,
                domain_id INTEGER REFERENCES domains(id),
                ip_address VARCHAR(45),
                ip_addresses JSONB,
                ipv6_addresses JSONB,
                host_name TEXT,
                asn VARCHAR(50),
                isp TEXT,
                cdn TEXT,
                cms TEXT,
                payment_processor TEXT,
                registrar TEXT,
                creation_date DATE,
                expiration_date TEXT,
                updated_date TEXT,
                name_servers JSONB,
                mx_records JSONB,
                whois_status TEXT,
                web_server TEXT,
                frameworks JSONB,
                analytics JSONB,
                languages JSONB,
                tech_stack JSONB,
                http_headers JSONB,
                ssl_info JSONB,
                whois_data JSONB,
                dns_records JSONB,
                enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(domain_id)
            )
        """)
        
        # Vendors table (clustered vendors)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendors (
                id SERIAL PRIMARY KEY,
                vendor_name VARCHAR(255),
                vendor_type VARCHAR(100),
                domain_count INTEGER DEFAULT 0,
                shared_infrastructure JSONB,
                payment_processors JSONB,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cluster_id INTEGER
            )
        """)
        
        # Vendor domains junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendor_domains (
                vendor_id INTEGER REFERENCES vendors(id),
                domain_id INTEGER REFERENCES domains(id),
                PRIMARY KEY (vendor_id, domain_id)
            )
        """)
        
        # Analysis cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_cache (
                id SERIAL PRIMARY KEY,
                analysis_type VARCHAR(50) DEFAULT 'vendor_clusters',
                analysis_data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(analysis_type)
            )
        """)
        
        self.conn.commit()
        cursor.close()
    
    def insert_domain(self, domain: str, source: str, notes: str = "", vendor_type: Optional[str] = None) -> int:
        """Insert or update a domain and return its ID."""
        if not self._ensure_connection():
            return None
            
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO domains (domain, source, notes, vendor_type, updated_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (domain) 
            DO UPDATE SET 
                source = EXCLUDED.source,
                notes = EXCLUDED.notes,
                vendor_type = EXCLUDED.vendor_type,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """, (domain, source, notes, vendor_type))
        
        domain_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return domain_id
    
    def insert_enrichment(self, domain_id: int, enrichment_data: Dict):
        """Insert or update enrichment data for a domain."""
        if not self._ensure_connection():
            return
            
        cursor = self.conn.cursor()
        
        # Convert dict/list fields to JSON for PostgreSQL
        def to_json(value):
            if value is None:
                return None
            return Json(value) if isinstance(value, (dict, list)) else value
        
        cursor.execute("""
            INSERT INTO domain_enrichment (
                domain_id, ip_address, ip_addresses, ipv6_addresses, host_name, asn, isp,
                cdn, cms, payment_processor, registrar, creation_date, expiration_date, updated_date,
                name_servers, mx_records, whois_status, web_server, frameworks, analytics, languages,
                tech_stack, http_headers, ssl_info, whois_data, dns_records
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (domain_id)
            DO UPDATE SET
                ip_address = EXCLUDED.ip_address,
                ip_addresses = EXCLUDED.ip_addresses,
                ipv6_addresses = EXCLUDED.ipv6_addresses,
                host_name = EXCLUDED.host_name,
                asn = EXCLUDED.asn,
                isp = EXCLUDED.isp,
                cdn = EXCLUDED.cdn,
                cms = EXCLUDED.cms,
                payment_processor = EXCLUDED.payment_processor,
                registrar = EXCLUDED.registrar,
                creation_date = EXCLUDED.creation_date,
                expiration_date = EXCLUDED.expiration_date,
                updated_date = EXCLUDED.updated_date,
                name_servers = EXCLUDED.name_servers,
                mx_records = EXCLUDED.mx_records,
                whois_status = EXCLUDED.whois_status,
                web_server = EXCLUDED.web_server,
                frameworks = EXCLUDED.frameworks,
                analytics = EXCLUDED.analytics,
                languages = EXCLUDED.languages,
                tech_stack = EXCLUDED.tech_stack,
                http_headers = EXCLUDED.http_headers,
                ssl_info = EXCLUDED.ssl_info,
                whois_data = EXCLUDED.whois_data,
                dns_records = EXCLUDED.dns_records,
                enriched_at = CURRENT_TIMESTAMP
        """, (
            domain_id,
            enrichment_data.get("ip_address"),
            to_json(enrichment_data.get("ip_addresses")),
            to_json(enrichment_data.get("ipv6_addresses")),
            enrichment_data.get("host_name"),
            enrichment_data.get("asn"),
            enrichment_data.get("isp"),
            enrichment_data.get("cdn"),
            enrichment_data.get("cms"),
            enrichment_data.get("payment_processor"),
            enrichment_data.get("registrar"),
            enrichment_data.get("creation_date"),
            enrichment_data.get("expiration_date"),
            enrichment_data.get("updated_date"),
            to_json(enrichment_data.get("name_servers")),
            to_json(enrichment_data.get("mx_records")),
            enrichment_data.get("whois_status"),
            enrichment_data.get("web_server"),
            to_json(enrichment_data.get("frameworks")),
            to_json(enrichment_data.get("analytics")),
            to_json(enrichment_data.get("languages")),
            to_json(enrichment_data.get("tech_stack")),
            to_json(enrichment_data.get("http_headers")),
            to_json(enrichment_data.get("ssl_info")),
            to_json(enrichment_data.get("whois_data")),
            to_json(enrichment_data.get("dns_records"))
        ))
        
        # Store vendor_risk_score and vendor_type in whois_data JSONB if provided
        # (since we don't have dedicated columns for these)
        if enrichment_data.get("vendor_risk_score") or enrichment_data.get("vendor_type"):
            cursor.execute("""
                UPDATE domain_enrichment
                SET whois_data = COALESCE(whois_data, '{}'::jsonb) || jsonb_build_object(
                    'vendor_risk_score', %s,
                    'vendor_type', %s,
                    'vendor_name', %s
                )
                WHERE domain_id = %s
            """, (
                enrichment_data.get("vendor_risk_score"),
                enrichment_data.get("vendor_type"),
                enrichment_data.get("vendor_name"),
                domain_id
            ))
        
        self.conn.commit()
        cursor.close()
    
    def get_all_enriched_domains(self) -> List[Dict]:
        """Get all domains with their enrichment data."""
        if not self._ensure_connection():
            return []
            
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                d.id, d.domain, d.source, d.notes, d.vendor_type,
                de.ip_address, de.ip_addresses, de.host_name, de.asn, de.isp,
                de.cdn, de.cms, de.payment_processor, de.registrar,
                de.creation_date, de.expiration_date, de.name_servers,
                de.whois_data, de.enriched_at
            FROM domains d
            LEFT JOIN domain_enrichment de ON d.id = de.domain_id
            ORDER BY d.updated_at DESC
        """)
        
        results = cursor.fetchall()
        cursor.close()
        
        # Reconstruct enrichment_data dict from individual columns
        enriched_domains = []
        for row in results:
            domain_dict = dict(row)
            
            # Get whois_data JSONB which may contain vendor_risk_score, vendor_type, vendor_name
            whois_data = domain_dict.get("whois_data") or {}
            if isinstance(whois_data, str):
                try:
                    import json
                    whois_data = json.loads(whois_data)
                except:
                    whois_data = {}
            
            # Build enrichment_data dict from individual columns
            enrichment_data = {
                "domain": domain_dict.get("domain"),
                "ip_address": domain_dict.get("ip_address"),
                "ip_addresses": domain_dict.get("ip_addresses"),
                "host_name": domain_dict.get("host_name"),
                "asn": domain_dict.get("asn"),
                "isp": domain_dict.get("isp"),
                "cdn": domain_dict.get("cdn"),
                "cms": domain_dict.get("cms"),
                "payment_processor": domain_dict.get("payment_processor"),
                "registrar": domain_dict.get("registrar"),
                "creation_date": str(domain_dict.get("creation_date")) if domain_dict.get("creation_date") else None,
                "expiration_date": domain_dict.get("expiration_date"),
                "name_servers": domain_dict.get("name_servers"),
                # Extract vendor data from whois_data JSONB
                "vendor_risk_score": whois_data.get("vendor_risk_score") or 0,
                "vendor_type": whois_data.get("vendor_type") or domain_dict.get("vendor_type"),
                "vendor_name": whois_data.get("vendor_name"),
            }
            
            domain_dict["enrichment_data"] = enrichment_data
            # Also set direct fields for easier access
            domain_dict["vendor_risk_score"] = enrichment_data["vendor_risk_score"]
            if not domain_dict.get("vendor_type"):
                domain_dict["vendor_type"] = enrichment_data["vendor_type"]
            
            enriched_domains.append(domain_dict)
        
        return enriched_domains
    
    def get_vendors(self, min_domains: int = 1) -> List[Dict]:
        """Get all vendors with their domain counts."""
        if not self._ensure_connection():
            return []
            
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                v.id, v.vendor_name, v.vendor_type, v.domain_count,
                v.shared_infrastructure, v.payment_processors,
                v.first_seen, v.last_seen, v.cluster_id
            FROM vendors v
            WHERE v.domain_count >= %s
            ORDER BY v.domain_count DESC
        """, (min_domains,))
        
        results = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in results]


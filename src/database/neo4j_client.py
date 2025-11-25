"""Neo4j graph database client for storing PersonaForge vendor relationships."""

import os
import threading
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Import after load_dotenv
try:
    from src.utils.config import Config
    from src.utils.logger import logger
except ImportError:
    # Fallback if imports fail
    class Config:
        NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        NEO4J_USER = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER", "neo4j")
        NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "personaforge123password")
    
    import logging
    logger = logging.getLogger("personaforge")

load_dotenv()

# Lock to prevent concurrent reconnection attempts
_reconnect_lock = threading.Lock()

# Try to import Neo4j driver (optional)
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None


class Neo4jClient:
    """Client for interacting with Neo4j graph database for PersonaForge."""
    
    def __init__(self):
        if not NEO4J_AVAILABLE:
            logger.warning("⚠️  Neo4j driver not available. Install with: pip install neo4j")
            self.driver = None
            return
            
        uri = Config.NEO4J_URI
        user = Config.NEO4J_USER
        password = Config.NEO4J_PASSWORD
        
        logger.info(f"🔌 Attempting Neo4j connection to {uri}")
        
        try:
            self.driver = GraphDatabase.driver(
                uri, 
                auth=(user, password),
                max_connection_lifetime=1800,
                max_connection_pool_size=10,
                connection_acquisition_timeout=30,
                connection_timeout=15,
                keep_alive=True
            )
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.consume()
            logger.info(f"✅ Neo4j connection established")
        except Exception as e:
            logger.error(f"⚠️  Could not connect to Neo4j: {e}")
            logger.warning("   Neo4j will be optional. Graph features will be disabled.")
            self.driver = None
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
    
    def _execute_query(self, query: str, parameters: Dict = None):
        """Execute a Cypher query and return results."""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record for record in result]
        except Exception as e:
            logger.error(f"Neo4j query error: {e}")
            return []
    
    def create_domain(self, domain: str, **properties):
        """Create or update a domain node."""
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"""
        MERGE (d:Domain {{domain: $domain}})
        SET d += {{{props_str}}}
        RETURN d
        """
        params = {"domain": domain, **properties}
        return self._execute_query(query, params)
    
    def create_vendor(self, vendor_name: str, vendor_type: str = None, **properties):
        """Create or update a vendor node."""
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        if vendor_type:
            props_str += ", vendor_type: $vendor_type"
        query = f"""
        MERGE (v:Vendor {{name: $vendor_name}})
        SET v += {{{props_str}}}
        RETURN v
        """
        params = {"vendor_name": vendor_name, "vendor_type": vendor_type, **properties}
        return self._execute_query(query, params)
    
    def link_domain_to_vendor(self, domain: str, vendor_name: str):
        """Link a domain to a vendor."""
        query = """
        MATCH (d:Domain {domain: $domain})
        MATCH (v:Vendor {name: $vendor_name})
        MERGE (d)-[:OWNED_BY]->(v)
        RETURN d, v
        """
        return self._execute_query(query, {"domain": domain, "vendor_name": vendor_name})
    
    def link_domain_to_host(self, domain: str, host_name: str):
        """Link a domain to a hosting provider."""
        query = """
        MATCH (d:Domain {domain: $domain})
        MERGE (h:Host {name: $host_name})
        MERGE (d)-[:HOSTED_ON]->(h)
        RETURN d, h
        """
        return self._execute_query(query, {"domain": domain, "host_name": host_name})
    
    def link_domain_to_cdn(self, domain: str, cdn_name: str):
        """Link a domain to a CDN."""
        query = """
        MATCH (d:Domain {domain: $domain})
        MERGE (c:CDN {name: $cdn_name})
        MERGE (d)-[:USES_CDN]->(c)
        RETURN d, c
        """
        return self._execute_query(query, {"domain": domain, "cdn_name": cdn_name})
    
    def link_domain_to_payment(self, domain: str, processor_name: str):
        """Link a domain to a payment processor."""
        query = """
        MATCH (d:Domain {domain: $domain})
        MERGE (p:PaymentProcessor {name: $processor_name})
        MERGE (d)-[:USES_PAYMENT]->(p)
        RETURN d, p
        """
        return self._execute_query(query, {"domain": domain, "processor_name": processor_name})
    
    def get_all_nodes_and_relationships(self) -> Dict:
        """Get all nodes and relationships for graph visualization."""
        if not self.driver:
            return {"nodes": [], "edges": []}
        
        nodes_query = """
        MATCH (n)
        RETURN n, labels(n) as labels, id(n) as id
        LIMIT 1000
        """
        
        edges_query = """
        MATCH (a)-[r]->(b)
        RETURN id(a) as source, id(b) as target, type(r) as type
        LIMIT 2000
        """
        
        nodes = []
        node_map = {}
        
        # Get nodes
        for record in self._execute_query(nodes_query):
            node_id = record["id"]
            labels = record["labels"]
            props = dict(record["n"])
            
            node_type = labels[0] if labels else "Unknown"
            node_map[node_id] = {
                "id": str(node_id),
                "label": node_type,
                "properties": props
            }
            nodes.append(node_map[node_id])
        
        # Get edges
        edges = []
        for record in self._execute_query(edges_query):
            source_id = str(record["source"])
            target_id = str(record["target"])
            
            if source_id in node_map and target_id in node_map:
                edges.append({
                    "source": source_id,
                    "target": target_id,
                    "type": record["type"]
                })
        
        return {
            "nodes": nodes,
            "edges": edges
        }


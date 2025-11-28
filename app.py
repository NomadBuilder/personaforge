"""Flask web application for PersonaForge Watcher."""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
from dotenv import load_dotenv
import csv
import json
import io
from collections import Counter

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.database.neo4j_client import Neo4jClient
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    Neo4jClient = None

from src.database.postgres_client import PostgresClient
from src.enrichment.enrichment_pipeline import enrich_domain
from src.utils.config import Config
from src.utils.logger import setup_logger, logger
from src.utils.validation import validate_domain
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Setup logger
app_logger = setup_logger("personaforge.app", Config.LOG_LEVEL)

# Register error handlers
try:
    from src.utils.error_handler import register_error_handlers
    register_error_handlers(app)
except ImportError:
    app_logger.warning("Error handlers not available")

# Initialize database clients
neo4j_client = None
postgres_client = None

if NEO4J_AVAILABLE:
    try:
        neo4j_client = Neo4jClient()
        if neo4j_client and neo4j_client.driver:
            app_logger.info("✅ Neo4j client initialized and connected")
        else:
            app_logger.warning("⚠️  Neo4j client initialized but not connected")
    except Exception as e:
        app_logger.warning(f"⚠️  Neo4j not available: {e}")

try:
    postgres_client = PostgresClient()
    if postgres_client and postgres_client.conn:
        app_logger.info("✅ PostgreSQL client initialized")
    else:
        app_logger.warning("⚠️  PostgreSQL not available")
except Exception as e:
    app_logger.warning(f"⚠️  PostgreSQL not available: {e}")


@app.route('/api/homepage-stats', methods=['GET'])
def get_homepage_stats():
    """Get statistics and data for homepage display."""
    stats = {
        "total_domains": 0,
        "total_vendors": 0,
        "vendor_types": {},
        "top_vendors": [],
        "recent_discoveries": [],
        "infrastructure_clusters": 0,
        "high_risk_domains": 0,
        "database_available": False
    }
    
    stats["database_available"] = postgres_client is not None and postgres_client.conn is not None
    
    if postgres_client and postgres_client.conn:
        try:
            domains = postgres_client.get_all_enriched_domains()
            vendors = postgres_client.get_vendors(min_domains=1)
            
            stats["total_domains"] = len(domains)
            stats["total_vendors"] = len(vendors)
            
            # Vendor type distribution
            vendor_types = Counter()
            high_risk = 0
            for domain in domains:
                if domain.get('vendor_type'):
                    vendor_types[domain['vendor_type']] += 1
                
                # Get risk score (check both direct field and enrichment_data)
                risk = domain.get('vendor_risk_score', 0)
                if risk == 0:
                    # Try to get from enrichment_data
                    enrichment = domain.get('enrichment_data', {})
                    if isinstance(enrichment, str):
                        try:
                            import json
                            enrichment = json.loads(enrichment)
                        except:
                            enrichment = {}
                    risk = enrichment.get('vendor_risk_score', 0)
                
                if risk >= 70:
                    high_risk += 1
            
            stats["vendor_types"] = dict(vendor_types)
            stats["high_risk_domains"] = high_risk
            
            # Top vendors by domain count
            # If vendors table is empty, create vendor entries from domains grouped by vendor_type
            if len(vendors) == 0 and len(domains) > 0:
                # Group domains by vendor_type and create vendor entries
                from collections import defaultdict
                vendor_groups = defaultdict(list)
                for d in domains:
                    vtype = d.get('vendor_type') or d.get('enrichment_data', {}).get('vendor_type')
                    if vtype:
                        vendor_groups[vtype].append(d)
                
                # Create top vendors from grouped domains
                top_vendors = []
                for vtype, domain_list in sorted(vendor_groups.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
                    # Calculate average risk score
                    risks = []
                    for d in domain_list:
                        risk = d.get('vendor_risk_score', 0)
                        if risk == 0:
                            enrichment = d.get('enrichment_data', {})
                            if isinstance(enrichment, str):
                                try:
                                    import json
                                    enrichment = json.loads(enrichment)
                                except:
                                    enrichment = {}
                            risk = enrichment.get('vendor_risk_score', 0)
                        if risk > 0:
                            risks.append(risk)
                    
                    avg_risk = sum(risks) / len(risks) if risks else 0
                    vendor_name = vtype.replace('_', ' ').title() + ' Vendors'
                    
                    top_vendors.append({
                        "vendor_name": vendor_name,
                        "domain_count": len(domain_list),
                        "vendor_type": vtype,
                        "avg_risk_score": int(avg_risk)
                    })
                stats["top_vendors"] = top_vendors
            else:
                # Use existing vendors table data
                top_vendors = []
                for v in sorted(vendors, key=lambda x: x.get('domain_count', 0), reverse=True)[:10]:
                    vendor_name = v.get('vendor_name', 'Unknown')
                    domain_count = v.get('domain_count', 0)
                    vendor_type = v.get('vendor_type', 'unknown')
                    avg_risk = v.get('avg_risk_score', 0)
                    
                    # If missing data, try to get from domains
                    if not vendor_name or vendor_type == 'unknown' or avg_risk == 0:
                        # Find a domain for this vendor
                        vendor_domains = [d for d in domains if d.get('vendor_name') == vendor_name or 
                                         (not vendor_name and d.get('domain'))]
                        if vendor_domains:
                            sample_domain = vendor_domains[0]
                            enrichment = sample_domain.get('enrichment_data', {})
                            if isinstance(enrichment, str):
                                try:
                                    import json
                                    enrichment = json.loads(enrichment)
                                except:
                                    enrichment = {}
                            if not vendor_name or vendor_name == 'Unknown':
                                vendor_name = enrichment.get('vendor_name') or sample_domain.get('domain', 'Unknown')
                            if vendor_type == 'unknown':
                                vendor_type = enrichment.get('vendor_type') or sample_domain.get('vendor_type', 'unknown')
                            if avg_risk == 0:
                                avg_risk = enrichment.get('vendor_risk_score', 0)
                    
                    top_vendors.append({
                        "vendor_name": vendor_name,
                        "domain_count": domain_count,
                        "vendor_type": vendor_type,
                        "avg_risk_score": avg_risk
                    })
                stats["top_vendors"] = top_vendors
            
            # Recent discoveries (last 10 domains, sorted by creation/update time)
            # Sort by id (most recent = highest id) or enriched_at
            sorted_domains = sorted(domains, key=lambda x: (
                x.get('id', 0)
            ), reverse=True)
            
            recent_discoveries = []
            for d in sorted_domains[:10]:
                # Get risk score from enrichment_data if not in direct field
                risk = d.get('vendor_risk_score', 0)
                vendor_type = d.get('vendor_type')
                if risk == 0 or not vendor_type:
                    enrichment = d.get('enrichment_data', {})
                    if isinstance(enrichment, str):
                        try:
                            import json
                            enrichment = json.loads(enrichment)
                        except:
                            enrichment = {}
                    if risk == 0:
                        risk = enrichment.get('vendor_risk_score', 0)
                    if not vendor_type:
                        vendor_type = enrichment.get('vendor_type')
                
                recent_discoveries.append({
                    "domain": d.get('domain'),
                    "vendor_type": vendor_type,
                    "risk_score": risk,
                    "source": d.get('source', 'Unknown')
                })
            stats["recent_discoveries"] = recent_discoveries
            
            # Infrastructure clusters
            try:
                from src.clustering.vendor_clustering import detect_vendor_clusters
                clusters = detect_vendor_clusters(postgres_client)
                stats["infrastructure_clusters"] = len(clusters)
            except:
                pass
                
        except Exception as e:
            app_logger.error(f"Error getting homepage stats: {e}")
    
    return jsonify(stats), 200


@app.route('/')
def index():
    """Render the landing page."""
    # Try templates first, fallback to root index.html
    if os.path.exists('templates/index.html'):
        return render_template('index.html')
    elif os.path.exists('index.html'):
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(content, mimetype='text/html')
    else:
        return jsonify({"message": "PersonaForge Watcher API", "endpoints": ["/api/enrich", "/api/check", "/api/domains", "/api/vendors", "/api/clusters", "/api/graph"]})


@app.route('/dashboard')
def dashboard():
    """Render the graph visualization dashboard."""
    return render_template('dashboard.html') if os.path.exists('templates/dashboard.html') else jsonify({"message": "Dashboard coming soon"})


@app.route('/vendors')
def vendors():
    """Render the vendors listing page."""
    return render_template('vendors.html') if os.path.exists('templates/vendors.html') else jsonify({"message": "Vendors page coming soon"})


@app.route('/methodology')
def methodology():
    """Render the sources and methodology page."""
    return render_template('methodology.html') if os.path.exists('templates/methodology.html') else jsonify({"message": "Methodology page coming soon"})


@app.route('/analytics')
def analytics():
    """Render the analytics page."""
    return render_template('analytics.html') if os.path.exists('templates/analytics.html') else jsonify({"message": "Analytics coming soon"})


@app.route('/api/enrich', methods=['POST'])
def enrich_and_store():
    """
    Enrich a domain and store results in database.
    
    POST /api/enrich
    Body: {
        "domain": "example.com",
        "source": "Manual entry",
        "notes": "Optional notes",
        "vendor_type": "synthetic_identity" (optional)
    }
    """
    data = request.get_json()
    
    if not data or 'domain' not in data:
        return jsonify({"error": "Domain is required"}), 400
    
    domain = data['domain'].strip()
    source = data.get('source', 'Web API')
    notes = data.get('notes', '')
    vendor_type = data.get('vendor_type')
    
    # Validate domain
    is_valid, validation_error = validate_domain(domain)
    if not is_valid:
        return jsonify({"error": validation_error or "Invalid domain format"}), 400
    
    # Check if domain already exists
    if postgres_client and postgres_client.conn:
        try:
            existing = postgres_client.get_all_enriched_domains()
            existing_domains = [d['domain'] for d in existing if d.get('domain')]
            
            if domain in existing_domains:
                return jsonify({
                    "message": "Domain already exists in database",
                    "domain": domain,
                    "status": "exists"
                }), 200
        except Exception as e:
            app_logger.error(f"Error checking existing domain: {e}")
    
    # Enrich domain
    try:
        app_logger.info(f"Enriching domain: {domain}")
        enrichment_data = enrich_domain(domain)
        
        # Store in PostgreSQL
        domain_id = None
        if postgres_client and postgres_client.conn:
            try:
                domain_id = postgres_client.insert_domain(domain, source, notes, vendor_type)
                postgres_client.insert_enrichment(domain_id, enrichment_data)
            except Exception as e:
                app_logger.error(f"Error storing in PostgreSQL: {e}")
        
        # Store in Neo4j (optional)
        if NEO4J_AVAILABLE and neo4j_client and neo4j_client.driver:
            try:
                neo4j_client.create_domain(domain, **enrichment_data)
                
                # Link to host
                if enrichment_data.get("host_name"):
                    neo4j_client.link_domain_to_host(domain, enrichment_data["host_name"])
                
                # Link to CDN
                if enrichment_data.get("cdn"):
                    neo4j_client.link_domain_to_cdn(domain, enrichment_data["cdn"])
                
                # Link to payment processor
                if enrichment_data.get("payment_processor"):
                    processors = [p.strip() for p in enrichment_data["payment_processor"].split(",")]
                    for processor in processors:
                        neo4j_client.link_domain_to_payment(domain, processor)
                
                neo4j_client.close()
            except Exception as e:
                app_logger.warning(f"Neo4j storage failed (continuing without it): {e}")
        
        return jsonify({
            "message": "Domain enriched and stored successfully",
            "domain": domain,
            "data": enrichment_data,
            "status": "success"
        }), 201
    
    except Exception as e:
        app_logger.error(f"Error enriching domain: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "domain": domain,
            "status": "error"
        }), 500


@app.route('/api/check', methods=['POST'])
def check_domain_only():
    """
    Check/enrich a domain WITHOUT storing it in the database.
    This is for one-off analysis only.
    
    POST /api/check
    Body: {
        "domain": "example.com"
    }
    """
    data = request.get_json()
    
    if not data or 'domain' not in data:
        return jsonify({"error": "Domain is required"}), 400
    
    domain = data['domain'].strip()
    
    # Validate domain
    is_valid, validation_error = validate_domain(domain)
    if not is_valid:
        return jsonify({"error": validation_error or "Invalid domain format"}), 400
    
    try:
        app_logger.info(f"Checking domain (no storage): {domain}")
        enrichment_data = enrich_domain(domain)
        
        return jsonify({
            "message": "Domain analyzed successfully (not stored)",
            "domain": domain,
            "data": enrichment_data,
            "status": "checked"
        }), 200
    
    except Exception as e:
        app_logger.error(f"Error checking domain: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "domain": domain,
            "status": "error"
        }), 500


@app.route('/api/domains', methods=['GET'])
def get_domains():
    """Get all enriched domains from database."""
    if not postgres_client or not postgres_client.conn:
        return jsonify({
            "domains": [],
            "count": 0,
            "message": "PostgreSQL not available"
        }), 200
    
    try:
        domains = postgres_client.get_all_enriched_domains()
        return jsonify({
            "domains": domains,
            "count": len(domains)
        })
    except Exception as e:
        app_logger.error(f"Error getting domains: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    """Get all vendors with their domain counts."""
    if not postgres_client or not postgres_client.conn:
        return jsonify({
            "vendors": [],
            "message": "PostgreSQL not available"
        }), 200
    
    try:
        min_domains = int(request.args.get('min_domains', 1))
        vendors = postgres_client.get_vendors(min_domains=min_domains)
        return jsonify({
            "vendors": vendors,
            "count": len(vendors)
        })
    except Exception as e:
        app_logger.error(f"Error getting vendors: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/graph', methods=['GET'])
def get_graph():
    """Get graph data from Neo4j or generate from PostgreSQL for visualization."""
    # Try Neo4j first if available
    if NEO4J_AVAILABLE and neo4j_client and neo4j_client.driver:
        try:
            graph_data = neo4j_client.get_all_nodes_and_relationships()
            if graph_data.get('nodes') and len(graph_data.get('nodes', [])) > 0:
                return jsonify(graph_data), 200
        except Exception as e:
            app_logger.warning(f"Neo4j graph data failed, falling back to PostgreSQL: {e}")
    
    # Fallback: Generate graph from PostgreSQL
    if not postgres_client or not postgres_client.conn:
        return jsonify({
            "nodes": [],
            "edges": [],
            "message": "No database available"
        }), 200
    
    try:
        domains = postgres_client.get_all_enriched_domains()
        
        if len(domains) == 0:
            return jsonify({
                "nodes": [],
                "edges": [],
                "message": "No domains available"
            }), 200
        
        # Use clustering to organize the graph better
        from src.clustering.vendor_clustering import detect_vendor_clusters
        clusters = detect_vendor_clusters(postgres_client)
        
        # Build graph from PostgreSQL data with clustering
        nodes = []
        edges = []
        node_map = {}  # Track nodes by ID to avoid duplicates
        
        # Limit to top domains by risk score or most recent
        sorted_domains = sorted(domains, key=lambda d: (
            d.get('vendor_risk_score', 0) or 
            d.get('enrichment_data', {}).get('vendor_risk_score', 0) if isinstance(d.get('enrichment_data'), dict) else 0
        ), reverse=True)
        
        # Take top 40 domains for cleaner visualization
        top_domains = sorted_domains[:40]
        top_domain_names = {d.get('domain') for d in top_domains if d.get('domain')}
        
        # Only create cluster nodes for clusters that have at least one domain in top_domains
        cluster_node_map = {}
        clusters_with_top_domains = []
        
        for cluster in clusters:
            # Check if any domain in this cluster is in the top domains
            cluster_domains = set(cluster.get('domains', []))
            if cluster_domains & top_domain_names:  # Intersection - at least one domain matches
                clusters_with_top_domains.append(cluster)
        
        # Create cluster nodes only for clusters with domains in the graph
        for cluster in clusters_with_top_domains[:10]:  # Top 10 clusters that have domains in graph
            cluster_id = f"cluster_{hash(cluster['signature']) % 10000}"
            cluster_node_map[cluster['signature']] = cluster_id
            
            # Count how many domains from this cluster are actually in the graph
            cluster_domains = set(cluster.get('domains', []))
            domains_in_graph = list(cluster_domains & top_domain_names)  # Keep as list for display
            domains_in_graph_count = len(domains_in_graph)
            
            nodes.append({
                "id": cluster_id,
                "label": "Cluster",
                "properties": {
                    "name": f"Cluster ({domains_in_graph_count} domains)",
                    "domain_count": domains_in_graph_count,
                    "signature": cluster['signature'],
                    "domains": sorted(domains_in_graph)  # Store actual domain names
                }
            })
            node_map[cluster_id] = True
        
        # Add domain nodes and create relationships
        for domain in top_domains:
            domain_name = domain.get('domain')
            if not domain_name:
                continue
            
            domain_id = f"domain_{domain.get('id', domain_name)}"
            
            # Get enrichment data (needed for both node creation and cluster matching)
            enrichment = domain.get('enrichment_data', {})
            if isinstance(enrichment, str):
                try:
                    import json
                    enrichment = json.loads(enrichment)
                except:
                    enrichment = {}
            
            # Add domain node
            if domain_id not in node_map:
                vendor_type = domain.get('vendor_type') or enrichment.get('vendor_type')
                risk_score = domain.get('vendor_risk_score', 0) or enrichment.get('vendor_risk_score', 0)
                
                nodes.append({
                    "id": domain_id,
                    "label": "Domain",
                    "properties": {
                        "domain": domain_name,
                        "vendor_type": vendor_type,
                        "risk_score": risk_score
                    }
                })
                node_map[domain_id] = True
            
            # Add vendor node and edge (group by vendor_type)
            vendor_type = domain.get('vendor_type') or enrichment.get('vendor_type')
            if vendor_type:
                vendor_id = f"vendor_{vendor_type}"
                if vendor_id not in node_map:
                    nodes.append({
                        "id": vendor_id,
                        "label": "Vendor",
                        "properties": {
                            "name": vendor_type.replace('_', ' ').title(),
                            "vendor_type": vendor_type
                        }
                    })
                    node_map[vendor_id] = True
                
                edges.append({
                    "source": domain_id,
                    "target": vendor_id,
                    "type": "OWNED_BY"
                })
            
            # Link domain to cluster if it belongs to one
            # Build domain signature the same way clusters are built
            domain_signature_parts = []
            domain_host = enrichment.get('host_name') or domain.get('host_name')
            domain_cdn = enrichment.get('cdn') or domain.get('cdn')
            domain_registrar = enrichment.get('registrar') or domain.get('registrar')
            domain_payment = enrichment.get('payment_processor') or domain.get('payment_processor')
            
            if domain_host:
                domain_signature_parts.append(f"host:{domain_host}")
            if domain_cdn:
                domain_signature_parts.append(f"cdn:{domain_cdn}")
            if domain_registrar:
                domain_signature_parts.append(f"registrar:{domain_registrar}")
            if domain_payment:
                domain_signature_parts.append(f"payment:{domain_payment}")
            
            # Match domain signature to cluster signature (exact match)
            if domain_signature_parts:
                domain_signature = "|".join(sorted(domain_signature_parts))
                if domain_signature in cluster_node_map:
                    cluster_id = cluster_node_map[domain_signature]
                    edges.append({
                        "source": domain_id,
                        "target": cluster_id,
                        "type": "IN_CLUSTER"
                    })
        
        # Now create infrastructure nodes with complete domain lists
        # First pass: collect all infrastructure usage
        infra_tracking = {'hosts': {}, 'cdns': {}, 'payments': {}}
        for domain in top_domains:
            domain_name = domain.get('domain')
            if not domain_name:
                continue
            
            enrichment = domain.get('enrichment_data', {})
            if isinstance(enrichment, str):
                try:
                    import json
                    enrichment = json.loads(enrichment)
                except:
                    enrichment = {}
            
            host_name = enrichment.get('host_name') or domain.get('host_name')
            cdn = enrichment.get('cdn') or domain.get('cdn')
            payment = enrichment.get('payment_processor') or domain.get('payment_processor')
            
            if host_name:
                host_id = f"host_{host_name}"
                if host_id not in infra_tracking['hosts']:
                    infra_tracking['hosts'][host_id] = {'name': host_name, 'domains': []}
                if domain_name not in infra_tracking['hosts'][host_id]['domains']:
                    infra_tracking['hosts'][host_id]['domains'].append(domain_name)
            
            if cdn:
                cdn_id = f"cdn_{cdn}"
                if cdn_id not in infra_tracking['cdns']:
                    infra_tracking['cdns'][cdn_id] = {'name': cdn, 'domains': []}
                if domain_name not in infra_tracking['cdns'][cdn_id]['domains']:
                    infra_tracking['cdns'][cdn_id]['domains'].append(domain_name)
            
            if payment:
                payment_id = f"payment_{payment}"
                if payment_id not in infra_tracking['payments']:
                    infra_tracking['payments'][payment_id] = {'name': payment, 'domains': []}
                if domain_name not in infra_tracking['payments'][payment_id]['domains']:
                    infra_tracking['payments'][payment_id]['domains'].append(domain_name)
        
        # Second pass: create infrastructure nodes and edges for those with 2+ domains
        for host_id, host_data in infra_tracking['hosts'].items():
            if len(host_data['domains']) >= 2:
                if host_id not in node_map:
                    nodes.append({
                        "id": host_id,
                        "label": "Host",
                        "properties": {
                            "name": host_data['name'],
                            "domain_count": len(host_data['domains']),
                            "domains": host_data['domains']
                        }
                    })
                    node_map[host_id] = True
                
                # Create edges for all domains using this host
                for domain_name in host_data['domains']:
                    domain_node = next((n for n in nodes if n.get("properties", {}).get("domain") == domain_name), None)
                    if domain_node:
                        edges.append({
                            "source": domain_node["id"],
                            "target": host_id,
                            "type": "HOSTED_ON"
                        })
        
        for cdn_id, cdn_data in infra_tracking['cdns'].items():
            if len(cdn_data['domains']) >= 2:
                if cdn_id not in node_map:
                    nodes.append({
                        "id": cdn_id,
                        "label": "CDN",
                        "properties": {
                            "name": cdn_data['name'],
                            "domain_count": len(cdn_data['domains']),
                            "domains": cdn_data['domains']
                        }
                    })
                    node_map[cdn_id] = True
                
                for domain_name in cdn_data['domains']:
                    domain_node = next((n for n in nodes if n.get("properties", {}).get("domain") == domain_name), None)
                    if domain_node:
                        edges.append({
                            "source": domain_node["id"],
                            "target": cdn_id,
                            "type": "USES_CDN"
                        })
        
        for payment_id, payment_data in infra_tracking['payments'].items():
            if len(payment_data['domains']) >= 2:
                if payment_id not in node_map:
                    nodes.append({
                        "id": payment_id,
                        "label": "PaymentProcessor",
                        "properties": {
                            "name": payment_data['name'],
                            "domain_count": len(payment_data['domains']),
                            "domains": payment_data['domains']
                        }
                    })
                    node_map[payment_id] = True
                
                for domain_name in payment_data['domains']:
                    domain_node = next((n for n in nodes if n.get("properties", {}).get("domain") == domain_name), None)
                    if domain_node:
                        edges.append({
                            "source": domain_node["id"],
                            "target": payment_id,
                            "type": "USES_PAYMENT"
                        })
        
        return jsonify({
            "nodes": nodes,
            "edges": edges
        }), 200
        
    except Exception as e:
        app_logger.error(f"Error generating graph from PostgreSQL: {e}")
        return jsonify({
            "error": str(e),
            "nodes": [],
            "edges": []
        }), 500


@app.route('/api/clusters', methods=['GET'])
def get_clusters():
    """Get detected vendor clusters."""
    if not postgres_client or not postgres_client.conn:
        return jsonify({
            "clusters": [],
            "message": "PostgreSQL not available"
        }), 200
    
    try:
        from src.clustering.vendor_clustering import detect_vendor_clusters
        clusters = detect_vendor_clusters(postgres_client)
        return jsonify({
            "clusters": clusters,
            "count": len(clusters)
        }), 200
    except Exception as e:
        app_logger.error(f"Error getting clusters: {e}")
        return jsonify({
            "clusters": [],
            "error": str(e)
        }), 500


@app.route('/api/export/domains', methods=['GET'])
def export_domains():
    """Export domains to CSV or JSON."""
    if not postgres_client or not postgres_client.conn:
        return jsonify({"error": "PostgreSQL not available"}), 500
    
    format_type = request.args.get('format', 'json').lower()
    
    try:
        domains = postgres_client.get_all_enriched_domains()
        
        if format_type == 'csv':
            from src.utils.export import export_domains_to_csv
            csv_data = export_domains_to_csv(domains)
            return Response(
                csv_data,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=personaforge_domains_{datetime.now().strftime("%Y%m%d")}.csv'}
            )
        else:
            return jsonify({
                "domains": domains,
                "count": len(domains),
                "exported_at": datetime.now().isoformat()
            })
    except Exception as e:
        app_logger.error(f"Error exporting domains: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/export/vendors', methods=['GET'])
def export_vendors():
    """Export vendors to CSV or JSON."""
    if not postgres_client or not postgres_client.conn:
        return jsonify({"error": "PostgreSQL not available"}), 500
    
    format_type = request.args.get('format', 'json').lower()
    min_domains = int(request.args.get('min_domains', 1))
    
    try:
        vendors = postgres_client.get_vendors(min_domains=min_domains)
        
        if format_type == 'csv':
            from src.utils.export import export_vendors_to_csv
            csv_data = export_vendors_to_csv(vendors)
            return Response(
                csv_data,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=personaforge_vendors_{datetime.now().strftime("%Y%m%d")}.csv'}
            )
        else:
            return jsonify({
                "vendors": vendors,
                "count": len(vendors),
                "exported_at": datetime.now().isoformat()
            })
    except Exception as e:
        app_logger.error(f"Error exporting vendors: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/export/graph', methods=['GET'])
def export_graph():
    """Export graph to GraphML or JSON."""
    if not NEO4J_AVAILABLE or not neo4j_client or not neo4j_client.driver:
        return jsonify({"error": "Neo4j not available"}), 500
    
    format_type = request.args.get('format', 'json').lower()
    
    try:
        graph_data = neo4j_client.get_all_nodes_and_relationships()
        
        if format_type == 'graphml':
            from src.utils.export import export_graph_to_graphml
            graphml_data = export_graph_to_graphml(
                graph_data.get('nodes', []),
                graph_data.get('edges', [])
            )
            return Response(
                graphml_data,
                mimetype='application/xml',
                headers={'Content-Disposition': f'attachment; filename=personaforge_graph_{datetime.now().strftime("%Y%m%d")}.graphml'}
            )
        else:
            return jsonify({
                **graph_data,
                "exported_at": datetime.now().isoformat()
            })
    except Exception as e:
        app_logger.error(f"Error exporting graph: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/batch/enrich', methods=['POST'])
def batch_enrich():
    """
    Enrich multiple domains in batch.
    
    POST /api/batch/enrich
    Body: {
        "domains": ["example.com", "example2.com"],
        "source": "Batch import",
        "vendor_type": "synthetic_identity"
    }
    """
    data = request.get_json()
    
    if not data or 'domains' not in data:
        return jsonify({"error": "domains array is required"}), 400
    
    domains = data.get('domains', [])
    if not isinstance(domains, list) or len(domains) == 0:
        return jsonify({"error": "domains must be a non-empty array"}), 400
    
    if len(domains) > 100:
        return jsonify({"error": "Maximum 100 domains per batch"}), 400
    
    source = data.get('source', 'Batch import')
    vendor_type = data.get('vendor_type')
    
    results = []
    errors = []
    
    for domain in domains:
        domain = domain.strip() if isinstance(domain, str) else str(domain).strip()
        
        # Validate domain
        is_valid, validation_error = validate_domain(domain)
        if not is_valid:
            errors.append({
                "domain": domain,
                "error": validation_error or "Invalid domain format"
            })
            continue
        
        try:
            # Enrich domain
            enrichment_data = enrich_domain(domain)
            
            # Store in database
            domain_id = None
            if postgres_client and postgres_client.conn:
                try:
                    domain_id = postgres_client.insert_domain(domain, source, '', vendor_type)
                    postgres_client.insert_enrichment(domain_id, enrichment_data)
                except Exception as e:
                    app_logger.error(f"Error storing {domain}: {e}")
            
            results.append({
                "domain": domain,
                "status": "success",
                "data": enrichment_data,
                "domain_id": domain_id
            })
        except Exception as e:
            errors.append({
                "domain": domain,
                "error": str(e)
            })
    
    return jsonify({
        "message": f"Processed {len(domains)} domains",
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }), 200


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get analytics and statistics about the dataset."""
    if not postgres_client or not postgres_client.conn:
        return jsonify({
            "error": "PostgreSQL not available",
            "statistics": {}
        }), 200
    
    try:
        domains = postgres_client.get_all_enriched_domains()
        vendors = postgres_client.get_vendors(min_domains=1)
        
        # Calculate statistics
        total_domains = len(domains)
        
        # Vendor type distribution
        vendor_types = Counter()
        for domain in domains:
            if domain.get('vendor_type'):
                vendor_types[domain['vendor_type']] += 1
        
        # Infrastructure statistics
        hosts = Counter()
        cdns = Counter()
        registrars = Counter()
        payment_processors = Counter()
        
        for domain in domains:
            if domain.get('host_name'):
                hosts[domain['host_name']] += 1
            if domain.get('cdn'):
                cdns[domain['cdn']] += 1
            if domain.get('registrar'):
                registrars[domain['registrar']] += 1
            if domain.get('payment_processor'):
                processors = [p.strip() for p in str(domain['payment_processor']).split(',')]
                for processor in processors:
                    if processor:
                        payment_processors[processor] += 1
        
        # Top vendors
        top_vendors = sorted(vendors, key=lambda x: x.get('domain_count', 0), reverse=True)[:10]
        
        analytics = {
            "summary": {
                "total_domains": total_domains,
                "total_vendors": len(vendors),
                "domains_with_vendor_type": sum(1 for d in domains if d.get('vendor_type')),
                "domains_with_enrichment": sum(1 for d in domains if d.get('ip_address'))
            },
            "vendor_types": dict(vendor_types),
            "top_hosts": [{"name": name, "count": count} for name, count in hosts.most_common(10)],
            "top_cdns": [{"name": name, "count": count} for name, count in cdns.most_common(10)],
            "top_registrars": [{"name": name, "count": count} for name, count in registrars.most_common(10)],
            "top_payment_processors": [{"name": name, "count": count} for name, count in payment_processors.most_common(10)],
            "top_vendors": [
                {
                    "name": v.get('vendor_name', 'Unknown'),
                    "type": v.get('vendor_type', 'Unknown'),
                    "domain_count": v.get('domain_count', 0)
                }
                for v in top_vendors
            ]
        }
        
        return jsonify(analytics), 200
    except Exception as e:
        app_logger.error(f"Error getting analytics: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/search', methods=['GET'])
def search():
    """Search domains, vendors, and infrastructure."""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all').lower()  # all, domain, vendor, infrastructure
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    if not postgres_client or not postgres_client.conn:
        return jsonify({"error": "PostgreSQL not available"}), 500
    
    try:
        results = {
            "query": query,
            "domains": [],
            "vendors": [],
            "infrastructure": []
        }
        
        if search_type in ['all', 'domain']:
            # Search domains
            domains = postgres_client.get_all_enriched_domains()
            query_lower = query.lower()
            for domain in domains:
                domain_name = domain.get('domain', '').lower()
                if query_lower in domain_name:
                    results["domains"].append(domain)
        
        if search_type in ['all', 'vendor']:
            # Search vendors
            vendors = postgres_client.get_vendors(min_domains=1)
            query_lower = query.lower()
            for vendor in vendors:
                vendor_name = vendor.get('vendor_name', '').lower()
                if query_lower in vendor_name:
                    results["vendors"].append(vendor)
        
        if search_type in ['all', 'infrastructure']:
            # Search infrastructure (hosts, CDNs, registrars)
            domains = postgres_client.get_all_enriched_domains()
            query_lower = query.lower()
            infrastructure_set = set()
            
            for domain in domains:
                if domain.get('host_name') and query_lower in domain.get('host_name', '').lower():
                    infrastructure_set.add(('host', domain['host_name']))
                if domain.get('cdn') and query_lower in domain.get('cdn', '').lower():
                    infrastructure_set.add(('cdn', domain['cdn']))
                if domain.get('registrar') and query_lower in domain.get('registrar', '').lower():
                    infrastructure_set.add(('registrar', domain['registrar']))
            
            results["infrastructure"] = [
                {"type": item[0], "name": item[1]}
                for item in infrastructure_set
            ]
        
        return jsonify(results), 200
    except Exception as e:
        app_logger.error(f"Error searching: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """Upload CSV file and enrich all domains in it."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a CSV"}), 400
    
    try:
        # Read CSV content
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        domains = []
        errors = []
        
        # Parse CSV - support multiple column formats
        for row_num, row in enumerate(csv_input, start=2):  # Start at 2 (row 1 is header)
            try:
                # Try different column name variations
                domain = row.get('domain') or row.get('url') or row.get('website') or row.get('site') or ''
                
                # Clean up domain
                domain = domain.strip() if domain else ''
                if domain:
                    # Remove protocol and www
                    domain = domain.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0].strip()
                
                if domain:
                    # Validate domain
                    is_valid, validation_error = validate_domain(domain)
                    if is_valid:
                        domains.append({
                            'domain': domain,
                            'row': row_num,
                            'source': row.get('source', 'CSV Upload'),
                            'notes': row.get('notes', ''),
                            'vendor_type': row.get('vendor_type') or row.get('type')
                        })
                    else:
                        errors.append(f"Row {row_num}: {validation_error or 'Invalid domain format'}")
                else:
                    errors.append(f"Row {row_num}: No domain found")
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        if not domains:
            return jsonify({
                "error": "No valid domains found in CSV",
                "details": errors
            }), 400
        
        # Enrich all domains
        results = []
        enriched_count = 0
        
        for domain_data in domains:
            try:
                domain = domain_data['domain']
                
                # Enrich domain
                enrichment_data = enrich_domain(domain)
                
                # Store in database
                domain_id = None
                if postgres_client and postgres_client.conn:
                    try:
                        domain_id = postgres_client.insert_domain(
                            domain,
                            domain_data.get('source', 'CSV Upload'),
                            domain_data.get('notes', ''),
                            domain_data.get('vendor_type')
                        )
                        postgres_client.insert_enrichment(domain_id, enrichment_data)
                    except Exception as e:
                        app_logger.error(f"Error storing {domain}: {e}")
                
                results.append({
                    'domain': domain,
                    'row': domain_data['row'],
                    'status': 'success',
                    'data': enrichment_data,
                    'domain_id': domain_id
                })
                enriched_count += 1
            except Exception as e:
                errors.append(f"Row {domain_data['row']}: Enrichment failed - {str(e)}")
                app_logger.error(f"Error enriching domain from CSV row {domain_data['row']}: {e}")
        
        return jsonify({
            "message": f"Processed {len(domains)} domains, enriched {enriched_count}",
            "enriched": enriched_count,
            "total": len(domains),
            "errors": errors,
            "results": results
        }), 200
        
    except Exception as e:
        app_logger.error(f"Error processing CSV: {e}", exc_info=True)
        return jsonify({"error": f"Error processing CSV: {str(e)}"}), 500


@app.route('/api/discover', methods=['POST'])
def discover_vendors():
    """
    Discover vendors from public sources and automatically enrich them.
    
    This actively searches:
    - AI-powered discovery (uses OpenAI to find vendors and data sources)
    - Certificate Transparency (crt.sh)
    - Reddit public posts
    - Search engines (DuckDuckGo)
    - URLhaus malware database
    - Public Telegram channels
    
    Returns discovered domains and enrichment status.
    """
    try:
        from src.enrichment.vendor_discovery import discover_all_sources, ask_ai_for_data_sources
        
        data = request.get_json() or {}
        limit_per_source = data.get('limit_per_source', 20)
        auto_enrich = data.get('auto_enrich', True)
        
        app_logger.info(f"🔍 Starting vendor discovery (limit: {limit_per_source})...")
        
        # First, ask AI for data sources and strategies
        ai_sources = ask_ai_for_data_sources()
        app_logger.info(f"🤖 AI suggested {len(ai_sources.get('sources', []))} data sources")
        
        # Discover from all sources (including AI)
        discovery_results = discover_all_sources(limit_per_source=limit_per_source)
        
        # Combine all discovered domains
        all_domains = set()
        for domains in discovery_results.values():
            all_domains.update(domains)
        
        enriched_domains = []
        errors = []
        
        # Optionally auto-enrich discovered domains
        if auto_enrich and all_domains:
            app_logger.info(f"📊 Auto-enriching {len(all_domains)} discovered domains...")
            
            for domain in list(all_domains)[:50]:  # Limit to 50 to avoid timeout
                try:
                    # Enrich the domain
                    enrichment_data = enrich_domain(domain)
                    
                    # Store in database
                    if postgres_client and postgres_client.conn:
                        try:
                            domain_id = postgres_client.insert_domain(
                                domain,
                                'Auto-discovery',
                                f"Discovered from public sources",
                                enrichment_data.get('vendor_type')
                            )
                            postgres_client.insert_enrichment(domain_id, enrichment_data)
                            enriched_domains.append({
                                'domain': domain,
                                'vendor_type': enrichment_data.get('vendor_type'),
                                'risk_score': enrichment_data.get('vendor_risk_score', 0)
                            })
                        except Exception as e:
                            app_logger.error(f"Error storing discovered domain {domain}: {e}")
                            errors.append(f"{domain}: Storage failed")
                except Exception as e:
                    app_logger.error(f"Error enriching discovered domain {domain}: {e}")
                    errors.append(f"{domain}: Enrichment failed")
        
        return jsonify({
            "message": f"Discovered {len(all_domains)} unique domains from public sources",
            "discovered": len(all_domains),
            "enriched": len(enriched_domains),
            "sources": {k: len(v) for k, v in discovery_results.items()},
            "domains_by_source": discovery_results,
            "enriched_domains": enriched_domains,
            "ai_suggestions": ai_sources,
            "errors": errors
        }), 200
        
    except Exception as e:
        app_logger.error(f"Error in vendor discovery: {e}", exc_info=True)
        return jsonify({"error": f"Discovery failed: {str(e)}"}), 500


@app.route('/api/discover/status', methods=['GET'])
def discover_status():
    """Get status of last discovery run."""
    # In a real implementation, you'd store this in the database
    # For now, return a simple status
    return jsonify({
        "status": "ready",
        "message": "Discovery endpoint available. POST to /api/discover to start discovery."
    }), 200


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    from src.utils.cache import get_cache_stats
    from src.utils.rate_limiter import get_api_remaining
    
    neo4j_status = {
        "available": NEO4J_AVAILABLE,
        "client_initialized": neo4j_client is not None,
        "driver_connected": neo4j_client is not None and neo4j_client.driver is not None
    }
    
    postgres_status = {
        "available": postgres_client is not None,
        "connected": postgres_client is not None and postgres_client.conn is not None
    }
    
    cache_stats = get_cache_stats()
    api_status = {
        "ip-api.com": get_api_remaining("ip-api.com"),
        "iplocate.io": get_api_remaining("iplocate.io")
    }
    
    return jsonify({
        "status": "ok",
        "neo4j": neo4j_status,
        "postgres": postgres_status,
        "cache": cache_stats,
        "api_quotas": api_status
    }), 200


def run_initial_discovery():
    """Run discovery on startup if database is empty."""
    if not postgres_client or not postgres_client.conn:
        app_logger.info("⚠️  PostgreSQL not available - skipping initial discovery")
        return
    
    try:
        # Check if we have any domains
        domains = postgres_client.get_all_enriched_domains()
        if len(domains) == 0:
            app_logger.info("🔍 Database is empty - running initial discovery...")
            try:
                from src.enrichment.vendor_discovery import discover_all_sources
                from src.enrichment.enrichment_pipeline import enrich_domain
                
                # Run discovery
                discovery_results = discover_all_sources(limit_per_source=10)
                
                # Combine all discovered domains
                all_domains = set()
                for domains_list in discovery_results.values():
                    all_domains.update(domains_list)
                
                app_logger.info(f"📊 Discovered {len(all_domains)} domains, enriching top 20...")
                
                # Enrich and store top domains
                enriched = 0
                for domain in list(all_domains)[:20]:
                    try:
                        enrichment_data = enrich_domain(domain)
                        domain_id = postgres_client.insert_domain(
                            domain,
                            'Auto-discovery',
                            'Initial discovery on startup',
                            enrichment_data.get('vendor_type')
                        )
                        postgres_client.insert_enrichment(domain_id, enrichment_data)
                        enriched += 1
                    except Exception as e:
                        app_logger.debug(f"Error enriching {domain}: {e}")
                
                app_logger.info(f"✅ Initial discovery complete - enriched {enriched} domains")
                
                # If discovery found nothing, enrich a few test domains to demonstrate the system
                if enriched == 0:
                    app_logger.info("🔍 Discovery found no domains - enriching test domains to demonstrate system...")
                    test_domains = [
                        "example.com",
                        "test.com", 
                        "demo.com"
                    ]
                    for domain in test_domains:
                        try:
                            enrichment_data = enrich_domain(domain)
                            domain_id = postgres_client.insert_domain(
                                domain,
                                'Test data',
                                'Initial test to demonstrate system',
                                enrichment_data.get('vendor_type')
                            )
                            postgres_client.insert_enrichment(domain_id, enrichment_data)
                            app_logger.info(f"  ✓ Enriched test domain: {domain}")
                        except Exception as e:
                            app_logger.debug(f"Error enriching test domain {domain}: {e}")
            except Exception as e:
                app_logger.error(f"Initial discovery failed: {e}", exc_info=True)
        else:
            app_logger.info(f"✅ Database has {len(domains)} domains - skipping initial discovery")
    except Exception as e:
        app_logger.error(f"Error checking database for initial discovery: {e}")


if __name__ == '__main__':
    # Auto-seed dummy data for PersonaForge ONCE if no dummy data exists
    # This ensures the visualization always has data to display
    import threading
    import time
    def delayed_setup():
        time.sleep(3)  # Wait for app to fully start
        try:
            if postgres_client and postgres_client.conn:
                # Check specifically for dummy data (not all domains)
                # Note: Standalone PersonaForge uses 'domains' table (not prefixed)
                cursor = postgres_client.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM domains WHERE source = 'DUMMY_DATA_FOR_TESTING'")
                dummy_count = cursor.fetchone()[0]
                cursor.close()
                
                if dummy_count == 0:
                    app_logger.info("📊 No dummy data found - seeding dummy data for PersonaForge visualization (one-time only)...")
                    from src.database.seed_dummy_data import seed_dummy_data
                    count = seed_dummy_data(num_domains=50)
                    app_logger.info(f"✅ Seeded {count} dummy domains for PersonaForge visualization")
                else:
                    app_logger.info(f"✅ Dummy data already exists ({dummy_count} domains) - skipping seed")
        except Exception as e:
            app_logger.error(f"Error checking/seeding dummy data: {e}", exc_info=True)
        
        # Run initial discovery in background if database has real data
        run_initial_discovery()
    
    setup_thread = threading.Thread(target=delayed_setup, daemon=True)
    setup_thread.start()
    
    port = int(os.getenv('PORT', os.getenv('FLASK_PORT', 5000)))
    debug = Config.FLASK_DEBUG
    app_logger.info(f"🚀 PersonaForge starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)


"""Vendor clustering module for detecting vendor patterns by infrastructure overlap."""

from typing import Dict, List
from collections import defaultdict, Counter


def detect_vendor_clusters(postgres_client) -> List[Dict]:
    """
    Detect vendor clusters by analyzing shared infrastructure.
    
    Clusters vendors based on:
    - Shared hosting providers
    - Shared CDNs
    - Shared payment processors
    - Shared registrars
    - Shared IP blocks
    """
    if not postgres_client or not postgres_client.conn:
        return []
    
    try:
        domains = postgres_client.get_all_enriched_domains()
        
        # Group domains by shared infrastructure
        infrastructure_groups = defaultdict(list)
        
        for domain in domains:
            domain_name = domain.get('domain')
            if not domain_name:
                continue
            
            # Create infrastructure signature
            # Check both direct fields and enrichment_data JSONB
            enrichment = domain.get('enrichment_data', {})
            if isinstance(enrichment, str):
                try:
                    import json
                    enrichment = json.loads(enrichment)
                except:
                    enrichment = {}
            
            signature_parts = []
            
            # Extract infrastructure data (check both direct fields and enrichment_data)
            host_name = domain.get('host_name') or enrichment.get('host_name')
            cdn = domain.get('cdn') or enrichment.get('cdn')
            registrar = domain.get('registrar') or enrichment.get('registrar')
            payment_processor = domain.get('payment_processor') or enrichment.get('payment_processor')
            
            if host_name:
                signature_parts.append(f"host:{host_name}")
            if cdn:
                signature_parts.append(f"cdn:{cdn}")
            if registrar:
                signature_parts.append(f"registrar:{registrar}")
            if payment_processor:
                signature_parts.append(f"payment:{payment_processor}")
            
            if signature_parts:
                signature = "|".join(sorted(signature_parts))
                infrastructure_groups[signature].append(domain_name)
        
        # Convert to clusters
        clusters = []
        for signature, domain_list in infrastructure_groups.items():
            if len(domain_list) >= 2:  # At least 2 domains to form a cluster
                # Get vendor types in this cluster to see if it spans multiple vendor types
                cluster_vendor_types = set()
                for domain_name in domain_list:
                    # Find the domain object
                    domain_obj = next((d for d in domains if d.get('domain') == domain_name), None)
                    if domain_obj:
                        vtype = domain_obj.get('vendor_type')
                        if not vtype:
                            enrichment = domain_obj.get('enrichment_data', {})
                            if isinstance(enrichment, str):
                                try:
                                    import json
                                    enrichment = json.loads(enrichment)
                                except:
                                    enrichment = {}
                            vtype = enrichment.get('vendor_type')
                        if vtype:
                            cluster_vendor_types.add(vtype)
                
                clusters.append({
                    "signature": signature,
                    "domains": domain_list,
                    "domain_count": len(domain_list),
                    "infrastructure": signature.split("|"),
                    "vendor_types": list(cluster_vendor_types),
                    "vendor_type_count": len(cluster_vendor_types)
                })
        
        # Sort by domain count (largest clusters first), then by vendor type diversity
        clusters.sort(key=lambda x: (x["domain_count"], x["vendor_type_count"]), reverse=True)
        
        return clusters
    
    except Exception as e:
        print(f"Error detecting vendor clusters: {e}")
        return []


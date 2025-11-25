"""Export utilities for PersonaForge data."""

import csv
import json
import io
from typing import List, Dict
from datetime import datetime


def export_domains_to_csv(domains: List[Dict]) -> str:
    """Export domains to CSV format."""
    if not domains:
        return ""
    
    output = io.StringIO()
    
    # Get all possible field names
    fieldnames = set()
    for domain in domains:
        fieldnames.update(domain.keys())
    
    # Order fields logically
    ordered_fields = [
        'id', 'domain', 'vendor_type', 'vendor_name', 'source', 'notes',
        'ip_address', 'host_name', 'isp', 'asn', 'cdn', 'cms',
        'payment_processor', 'registrar', 'creation_date', 'expiration_date',
        'enriched_at'
    ]
    
    # Add remaining fields
    for field in sorted(fieldnames):
        if field not in ordered_fields:
            ordered_fields.append(field)
    
    writer = csv.DictWriter(output, fieldnames=ordered_fields, extrasaction='ignore')
    writer.writeheader()
    
    for domain in domains:
        # Flatten nested structures
        row = {}
        for key, value in domain.items():
            if isinstance(value, (dict, list)):
                row[key] = json.dumps(value) if value else ''
            elif value is None:
                row[key] = ''
            else:
                row[key] = str(value)
        writer.writerow(row)
    
    return output.getvalue()


def export_vendors_to_csv(vendors: List[Dict]) -> str:
    """Export vendors to CSV format."""
    if not vendors:
        return ""
    
    output = io.StringIO()
    
    fieldnames = ['id', 'vendor_name', 'vendor_type', 'domain_count',
                  'shared_infrastructure', 'payment_processors',
                  'first_seen', 'last_seen', 'cluster_id']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    
    for vendor in vendors:
        row = {}
        for key in fieldnames:
            value = vendor.get(key)
            if isinstance(value, (dict, list)):
                row[key] = json.dumps(value) if value else ''
            elif value is None:
                row[key] = ''
            else:
                row[key] = str(value)
        writer.writerow(row)
    
    return output.getvalue()


def export_to_json(data: List[Dict], pretty: bool = False) -> str:
    """Export data to JSON format."""
    if pretty:
        return json.dumps(data, indent=2, default=str)
    return json.dumps(data, default=str)


def export_graph_to_graphml(nodes: List[Dict], edges: List[Dict]) -> str:
    """Export graph to GraphML format."""
    graphml = ['<?xml version="1.0" encoding="UTF-8"?>']
    graphml.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">')
    
    # Add attribute definitions
    graphml.append('  <key id="d0" for="node" attr.name="label" attr.type="string"/>')
    graphml.append('  <key id="d1" for="edge" attr.name="type" attr.type="string"/>')
    
    graphml.append('  <graph id="G" edgedefault="directed">')
    
    # Add nodes
    for node in nodes:
        node_id = node.get('id', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        label = node.get('label', 'Unknown').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        graphml.append(f'    <node id="{node_id}">')
        graphml.append(f'      <data key="d0">{label}</data>')
        graphml.append('    </node>')
    
    # Add edges
    for i, edge in enumerate(edges):
        source = edge.get('source', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        target = edge.get('target', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        edge_type = edge.get('type', 'RELATED').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        graphml.append(f'    <edge id="e{i}" source="{source}" target="{target}">')
        graphml.append(f'      <data key="d1">{edge_type}</data>')
        graphml.append('    </edge>')
    
    graphml.append('  </graph>')
    graphml.append('</graphml>')
    
    return '\n'.join(graphml)


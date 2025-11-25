// D3.js graph visualization for PersonaForge

let graphData = { nodes: [], edges: [] };
let svg, simulation;
let width, height;
let selectedNode = null;
let graphNodes, graphEdges, graphLabels; // Store references for filtering

// Get filter state
function getFilterState() {
  return {
    domains: document.getElementById('filter-domains')?.checked ?? true,
    vendors: document.getElementById('filter-vendors')?.checked ?? true,
    hosts: document.getElementById('filter-hosts')?.checked ?? true,
    cdns: document.getElementById('filter-cdns')?.checked ?? true,
    payment: document.getElementById('filter-payment')?.checked ?? true,
    clusters: true // Always show clusters
  };
}

// Check if node should be visible based on filters
function isNodeVisible(node, filters) {
  const label = node.label;
  if (label === 'Domain') return filters.domains;
  if (label === 'Vendor') return filters.vendors;
  if (label === 'Host') return filters.hosts;
  if (label === 'CDN') return filters.cdns;
  if (label === 'PaymentProcessor') return filters.payment;
  if (label === 'Cluster') return filters.clusters;
  return true;
}

// Apply filters to graph
function applyFilters() {
  const filters = getFilterState();
  
  if (!graphNodes || !graphEdges || !graphLabels) return;
  
  // Update node visibility
  graphNodes.style('opacity', d => isNodeVisible(d, filters) ? 1 : 0)
    .style('pointer-events', d => isNodeVisible(d, filters) ? 'all' : 'none');
  
  // Update label visibility
  graphLabels.style('opacity', d => isNodeVisible(d, filters) ? 1 : 0)
    .style('pointer-events', d => isNodeVisible(d, filters) ? 'all' : 'none');
  
  // Update edge visibility (only show if both source and target are visible)
  graphEdges.style('opacity', d => {
    const sourceVisible = isNodeVisible(d.source, filters);
    const targetVisible = isNodeVisible(d.target, filters);
    return (sourceVisible && targetVisible) ? 0.6 : 0;
  });
}

// Initialize visualization
function initVisualization() {
  const container = d3.select('.graph-container');
  width = container.node().offsetWidth;
  height = container.node().offsetHeight;

  svg = d3.select('#graph-svg')
    .attr('width', width)
    .attr('height', height);

  // Add zoom behavior
  const zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      svg.select('g').attr('transform', event.transform);
    });

  svg.call(zoom);

  // Create container group
  const g = svg.append('g');

  // Load graph data
  loadGraphData();
}

// Load graph data from API
async function loadGraphData() {
  try {
    // Load stats from homepage-stats API (works even without Neo4j)
    const statsResponse = await fetch('/api/homepage-stats');
    const statsData = await statsResponse.json();
    
    // Update stats from homepage API
    updateStatsFromHomepage(statsData);
    
    // Try to load graph data from Neo4j
    const response = await fetch('/api/graph');
    const data = await response.json();
    
    if (data.nodes && data.edges && data.nodes.length > 0) {
      graphData = data;
      renderGraph();
    } else {
      console.warn('No graph data available:', data.message || 'Neo4j not configured');
      showEmptyState();
    }
  } catch (error) {
    console.error('Error loading graph data:', error);
    showEmptyState();
  }
}

// Update statistics from homepage-stats API
function updateStatsFromHomepage(statsData) {
  const domainCount = statsData.total_domains || 0;
  // Use top_vendors count if vendors table is empty
  let vendorCount = statsData.total_vendors || 0;
  if (vendorCount === 0 && statsData.top_vendors && statsData.top_vendors.length > 0) {
    vendorCount = statsData.top_vendors.length;
  }
  const clusterCount = statsData.infrastructure_clusters || 0;
  
  const domainEl = document.getElementById('domain-count');
  const vendorEl = document.getElementById('vendor-count');
  const clusterEl = document.getElementById('cluster-count');
  
  if (domainEl) domainEl.textContent = domainCount;
  if (vendorEl) vendorEl.textContent = vendorCount;
  if (clusterEl) clusterEl.textContent = clusterCount;
  
  console.log('Updated dashboard stats:', { domainCount, vendorCount, clusterCount });
}

// Update statistics from graph data (legacy, for Neo4j)
function updateStats(data) {
  const domainCount = data.nodes.filter(n => n.label === 'Domain').length;
  const vendorCount = data.nodes.filter(n => n.label === 'Vendor').length;
  
  document.getElementById('domain-count').textContent = domainCount;
  document.getElementById('vendor-count').textContent = vendorCount;
  document.getElementById('cluster-count').textContent = '0'; // TODO: Calculate from clusters
}

// Render the graph
function renderGraph() {
  const g = svg.select('g');
  
  // Clear existing
  g.selectAll('*').remove();

  if (graphData.nodes.length === 0) {
    showEmptyState();
    return;
  }

  // Create force simulation with better clustering
  simulation = d3.forceSimulation(graphData.nodes)
    .force('link', d3.forceLink(graphData.edges).id(d => d.id)
      .distance(d => {
        // Shorter distance for cluster relationships
        if (d.type === 'IN_CLUSTER') return 50;
        if (d.type === 'OWNED_BY') return 80;
        return 120;
      })
      .strength(0.5))
    .force('charge', d3.forceManyBody().strength(d => {
      // Stronger repulsion for clusters and vendors (centers)
      if (d.label === 'Cluster' || d.label === 'Vendor') return -800;
      if (d.label === 'Host' || d.label === 'CDN' || d.label === 'PaymentProcessor') return -400;
      return -200; // Domains have less repulsion
    }))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => {
      // Larger collision radius for important nodes
      if (d.label === 'Cluster') return 60;
      if (d.label === 'Vendor') return 40;
      if (d.label === 'Host' || d.label === 'CDN' || d.label === 'PaymentProcessor') return 25;
      return 15;
    }))
    .force('x', d3.forceX(width / 2).strength(0.05))
    .force('y', d3.forceY(height / 2).strength(0.05));

  // Draw edges (store reference for filtering)
  graphEdges = g.append('g')
    .selectAll('line')
    .data(graphData.edges)
    .enter()
    .append('line')
    .attr('stroke', '#4a5568')
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.6);

  // Draw nodes (store reference for filtering)
  graphNodes = g.append('g')
    .selectAll('circle')
    .data(graphData.nodes)
    .enter()
    .append('circle')
    .attr('r', d => getNodeRadius(d))
    .attr('fill', d => getNodeColor(d))
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .style('cursor', 'pointer')
    .call(drag(simulation))
    .on('click', (event, d) => showNodeDetails(d))
    .on('mouseover', (event, d) => showTooltip(event, d))
    .on('mouseout', hideTooltip);

  // Add labels (store reference for filtering)
  graphLabels = g.append('g')
    .selectAll('text')
    .data(graphData.nodes)
    .enter()
    .append('text')
    .text(d => getNodeLabel(d))
    .attr('font-size', '10px')
    .attr('fill', '#9aa0a6')
    .attr('text-anchor', 'middle')
    .attr('dy', d => getNodeRadius(d) + 12);

  // Apply initial filters
  applyFilters();

  // Update positions on simulation tick
  simulation.on('tick', () => {
    graphEdges
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);

    graphNodes
      .attr('cx', d => d.x)
      .attr('cy', d => d.y);

    graphLabels
      .attr('x', d => d.x)
      .attr('y', d => d.y);
  });
}

// Get node radius based on type
function getNodeRadius(node) {
  const sizes = {
    'Domain': 6,
    'Vendor': 14,
    'Host': 10,
    'CDN': 10,
    'PaymentProcessor': 10,
    'Cluster': 18  // Larger for clusters
  };
  return sizes[node.label] || 8;
}

// Get node color based on type
function getNodeColor(node) {
  const colors = {
    'Domain': '#ff6b6b',
    'Vendor': '#4ecdc4',
    'Host': '#95e1d3',
    'CDN': '#f38181',
    'PaymentProcessor': '#aa96da',
    'Cluster': '#ffd93d'  // Yellow for clusters
  };
  return colors[node.label] || '#9aa0a6';
}

// Get node label
function getNodeLabel(node) {
  if (node.properties) {
    return node.properties.domain || node.properties.name || node.id;
  }
  return node.id;
}

// Drag behavior
function drag(simulation) {
  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
  }

  function dragged(event) {
    event.subject.fx = event.x;
    event.subject.fy = event.y;
  }

  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
  }

  return d3.drag()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended);
}

// Show tooltip
function showTooltip(event, node) {
  const tooltip = d3.select('#tooltip');
  tooltip
    .style('display', 'block')
    .style('left', (event.pageX + 10) + 'px')
    .style('top', (event.pageY - 10) + 'px')
    .html(`<strong>${node.label}</strong><br>${getNodeLabel(node)}`);
}

// Hide tooltip
function hideTooltip() {
  d3.select('#tooltip').style('display', 'none');
}

// Show node details in modal
function showNodeDetails(node) {
  const modal = document.getElementById('node-modal');
  const body = document.getElementById('modal-body');
  
  const nodeName = getNodeLabel(node);
  const nodeType = node.label;
  
  // Get node color for badge
  const nodeColor = getNodeColor(node);
  
  let html = `
    <div class="modal-header">
      <h2>
        <span>${nodeName}</span>
        <span class="node-type-badge" style="background: ${nodeColor}20; color: ${nodeColor}; border: 1px solid ${nodeColor}40;">
          ${nodeType}
        </span>
      </h2>
    </div>
    <div id="modal-body">
  `;
  
  // Format properties based on node type
  if (node.properties) {
    if (nodeType === 'Cluster') {
      html += '<div class="modal-section">';
      html += '<div class="modal-section-title">Cluster Information</div>';
      
      if (node.properties.domain_count) {
        html += `
          <div class="modal-property">
            <div class="modal-property-label">Domains in Cluster</div>
            <div class="modal-property-value highlight">${node.properties.domain_count}</div>
          </div>
        `;
      }
      
      // Show actual domain names in the cluster
      if (node.properties.domains && Array.isArray(node.properties.domains) && node.properties.domains.length > 0) {
        html += '<div class="modal-property">';
        html += '<div class="modal-property-label">Domain Names</div>';
        html += '<div class="modal-property-value">';
        html += '<ul class="modal-list">';
        node.properties.domains.forEach(domain => {
          html += `<li class="modal-list-item">${domain}</li>`;
        });
        html += '</ul>';
        html += '</div></div>';
      }
      
      if (node.properties.signature) {
        const signatureParts = node.properties.signature.split('|');
        html += '<div class="modal-property">';
        html += '<div class="modal-property-label">Shared Infrastructure</div>';
        html += '<div class="modal-property-value">';
        signatureParts.forEach(part => {
          const [type, value] = part.split(':');
          html += `<div style="margin: 0.5rem 0; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 4px;">
            <span style="color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase;">${type}:</span>
            <span style="color: var(--text-main); margin-left: 0.5rem;">${value}</span>
          </div>`;
        });
        html += '</div></div>';
      }
      
      html += '</div>';
    } else if (nodeType === 'Domain') {
      html += '<div class="modal-section">';
      html += '<div class="modal-section-title">Domain Information</div>';
      
      if (node.properties.domain) {
        html += `
          <div class="modal-property">
            <div class="modal-property-label">Domain</div>
            <div class="modal-property-value highlight">${node.properties.domain}</div>
          </div>
        `;
      }
      
      if (node.properties.vendor_type) {
        html += `
          <div class="modal-property">
            <div class="modal-property-label">Vendor Type</div>
            <div class="modal-property-value">${node.properties.vendor_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
          </div>
        `;
      }
      
      if (node.properties.risk_score !== undefined && node.properties.risk_score !== null) {
        const risk = node.properties.risk_score;
        const riskColor = risk >= 70 ? '#ff4444' : risk >= 40 ? '#ff8844' : '#999';
        html += `
          <div class="modal-property">
            <div class="modal-property-label">Risk Score</div>
            <div class="modal-property-value" style="color: ${riskColor}; font-weight: 600;">${risk}/100</div>
          </div>
        `;
      }
      
      html += '</div>';
    } else if (nodeType === 'Vendor') {
      html += '<div class="modal-section">';
      html += '<div class="modal-section-title">Vendor Information</div>';
      
      if (node.properties.name) {
        html += `
          <div class="modal-property">
            <div class="modal-property-label">Name</div>
            <div class="modal-property-value highlight">${node.properties.name}</div>
          </div>
        `;
      }
      
      if (node.properties.vendor_type) {
        html += `
          <div class="modal-property">
            <div class="modal-property-label">Type</div>
            <div class="modal-property-value">${node.properties.vendor_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
          </div>
        `;
      }
      
      html += '</div>';
    } else if (nodeType === 'Host' || nodeType === 'CDN' || nodeType === 'PaymentProcessor') {
      html += '<div class="modal-section">';
      html += '<div class="modal-section-title">Details</div>';
      
      if (node.properties.name) {
        html += `
          <div class="modal-property">
            <div class="modal-property-label">Name</div>
            <div class="modal-property-value highlight">${node.properties.name}</div>
          </div>
        `;
      }
      
      if (node.properties.domain_count !== undefined) {
        html += `
          <div class="modal-property">
            <div class="modal-property-label">Domain Count</div>
            <div class="modal-property-value highlight">${node.properties.domain_count}</div>
          </div>
        `;
      }
      
      // Show associated domains
      if (node.properties.domains && Array.isArray(node.properties.domains) && node.properties.domains.length > 0) {
        html += '<div class="modal-property">';
        html += '<div class="modal-property-label">Associated Domains</div>';
        html += '<div class="modal-property-value">';
        html += '<ul class="modal-list">';
        node.properties.domains.forEach(domain => {
          html += `<li class="modal-list-item">${domain}</li>`;
        });
        html += '</ul>';
        html += '</div></div>';
      }
      
      html += '</div>';
    } else {
      // Generic properties for other node types
      html += '<div class="modal-section">';
      html += '<div class="modal-section-title">Details</div>';
      
      for (const [key, value] of Object.entries(node.properties)) {
        if (value !== null && value !== undefined && value !== '' && key !== 'domains') {
          const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          html += `
            <div class="modal-property">
              <div class="modal-property-label">${formattedKey}</div>
              <div class="modal-property-value">${value}</div>
            </div>
          `;
        }
      }
      
      html += '</div>';
    }
  }
  
  html += '</div>';
  
  // Update modal structure
  const modalContent = modal.querySelector('.modal-content');
  modalContent.innerHTML = `
    <span class="modal-close">&times;</span>
    ${html}
  `;
  
  // Attach close handler
  const closeBtn = modalContent.querySelector('.modal-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      modal.style.display = 'none';
    });
  }
  
  // Close on background click
  const handleBackgroundClick = (e) => {
    if (e.target === modal) {
      modal.style.display = 'none';
    }
  };
  modal.addEventListener('click', handleBackgroundClick);
  
  modal.style.display = 'flex';
  
  modal.style.display = 'flex';
}

// Show empty state
function showEmptyState() {
  const g = svg.select('g');
  g.selectAll('*').remove();
  
  g.append('text')
    .attr('x', width / 2)
    .attr('y', height / 2)
    .attr('text-anchor', 'middle')
    .attr('fill', '#9aa0a6')
    .text('No graph data available. Enrich some domains to see the network.');
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
  // Load stats immediately on page load
  fetch('/api/homepage-stats')
    .then(res => res.json())
    .then(data => {
      updateStatsFromHomepage(data);
    })
    .catch(err => console.error('Error loading stats:', err));
  
  initVisualization();
  
  // Refresh button
  document.getElementById('refresh-btn')?.addEventListener('click', () => {
    loadGraphData();
  });
  
  // Reset zoom button
  document.getElementById('reset-zoom-btn')?.addEventListener('click', () => {
    svg.transition().call(
      d3.zoom().transform,
      d3.zoomIdentity
    );
  });
  
  // Modal close is handled in showNodeDetails function
  
  // Search
  document.getElementById('graph-search')?.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    if (!graphNodes || !graphLabels) return;
    
    if (query === '') {
      // Reset visibility when search is cleared
      applyFilters();
      return;
    }
    
    // Filter nodes by search query
    graphNodes.style('opacity', d => {
      const label = getNodeLabel(d).toLowerCase();
      const visible = label.includes(query) && isNodeVisible(d, getFilterState());
      return visible ? 1 : 0;
    }).style('pointer-events', d => {
      const label = getNodeLabel(d).toLowerCase();
      return label.includes(query) && isNodeVisible(d, getFilterState()) ? 'all' : 'none';
    });
    
    graphLabels.style('opacity', d => {
      const label = getNodeLabel(d).toLowerCase();
      return label.includes(query) && isNodeVisible(d, getFilterState()) ? 1 : 0;
    });
    
    // Hide edges if either node is hidden
    graphEdges.style('opacity', d => {
      const sourceLabel = getNodeLabel(d.source).toLowerCase();
      const targetLabel = getNodeLabel(d.target).toLowerCase();
      const sourceVisible = sourceLabel.includes(query) && isNodeVisible(d.source, getFilterState());
      const targetVisible = targetLabel.includes(query) && isNodeVisible(d.target, getFilterState());
      return (sourceVisible && targetVisible) ? 0.6 : 0;
    });
  });
  
  // Filter checkboxes
  ['filter-domains', 'filter-vendors', 'filter-hosts', 'filter-cdns', 'filter-payment'].forEach(filterId => {
    document.getElementById(filterId)?.addEventListener('change', () => {
      applyFilters();
      // Re-apply search if active
      const searchInput = document.getElementById('graph-search');
      if (searchInput && searchInput.value) {
        searchInput.dispatchEvent(new Event('input'));
      }
    });
  });
  
  // Window resize
  window.addEventListener('resize', () => {
    width = d3.select('.graph-container').node().offsetWidth;
    height = d3.select('.graph-container').node().offsetHeight;
    svg.attr('width', width).attr('height', height);
    if (simulation) {
      simulation.force('center', d3.forceCenter(width / 2, height / 2));
      simulation.alpha(1).restart();
    }
  });
  
  // CSV Upload
  const csvUpload = document.getElementById('csv-upload');
  const uploadBtn = document.getElementById('upload-btn');
  const uploadStatus = document.getElementById('upload-status');
  
  uploadBtn?.addEventListener('click', () => {
    csvUpload?.click();
  });
  
  csvUpload?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    uploadStatus.style.display = 'block';
    uploadStatus.textContent = 'Uploading...';
    uploadBtn.disabled = true;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('/api/upload-csv', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      
      if (result.error) {
        uploadStatus.textContent = `Error: ${result.error}`;
        uploadStatus.style.color = '#ff6b6b';
      } else {
        uploadStatus.textContent = `Success: ${result.enriched} domains enriched`;
        uploadStatus.style.color = '#4ecdc4';
        // Refresh graph after upload
        setTimeout(() => loadGraphData(), 1000);
      }
    } catch (error) {
      uploadStatus.textContent = `Error: ${error.message}`;
      uploadStatus.style.color = '#ff6b6b';
    } finally {
      uploadBtn.disabled = false;
      csvUpload.value = '';
    }
  });
});


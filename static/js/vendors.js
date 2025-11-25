// Vendors page JavaScript

let vendors = [];
let clusters = [];

// Load vendors data
async function loadVendors() {
  try {
    const minDomains = document.getElementById('min-domains')?.value || 1;
    const response = await fetch(`/api/vendors?min_domains=${minDomains}`);
    const data = await response.json();
    
    if (data.vendors) {
      vendors = data.vendors;
      renderVendors();
      updateStats();
    }
  } catch (error) {
    console.error('Error loading vendors:', error);
    document.getElementById('vendors-container').innerHTML = 
      '<div class="loading">Error loading vendors. Please try again.</div>';
  }
}

// Load clusters data
async function loadClusters() {
  try {
    const minDomains = parseInt(document.getElementById('min-domains')?.value || 2);
    
    // Load both clusters and homepage stats for consistency
    const [clustersResponse, statsResponse] = await Promise.all([
      fetch('/api/clusters'),
      fetch('/api/homepage-stats')
    ]);
    
    const clustersData = await clustersResponse.json();
    const statsData = await statsResponse.json();
    
    if (clustersData.clusters) {
      // Filter clusters by min domains
      clusters = clustersData.clusters.filter(c => (c.domain_count || 0) >= minDomains);
      renderClusters();
    }
    
    // Update stats from homepage-stats API for consistency
    if (statsData) {
      updateStatsFromHomepage(statsData);
    } else {
      updateStats();
    }
  } catch (error) {
    console.error('Error loading clusters:', error);
    document.getElementById('clusters-container').innerHTML = 
      '<div class="loading" style="color: #ff4444;">Error loading clusters. Please try again.</div>';
    updateStats(); // Fallback to cluster-based stats
  }
}

// Update stats from homepage-stats API (for consistency)
function updateStatsFromHomepage(data) {
  document.getElementById('total-domains').textContent = data.total_domains || 0;
  
  // Use top_vendors count if vendors table is empty
  let vendorCount = data.total_vendors || 0;
  if (vendorCount === 0 && data.top_vendors && data.top_vendors.length > 0) {
    vendorCount = data.top_vendors.length;
  }
  document.getElementById('total-vendors').textContent = vendorCount;
  
  document.getElementById('total-high-risk').textContent = data.high_risk_domains || 0;
  document.getElementById('total-clusters').textContent = clusters.length; // Use filtered clusters count
}

// Render vendors list (deprecated - now using clusters)
function renderVendors() {
  // This function is kept for compatibility but vendors are now shown in clusters
  return;
}

// Render clusters
function renderClusters() {
  const container = document.getElementById('clusters-container');
  
  if (clusters.length === 0) {
    container.innerHTML = `
      <div style="background: rgba(255, 68, 68, 0.1); border: 1px solid rgba(255, 68, 68, 0.3); border-radius: 8px; padding: 2rem; text-align: center;">
        <p style="color: #999; margin-bottom: 1rem;">No clusters found matching the current filter.</p>
        <p style="color: #666; font-size: 0.9rem;">
          Try lowering the "Min Domains" filter, or visit the <a href="/dashboard" style="color: #ff4444;">Dashboard</a> to see the network graph.
        </p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = clusters.map(cluster => {
    // Format infrastructure signature nicely
    const infrastructure = cluster.infrastructure || [];
    const infraDisplay = infrastructure.map(infra => {
      const [type, value] = infra.split(':');
      return `<span style="display: inline-block; margin: 0.25rem 0.5rem 0.25rem 0; padding: 0.25rem 0.75rem; background: rgba(255, 68, 68, 0.1); border-radius: 4px; font-size: 0.85rem;">
        <strong style="color: #ff4444; text-transform: uppercase;">${type}:</strong> ${value}
      </span>`;
    }).join('');
    
    return `
      <div class="cluster-card" style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
          <div>
            <h3 style="margin: 0 0 0.5rem 0; color: #fff; font-size: 1.1rem;">Cluster (${cluster.domain_count || 0} domains)</h3>
            <p style="color: #999; font-size: 0.85rem; margin: 0;">Shared infrastructure grouping</p>
          </div>
          <div style="background: rgba(255, 68, 68, 0.2); color: #ff4444; padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.85rem; font-weight: 600;">
            ${cluster.domain_count || 0} domains
          </div>
        </div>
        
        <div style="margin-bottom: 1rem;">
          <p style="color: #999; font-size: 0.85rem; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;">Shared Infrastructure</p>
          <div style="margin-bottom: 1rem;">
            ${infraDisplay || '<span style="color: #666;">No infrastructure data</span>'}
          </div>
        </div>
        
        <div>
          <p style="color: #999; font-size: 0.85rem; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;">Domains in Cluster</p>
          <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
            ${(cluster.domains || []).map(domain => `
              <span style="display: inline-block; padding: 0.4rem 0.8rem; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 4px; font-size: 0.9rem; color: #fff; font-family: monospace;">
                ${domain}
              </span>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// Update statistics
function updateStats() {
  // Count unique vendor types from clusters
  const vendorTypes = new Set();
  clusters.forEach(cluster => {
    if (cluster.vendor_types && Array.isArray(cluster.vendor_types)) {
      cluster.vendor_types.forEach(vt => vendorTypes.add(vt));
    }
  });
  
  document.getElementById('total-vendors').textContent = vendorTypes.size;
  document.getElementById('total-clusters').textContent = clusters.length;
  
  // Calculate total unique domains from clusters
  const allDomains = new Set();
  clusters.forEach(cluster => {
    if (cluster.domains && Array.isArray(cluster.domains)) {
      cluster.domains.forEach(domain => allDomains.add(domain));
    }
  });
  document.getElementById('total-domains').textContent = allDomains.size;
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
  // Load clusters (main data)
  loadClusters();
  
  // Refresh button
  document.getElementById('refresh-vendors')?.addEventListener('click', () => {
    loadClusters();
  });
  
  // Min domains filter - update clusters when changed
  document.getElementById('min-domains')?.addEventListener('change', () => {
    loadClusters();
  });
  
  // Also trigger on input for real-time filtering
  document.getElementById('min-domains')?.addEventListener('input', () => {
    loadClusters();
  });
});


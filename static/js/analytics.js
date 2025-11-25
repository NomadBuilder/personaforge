// Analytics page JavaScript

let analyticsData = null;

// Load analytics data
async function loadAnalytics() {
  try {
    const response = await fetch('/api/analytics');
    const data = await response.json();
    
    if (data.error) {
      console.error('Error loading analytics:', data.error);
      showError(data.error);
      return;
    }
    
    analyticsData = data;
    renderAnalytics();
  } catch (error) {
    console.error('Error loading analytics:', error);
    showError('Failed to load analytics data');
  }
}

// Render analytics
function renderAnalytics() {
  if (!analyticsData) return;
  
  const summary = analyticsData.summary || {};
  
  // Update summary stats
  document.getElementById('total-domains').textContent = summary.total_domains || 0;
  document.getElementById('total-vendors').textContent = summary.total_vendors || 0;
  document.getElementById('domains-enriched').textContent = summary.domains_with_enrichment || 0;
  document.getElementById('domains-typed').textContent = summary.domains_with_vendor_type || 0;
  
  // Render vendor types
  renderVendorTypes(analyticsData.vendor_types || {});
  
  // Render top infrastructure
  renderTopList('top-hosts', analyticsData.top_hosts || []);
  renderTopList('top-cdns', analyticsData.top_cdns || []);
  renderTopList('top-registrars', analyticsData.top_registrars || []);
  renderTopList('top-payment', analyticsData.top_payment_processors || []);
  
  // Render top vendors
  renderTopVendors(analyticsData.top_vendors || []);
}

// Render vendor types chart
function renderVendorTypes(vendorTypes) {
  const container = document.getElementById('vendor-types-chart');
  
  if (Object.keys(vendorTypes).length === 0) {
    container.innerHTML = '<div class="loading">No vendor type data available</div>';
    return;
  }
  
  const total = Object.values(vendorTypes).reduce((sum, count) => sum + count, 0);
  
  let html = '<div class="vendor-types-list">';
  for (const [type, count] of Object.entries(vendorTypes)) {
    const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
    html += `
      <div class="vendor-type-item">
        <div class="vendor-type-header">
          <span class="vendor-type-name">${type || 'Unknown'}</span>
          <span class="vendor-type-count">${count} (${percentage}%)</span>
        </div>
        <div class="vendor-type-bar">
          <div class="vendor-type-bar-fill" style="width: ${percentage}%;"></div>
        </div>
      </div>
    `;
  }
  html += '</div>';
  
  container.innerHTML = html;
}

// Render top list
function renderTopList(containerId, items) {
  const container = document.getElementById(containerId);
  
  if (items.length === 0) {
    container.innerHTML = '<div class="loading">No data available</div>';
    return;
  }
  
  let html = '<ul class="top-list">';
  for (const item of items.slice(0, 10)) {
    html += `
      <li class="top-list-item">
        <span class="top-list-name">${item.name || 'Unknown'}</span>
        <span class="top-list-count">${item.count}</span>
      </li>
    `;
  }
  html += '</ul>';
  
  container.innerHTML = html;
}

// Render top vendors
function renderTopVendors(vendors) {
  const container = document.getElementById('top-vendors');
  
  if (vendors.length === 0) {
    container.innerHTML = '<div class="loading">No vendors found</div>';
    return;
  }
  
  container.innerHTML = vendors.map(vendor => `
    <div class="vendor-card">
      <h3>${vendor.name || 'Unknown Vendor'}</h3>
      <p><strong>Type:</strong> ${vendor.type || 'Unknown'}</p>
      <p><strong>Domain Count:</strong> ${vendor.domain_count || 0}</p>
    </div>
  `).join('');
}

// Show error
function showError(message) {
  const containers = document.querySelectorAll('.loading, .chart-container, .list-container, .vendors-container');
  containers.forEach(container => {
    container.innerHTML = `<div class="loading" style="color: #ff6b6b;">Error: ${message}</div>`;
  });
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
  loadAnalytics();
  
  // Auto-refresh every 30 seconds
  setInterval(loadAnalytics, 30000);
});


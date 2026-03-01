/**
 * INDRA - Intelligent Network Data ROI Analytics
 * Enhanced Prototype with Database Integration
 * Campaign Intelligence Platform for Strategic Decision Making
 */
let currentMetrics = {};

// ==================== DOM ELEMENTS ====================
function showSection(id) {
    document.querySelectorAll('.section').forEach(el => el.style.display = 'none');
    document.getElementById(id).style.display = 'block';
    if(id === 'dashboard') loadDashboard();
    if(id === 'history') loadHistory();
}

// Form and UI Elements
const form = document.getElementById('analyzeForm');
const resetBtn = document.getElementById('resetBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const saveCampaignBtn = document.getElementById('saveCampaignBtn');
const generateDetailedReportBtn = document.getElementById('generateDetailedReportBtn');
const exportSelectedCsv = document.getElementById('exportSelectedCsv');
const resultsContainer = document.getElementById('resultsContainer');
const resultsCard = document.getElementById('resultsCard');
const emptyState = document.getElementById('emptyState');
const errorState = document.getElementById('errorState');
const errorMessage = document.getElementById('errorMessage');

// Chart elements
const financialChartCanvas = document.getElementById('financialChart');

let financialChart = null;
let trendChart = null;
// New Charts
let channelRoiChart = null;
let channelCacChart = null;
let revenuePieChart = null;
let abTestChart = null;

// ==================== NAVIGATION BUTTONS ====================

const dashboardBtn = document.getElementById('dashboardBtn');
const historyBtn = document.getElementById('historyBtn');
const closeDashboard = document.getElementById('closeDashboard');
const closeHistory = document.getElementById('closeHistory');
const closeComparison = document.getElementById('closeComparison');
const exportAllCsv = document.getElementById('exportAllCsv');
const compareSelected = document.getElementById('compareSelected');

// Theme toggle
const themeToggle = document.getElementById('themeToggle');
const helpBtn = document.getElementById('helpBtn');
const settingsBtn = document.getElementById('settingsBtn');
const downloadTemplateBtn = document.getElementById('downloadTemplateBtn');

// ==================== FILE UPLOAD ====================

const csvFileInput = document.getElementById('csvFileInput');
const fileNameSpan = document.getElementById('fileName');

// ==================== SETTINGS ====================

const settingsModal = document.getElementById('settingsModal');
const closeSettings = document.getElementById('closeSettings');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');
const currencyInput = document.getElementById('currencySymbol');
const revenueColorInput = document.getElementById('revenueColor');
const costColorInput = document.getElementById('costColor');

// ==================== SECTIONS ====================

const mainContent = document.getElementById('mainContent');
const dashboardSection = document.getElementById('dashboardSection');
const historySection = document.getElementById('historySection');
const comparisonSection = document.getElementById('comparisonSection');

// ==================== RESULT ELEMENTS ====================

const ctrValue = document.getElementById('ctrValue');
const conversionValue = document.getElementById('conversionValue');
const roiValue = document.getElementById('roiValue');
const ctrBar = document.getElementById('ctrBar');
const conversionBar = document.getElementById('conversionBar');
const roiBar = document.getElementById('roiBar');

// A/B Test Results elements
const abTestResultsSection = document.getElementById('abTestResultsSection');
const abTestResults = document.getElementById('abTestResults');
const channelPerformanceSection = document.getElementById('channelPerformanceSection');
const channelPerformance = document.getElementById('channelPerformance');

// Additional metric elements
const impressionsValue = document.getElementById('impressionsValue');
const clicksValue = document.getElementById('clicksValue');
const conversionsValue = document.getElementById('conversionsValue');
const revenueValue = document.getElementById('revenueValue');
const costValue = document.getElementById('costValue');
const netProfitValue = document.getElementById('netProfitValue');
const cpcValue = document.getElementById('cpcValue');
const cpaValue = document.getElementById('cpaValue');
const rpmValue = document.getElementById('rpmValue');

// ==================== INPUT ELEMENTS ====================

const inputs = {
    campaignName: document.getElementById('campaignName'),
    channel: document.getElementById('channel'),
    testVariant: document.getElementById('testVariant'),
    testGroup: document.getElementById('testGroup'),
    testDuration: document.getElementById('testDuration'),
    sampleSize: document.getElementById('sampleSize'),
    impressions: document.getElementById('impressions'),
    clicks: document.getElementById('clicks'),
    conversions: document.getElementById('conversions'),
    revenue: document.getElementById('revenue'),
    cost: document.getElementById('cost')
};

// ==================== NEW BUTTON ELEMENTS ====================

const analyzeAbTestBtn = document.getElementById('analyzeAbTestBtn');
const compareChannelsBtn = document.getElementById('compareChannelsBtn');
const roasValue = document.getElementById('roasValue');

// ==================== STATE ====================

let currentResult = null;
let selectedCampaigns = new Set();
let comparisonChart = null;

// ==================== SETTINGS STATE ====================

let appSettings = {
    currency: '$',
    revenueColor: '#00BFFF',
    costColor: '#FF4500'
};

// ==================== MAIN ANALYZE FUNCTION ====================

async function analyze(event) {
    event.preventDefault();

    // Sanity check for form binding
    if (!form) {
        console.error('analyze: form element not found, cannot submit');
        alert('Internal error: form not initialized. Please refresh.');
        return;
    }

    hideError();
    hideResults();
    hideEmptyState();

    if (!validateInputs()) return;

    const data = {
        name: inputs.campaignName.value || `Campaign_${Date.now()}`,
        channel: inputs.channel.value || 'Direct',
        test_variant: inputs.testVariant.value || 'Control',
        test_group: inputs.testGroup.value || null,
        test_duration_days: parseInt(inputs.testDuration.value) || 7,
        sample_size: parseInt(inputs.sampleSize.value) || null,
        impressions: parseFloat(inputs.impressions.value) || 0,
        clicks: parseFloat(inputs.clicks.value) || 0,
        conversions: parseFloat(inputs.conversions.value) || 0,
        revenue: parseFloat(inputs.revenue.value) || 0,
        cost: parseFloat(inputs.cost.value) || 0
    };

    console.log("[analyze] Sending data to backend:", data);
    setLoading(true);

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        console.log("[analyze] Response status:", response.status);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Server error. Please try again.');
        }

        const result = await response.json();
        console.log("[analyze] Response data:", result);
        
        if (result.error) throw new Error(result.error);

        // Store current result for saving later
        currentResult = { ...data, ...result };
        
        displayResults(result, data);
        setLoading(false);

        // ensure user sees the results
        try {
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } catch (e) {
            /* ignore */
        }

    } catch (error) {
        console.error("Analyze error:", error);
        showError(error.message || 'An unexpected error occurred. Please check your inputs and try again.');
        setLoading(false);
    }
}

function validateInputs() {
    let isValid = true;
    
    // Basic validation
    if (parseFloat(inputs.impressions.value) < 0) isValid = false;
    if (parseFloat(inputs.clicks.value) < 0) isValid = false;
    if (parseFloat(inputs.conversions.value) < 0) isValid = false;
    
    // Logical validation
    const imp = parseFloat(inputs.impressions.value) || 0;
    const clk = parseFloat(inputs.clicks.value) || 0;
    const conv = parseFloat(inputs.conversions.value) || 0;

    if (imp > 0 && clk > imp) {
        showError('Clicks cannot exceed impressions.');
        isValid = false;
    }

    if (clk > 0 && conv > clk) {
        showError('Conversions cannot exceed clicks.');
        isValid = false;
    }

    return isValid;
}

// ==================== DASHBOARD LOGIC ====================

async function updateDashboard() {
    try {
        // Fetch Stats
        const statsRes = await fetch('/dashboard/stats');
        const statsData = await statsRes.json();
        
        if (statsData.success) {
            const s = statsData.stats;
            document.getElementById('totalCampaigns').textContent = s.total_campaigns;
            document.getElementById('totalRevenue').textContent = formatCurrency(s.total_revenue);
            document.getElementById('totalCost').textContent = formatCurrency(s.total_cost);
            document.getElementById('netProfit').textContent = formatCurrency(s.net_profit);
            document.getElementById('avgCtr').textContent = s.avg_ctr + '%';
            document.getElementById('avgRoi').textContent = s.avg_roi + '%';

            // Render Top Campaigns
            const topList = document.getElementById('topCampaignsList');
            if (topList) {
                topList.innerHTML = s.top_campaigns.map(c => `
                    <div class="campaign-item">
                        <span class="name">${c.name}</span>
                        <span class="roi ${c.roi >= 0 ? 'positive' : 'negative'}">${c.roi}% ROI</span>
                    </div>
                `).join('');
            }

            // Render Recent Campaigns
            const recentList = document.getElementById('recentCampaignsList');
            if (recentList) {
                recentList.innerHTML = s.recent_campaigns.map(c => `
                    <div class="campaign-item">
                        <span class="name">${c.name}</span>
                        <span class="date">${new Date(c.created_at).toLocaleDateString()}</span>
                    </div>
                `).join('');
            }
        }

        // Fetch Trends
        const trendRes = await fetch('/dashboard/trends');
        const trendData = await trendRes.json();

        if (trendData.success) {
            renderTrendChart(trendData.trends);
        }
        
        // Fetch Advanced Analytics
        await updateAnalyticsCharts();

    } catch (e) {
        console.error("Dashboard error:", e);
    }
}

function renderTrendChart(trends) {
    const ctx = document.getElementById('performanceTrendChart');
    if (!ctx) return;
    
    const chartCtx = ctx.getContext('2d');
    if (trendChart) trendChart.destroy();

    trendChart = new Chart(chartCtx, {
        type: 'line',
        data: {
            labels: trends.dates,
            datasets: [
                {
                    label: 'ROI (%)',
                    data: trends.roi,
                    borderColor: '#4ade80',
                    backgroundColor: 'rgba(74, 222, 128, 0.1)',
                    yAxisID: 'y',
                    tension: 0.4
                },
                {
                    label: 'Revenue',
                    data: trends.revenue,
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

async function updateAnalyticsCharts() {
    try {
        const res = await fetch('/dashboard/analytics');
        const data = await res.json();
        
        if (data.success && data.charts) {
            renderChannelRoiChart(data.charts.channel_roi);
            renderChannelCacChart(data.charts.channel_cac);
            renderRevenuePieChart(data.charts.revenue_share);
            renderAbTestChart(data.charts.variant_comparison);
            renderRecommendations(data.recommendations);
        }
    } catch (e) {
        console.error("Analytics error:", e);
    }
}

function renderChannelRoiChart(data) {
    const ctx = document.getElementById('channelRoiChart');
    if (!ctx) return;
    
    const chartCtx = ctx.getContext('2d');
    if (channelRoiChart) channelRoiChart.destroy();
    
    channelRoiChart = new Chart(chartCtx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'ROI (%)',
                data: data.data,
                backgroundColor: '#00d9ff',
                borderRadius: 4
            }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });
}

function renderChannelCacChart(data) {
    const ctx = document.getElementById('channelCacChart');
    if (!ctx) return;
    
    const chartCtx = ctx.getContext('2d');
    if (channelCacChart) channelCacChart.destroy();
    
    channelCacChart = new Chart(chartCtx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'CAC ($)',
                data: data.data,
                backgroundColor: '#fbbf24',
                borderRadius: 4
            }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });
}

function renderRevenuePieChart(data) {
    const ctx = document.getElementById('revenuePieChart');
    if (!ctx) return;
    
    const chartCtx = ctx.getContext('2d');
    if (revenuePieChart) revenuePieChart.destroy();
    
    revenuePieChart = new Chart(chartCtx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: ['#00d9ff', '#fbbf24', '#10b981', '#ef4444', '#8b5cf6'],
                borderWidth: 0
            }]
        },
        options: { responsive: true, plugins: { legend: { position: 'right' } } }
    });
}

function renderAbTestChart(data) {
    const ctx = document.getElementById('abTestChart');
    if (!ctx) return;
    
    const chartCtx = ctx.getContext('2d');
    if (abTestChart) abTestChart.destroy();
    
    abTestChart = new Chart(chartCtx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Conversion Rate (%)',
                data: data.data,
                backgroundColor: data.labels.map(l => l === 'Control' ? '#94a3b8' : '#10b981'),
                borderRadius: 4
            }]
        },
        options: { 
            responsive: true, 
            plugins: { legend: { display: false } },
            indexAxis: 'y'
        }
    });
}

function renderRecommendations(recs) {
    const container = document.getElementById('recommendationsContainer');
    if (!container) return;
    
    if (!recs || recs.length === 0) {
        container.innerHTML = '<p class="text-muted">No specific recommendations available yet. Add more data.</p>';
        return;
    }
    
    container.innerHTML = recs.map(rec => {
        // Simple markdown parsing for bold text
        const formatted = rec.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        return `
            <div class="recommendation-item">
                <p>${formatted}</p>
            </div>
        `;
    }).join('');
}

// ==================== HISTORY LOGIC ====================

async function loadHistory() {
    try {
        const res = await fetch('/campaigns');
        const data = await res.json();
        
        const list = document.getElementById('campaignList');
        if (!list) return;
        
        list.innerHTML = '';
        selectedCampaigns.clear();
        updateCompareButton();

        if (data.success && data.campaigns.length > 0) {
            data.campaigns.forEach(c => {
                const item = document.createElement('div');
                item.className = 'history-card';
                const roiClass = c.roi >= 0 ? 'positive' : 'negative';
                item.innerHTML = `
                    <input type="checkbox" class="history-card-checkbox campaign-check" data-id="${c.id}">
                    <div class="history-card-content">
                        <div class="history-card-name">${c.name}</div>
                        <div class="history-card-meta">
                            <div class="history-card-meta-item">
                                <span class="history-card-meta-label">Impressions</span>
                                <span class="history-card-meta-value"><i class="fa-solid fa-eye"></i> ${c.impressions}</span>
                            </div>
                            <div class="history-card-meta-item">
                                <span class="history-card-meta-label">Clicks</span>
                                <span class="history-card-meta-value"><i class="fa-solid fa-mouse-pointer"></i> ${c.clicks}</span>
                            </div>
                            <div class="history-card-meta-item">
                                <span class="history-card-meta-label">Revenue</span>
                                <span class="history-card-meta-value"><i class="fa-solid fa-sack-dollar"></i> ${formatCurrency(c.revenue)}</span>
                            </div>
                            <div class="history-card-meta-item">
                                <span class="history-card-meta-label">ROI</span>
                                <span class="history-card-meta-value ${roiClass}">${c.roi}%</span>
                            </div>
                            <div class="history-card-meta-item">
                                <span class="history-card-meta-label">CTR</span>
                                <span class="history-card-meta-value">${c.ctr}%</span>
                            </div>
                        </div>
                    </div>
                    <div class="history-card-actions">
                        <button class="history-card-btn delete" onclick="deleteCampaign(${c.id})" title="Delete">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                `;
                list.appendChild(item);
            });

            // Add checkbox listeners
            document.querySelectorAll('.campaign-check').forEach(cb => {
                cb.addEventListener('change', (e) => {
                    if (e.target.checked) selectedCampaigns.add(parseInt(e.target.dataset.id));
                    else selectedCampaigns.delete(parseInt(e.target.dataset.id));
                    updateCompareButton();
                });
            });
        } else {
            list.innerHTML = '<p style="text-align:center; color:var(--text-muted);">No history found.</p>';
        }
    } catch (e) {
        console.error("History error:", e);
    }
}

async function deleteCampaign(id) {
    if (!confirm('Are you sure you want to delete this campaign?')) return;
    
    try {
        await fetch(`/campaigns/${id}`, { method: 'DELETE' });
        loadHistory();
        updateDashboard();
    } catch (e) {
        alert('Failed to delete');
    }
}

function updateCompareButton() {
    if (compareSelected) {
        compareSelected.disabled = selectedCampaigns.size < 2;
    }
}

// ==================== COMPARISON LOGIC ====================

async function compareCampaigns() {
    if (selectedCampaigns.size < 2) return;

    const originalText = compareSelected.innerHTML;
    compareSelected.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Comparing...';
    compareSelected.disabled = true;

    try {
        const ids = Array.from(selectedCampaigns);
        const res = await fetch('/campaigns/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ campaign_ids: ids })
        });
        
        const data = await res.json();
        
        if (data.success) {
            // Show Modal
            comparisonSection.style.display = 'block';
            historySection.style.display = 'none';

            // Update Stats
            const s = data.comparison.summary;
            const statsEl = document.getElementById('comparisonStats');
            if (statsEl) {
                statsEl.innerHTML = `
                    <div class="stat-item"><span>Avg ROI</span><strong>${s.avg_roi}%</strong></div>
                    <div class="stat-item"><span>Avg CTR</span><strong>${s.avg_ctr}%</strong></div>
                    <div class="stat-item"><span>Total Profit</span><strong>${formatCurrency(s.net_profit)}</strong></div>
                `;
            }

            // Update Chart
            const chartRes = await fetch('/generate-comparison-chart', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ campaign_ids: ids })
            });
            
            const blob = await chartRes.blob();
            const url = URL.createObjectURL(blob);
            
            const ctx = document.getElementById('comparisonChart').getContext('2d');
            const img = new Image();
            img.onload = () => {
                ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
                ctx.canvas.width = img.width;
                ctx.canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
            };
            img.src = url;

            // Update Insights
            const resultsDiv = document.getElementById('comparisonResults');
            if (resultsDiv) {
                resultsDiv.innerHTML = data.comparison.insights.map(insight => `
                    <div class="best-performer">
                        <h4>Insight</h4>
                        <p>${insight}</p>
                    </div>
                `).join('');
            }
        }
    } catch (e) {
        console.error("Comparison error:", e);
        showError('Failed to compare campaigns: ' + e.message);
    } finally {
        compareSelected.innerHTML = originalText;
        updateCompareButton();
    }
}

// ==================== HELPERS ====================

function formatCurrency(val) {
    return appSettings.currency + parseFloat(val).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

function showInputError(input, show) {
    input.style.borderColor = show ? '#FF4500' : '';
    input.style.boxShadow = show ? '0 0 0 4px rgba(255,69,0,0.3)' : '';
}

function setLoading(loading) {
    if (analyzeBtn) {
        analyzeBtn.disabled = loading;
        analyzeBtn.classList.toggle('loading', loading);
    }
    Object.values(inputs).forEach(i => {
        if (i) i.disabled = loading;
    });
}

// ==================== RESULTS ====================

function displayResults(result, inputData) {
    console.log('[displayResults] showing results', result, inputData);
    resultsContainer.style.display = 'block';
    resultsContainer.classList.add('show');
    resultsCard.classList.add('show');
    
    // Update Badge
    document.getElementById('resultCampaignName').textContent = inputData.name;

    // Animate Bars
    animateValue(ctrValue, result['CTR (%)'], '%', 100);
    animateValue(conversionValue, result['Conversion Rate (%)'], '%', 200);
    animateValue(roiValue, result['ROI (%)'], '%', 300);
    
    // Update Progress Bars Width
    ctrBar.style.width = Math.min(result['CTR (%)'] * 10, 100) + '%';
    conversionBar.style.width = Math.min(result['Conversion Rate (%)'] * 5, 100) + '%';
    roiBar.style.width = Math.min(Math.abs(result['ROI (%)']), 100) + '%';
    roiBar.style.backgroundColor = result['ROI (%)'] >= 0 ? '#4ade80' : '#f87171';

    // Update Secondary Metrics
    impressionsValue.textContent = inputData.impressions.toLocaleString();
    clicksValue.textContent = inputData.clicks.toLocaleString();
    conversionsValue.textContent = inputData.conversions.toLocaleString();
    revenueValue.textContent = formatCurrency(inputData.revenue);
    costValue.textContent = formatCurrency(inputData.cost);
    netProfitValue.textContent = formatCurrency(inputData.revenue - inputData.cost);

    // Calculate and display ROAS
    const roas = inputData.cost > 0 ? (inputData.revenue / inputData.cost) : 0;
    roasValue.textContent = '$' + roas.toFixed(2);
    
    // Calculate additional metrics
    const cpc = inputData.clicks > 0 ? (inputData.cost / inputData.clicks) : 0;
    const cpa = inputData.conversions > 0 ? (inputData.cost / inputData.conversions) : 0;
    const rpm = inputData.impressions > 0 ? ((inputData.revenue / inputData.impressions) * 1000) : 0;
    
    cpcValue.textContent = formatCurrency(cpc);
    cpaValue.textContent = formatCurrency(cpa);
    rpmValue.textContent = formatCurrency(rpm);

    // Show A/B Test button if test group is specified
    if (inputs.testGroup.value && inputs.testGroup.value.trim()) {
        analyzeAbTestBtn.style.display = 'inline-flex';
    } else {
        analyzeAbTestBtn.style.display = 'none';
    }

    // Show Channel comparison button
    compareChannelsBtn.style.display = 'inline-flex';

    // Render Financial Chart
    renderFinancialChart(inputData.revenue, inputData.cost);
}

function renderFinancialChart(revenue, cost) {
    const ctx = financialChartCanvas.getContext('2d');
    
    if (financialChart) financialChart.destroy();

    financialChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Revenue', 'Cost'],
            datasets: [{
                label: 'Amount',
                data: [revenue, cost]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// ==================== A/B TEST ANALYSIS ====================

async function analyzeAbTest() {
    const testGroup = inputs.testGroup.value;
    if (!testGroup || !testGroup.trim()) {
        alert('Please enter a Test Group ID to analyze A/B tests.');
        return;
    }

    console.log("[analyzeAbTest] Analyzing test group:", testGroup);
    
    try {
        const response = await fetch('/ab-test/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ test_group: testGroup })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Failed to analyze A/B test');
        }

        const result = await response.json();
        console.log("[analyzeAbTest] Response:", result);

        if (result.error) {
            throw new Error(result.error);
        }

        // Display A/B Test Results
        displayAbTestResults(result);

    } catch (error) {
        console.error("A/B Test Analysis error:", error);
        alert('A/B Test Analysis failed: ' + error.message);
    }
}

function displayAbTestResults(result) {
    // Show the A/B test results section
    abTestResultsSection.style.display = 'block';
    
    if (!result.results || result.results.length === 0) {
        abTestResults.innerHTML = '<p>No A/B test results found for this test group. Make sure you have saved campaigns with the same Test Group ID.</p>';
        return;
    }

    let html = '';
    
    result.results.forEach((res, index) => {
        const isSignificant = res.statistical_test.is_significant;
        const winnerClass = res.winner === res.variant.variant ? 'winner' : 'loser';
        
        html += `
            <div class="ab-test-result-card ${winnerClass}">
                <div class="ab-test-header">
                    <h5>${res.variant.name} (${res.variant.variant}) vs ${res.control.name} (${res.control.variant})</h5>
                    <span class="ab-badge ${isSignificant ? 'significant' : 'not-significant'}">
                        ${isSignificant ? 'Statistically Significant' : 'Not Significant'}
                    </span>
                </div>
                
                <div class="ab-metrics-comparison">
                    <div class="ab-metric-column">
                        <h6>Control (${res.control.variant})</h6>
                        <div class="ab-metric">
                            <span class="label">CTR</span>
                            <span class="value">${res.control.ctr}%</span>
                        </div>
                        <div class="ab-metric">
                            <span class="label">Conversion Rate</span>
                            <span class="value">${res.control.conversion_rate}%</span>
                            <span class="ci">CI: [${res.control.conversion_rate_ci[0]}% - ${res.control.conversion_rate_ci[1]}%]</span>
                        </div>
                        <div class="ab-metric">
                            <span class="label">ROI</span>
                            <span class="value">${res.control.roi}%</span>
                        </div>
                    </div>
                    
                    <div class="ab-vs-indicator">
                        <i class="fa-solid fa-arrow-right"></i>
                    </div>
                    
                    <div class="ab-metric-column">
                        <h6>Variant (${res.variant.variant})</h6>
                        <div class="ab-metric">
                            <span class="label">CTR</span>
                            <span class="value">${res.variant.ctr}%</span>
                            <span class="lift ${res.lift.ctr_lift_percent >= 0 ? 'positive' : 'negative'}">
                                ${res.lift.ctr_lift_percent >= 0 ? '+' : ''}${res.lift.ctr_lift_percent}%
                            </span>
                        </div>
                        <div class="ab-metric">
                            <span class="label">Conversion Rate</span>
                            <span class="value">${res.variant.conversion_rate}%</span>
                            <span class="ci">CI: [${res.variant.conversion_rate_ci[0]}% - ${res.variant.conversion_rate_ci[1]}%]</span>
                            <span class="lift ${res.lift.conversion_lift_percent >= 0 ? 'positive' : 'negative'}">
                                ${res.lift.conversion_lift_percent >= 0 ? '+' : ''}${res.lift.conversion_lift_percent}%
                            </span>
                        </div>
                        <div class="ab-metric">
                            <span class="label">ROI</span>
                            <span class="value">${res.variant.roi}%</span>
                            <span class="lift ${res.lift.roi_lift_percent >= 0 ? 'positive' : 'negative'}">
                                ${res.lift.roi_lift_percent >= 0 ? '+' : ''}${res.lift.roi_lift_percent}%
                            </span>
                        </div>
                    </div>
                </div>
                
                <div class="ab-statistical-info">
                    <div class="stat-item">
                        <span class="label">Chi-Square</span>
                        <span class="value">${res.statistical_test.chi_square}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">P-Value</span>
                        <span class="value">${res.statistical_test.p_value}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">Confidence</span>
                        <span class="value">${res.statistical_test.confidence_level}</span>
                    </div>
                </div>
                
                <div class="ab-recommendation">
                    <i class="fa-solid fa-lightbulb"></i>
                    <span>${res.recommendation}</span>
                </div>
                
                <div class="ab-winner">
                    <strong>Winner:</strong> ${res.winner}
                </div>
            </div>
        `;
    });

    abTestResults.innerHTML = html;
    
    // Scroll to A/B test results
    abTestResultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ==================== CHANNEL COMPARISON ====================

async function compareChannels() {
    console.log("[compareChannels] Comparing channels");
    
    try {
        const response = await fetch('/channels/comparison', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channels: [] })  // Empty will get all channels
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Failed to compare channels');
        }

        const result = await response.json();
        console.log("[compareChannels] Response:", result);

        if (result.error) {
            throw new Error(result.error);
        }

        // Display Channel Performance
        displayChannelPerformance(result);

    } catch (error) {
        console.error("Channel Comparison error:", error);
        alert('Channel Comparison failed: ' + error.message);
    }
}

function displayChannelPerformance(result) {
    // Show the channel performance section
    channelPerformanceSection.style.display = 'block';
    
    if (!result.channel_comparison || result.channel_comparison.length === 0) {
        channelPerformance.innerHTML = '<p>No channel data found.</p>';
        return;
    }

    let html = '<div class="channel-cards-grid">';
    
    result.channel_comparison.forEach(channel => {
        html += `
            <div class="channel-card">
                <div class="channel-header">
                    <h5><i class="fa-solid fa-share-nodes"></i> ${channel.channel}</h5>
                </div>
                <div class="channel-metrics">
                    <div class="channel-metric">
                        <span class="label">Campaigns</span>
                        <span class="value">${channel.total_campaigns}</span>
                    </div>
                    <div class="channel-metric">
                        <span class="label">Total Revenue</span>
                        <span class="value">${formatCurrency(channel.total_revenue)}</span>
                    </div>
                    <div class="channel-metric">
                        <span class="label">Total Cost</span>
                        <span class="value">${formatCurrency(channel.total_cost)}</span>
                    </div>
                    <div class="channel-metric">
                        <span class="label">Net Profit</span>
                        <span class="value ${channel.net_profit >= 0 ? 'positive' : 'negative'}">${formatCurrency(channel.net_profit)}</span>
                    </div>
                    <div class="channel-metric">
                        <span class="label">Avg CTR</span>
                        <span class="value">${channel.avg_ctr}%</span>
                    </div>
                    <div class="channel-metric">
                        <span class="label">Avg Conversion</span>
                        <span class="value">${channel.avg_conversion_rate}%</span>
                    </div>
                    <div class="channel-metric highlight">
                        <span class="label">Avg ROI</span>
                        <span class="value">${channel.avg_roi}%</span>
                    </div>
                    <div class="channel-metric">
                        <span class="label">ROAS</span>
                        <span class="value">${channel.roas}x</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    
    // Add ranked channels info
    if (result.ranked_by_roi && result.ranked_by_roi.length > 0) {
        html += `
            <div class="channel-ranking">
                <h5><i class="fa-solid fa-trophy"></i> Channels Ranked by ROI</h5>
                <ol>
                    ${result.ranked_by_roi.map((c, i) => `<li>${c.channel} - ${c.avg_roi}% ROI</li>`).join('')}
                </ol>
            </div>
        `;
    }

    channelPerformance.innerHTML = html;
    
    // Scroll to channel performance section
    channelPerformanceSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ==================== HELPER FUNCTIONS ====================

function hideResults() {
    resultsContainer.style.display = 'none';
    resultsContainer.classList.remove('show');
    resultsCard.classList.remove('show');
}

function showEmptyState() {
    emptyState.style.display = 'flex';
    resultsContainer.style.display = 'none';
    errorState.style.display = 'none';
}

function hideError() {
    errorState.style.display = 'none';
}

function showError(message) {
    errorMessage.textContent = message;
    errorState.style.display = 'flex';
    emptyState.style.display = 'none';
    resultsContainer.style.display = 'none';
}

function animateValue(element, value, suffix = '', maxVal = 100) {
    if (!element) return;
    const target = parseFloat(value) || 0;
    element.textContent = (target >= 0 ? '+' : '') + target.toFixed(2) + suffix;
}

// ==================== SAVE CAMPAIGN ====================

async function saveCampaign() {
    if (!currentResult) {
        alert('No analysis results to save. Please run an analysis first.');
        return;
    }

    try {
        const response = await fetch('/save-campaign', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentResult)
        });

        const result = await response.json();
        
        if (result.success) {
            alert('Campaign saved successfully!');
            updateDashboard();
        } else {
            alert('Failed to save campaign: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error("Save campaign error:", error);
        alert('Failed to save campaign: ' + error.message);
    }
}

// ==================== GENERATE DETAILED REPORT ====================

async function generateDetailedReport() {
    if (!currentResult) {
        alert('No analysis results to generate report. Please run an analysis first.');
        return;
    }

    try {
        const response = await fetch('/generate-detailed-report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentResult)
        });

        const result = await response.json();
        
        if (result.success) {
            // Open report in new window
            const reportWindow = window.open('', '_blank');
            reportWindow.document.write(result.report);
            reportWindow.document.close();
        } else {
            alert('Failed to generate report: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error("Generate report error:", error);
        alert('Failed to generate report: ' + error.message);
    }
}

// ==================== EXPORT FUNCTIONS ====================

async function exportSelectedCampaigns() {
    if (selectedCampaigns.size === 0) {
        alert('Please select campaigns to export.');
        return;
    }

    try {
        const ids = Array.from(selectedCampaigns);
        const response = await fetch('/export/selected-csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ campaign_ids: ids })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'indra_selected_campaigns.csv';
            a.click();
            URL.revokeObjectURL(url);
        } else {
            alert('Failed to export campaigns');
        }
    } catch (error) {
        console.error("Export error:", error);
        alert('Failed to export: ' + error.message);
    }
}

async function exportAllCampaigns() {
    try {
        const response = await fetch('/export/csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'indra_all_campaigns.csv';
            a.click();
            URL.revokeObjectURL(url);
        } else {
            alert('Failed to export campaigns');
        }
    } catch (error) {
        console.error("Export error:", error);
        alert('Failed to export: ' + error.message);
    }
}

// ==================== FILE UPLOAD ====================

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    fileNameSpan.textContent = file.name;
    
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/import/campaigns', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully imported ${result.imported} campaigns!`);
            fileNameSpan.textContent = 'No file selected';
            csvFileInput.value = '';
            updateDashboard();
            loadHistory();
        } else {
            alert('Import failed: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error("Upload error:", error);
        alert('Failed to upload file: ' + error.message);
    }
}

async function downloadTemplate() {
    try {
        const response = await fetch('/import/template');
        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'indra_template.csv';
            a.click();
            URL.revokeObjectURL(url);
        } else {
            alert('Failed to download template');
        }
    } catch (error) {
        console.error("Template download error:", error);
    }
}

// ==================== THEME & SETTINGS ====================

function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    document.body.classList.toggle('light-theme');
    
    const icon = themeToggle.querySelector('i');
    if (document.body.classList.contains('dark-theme')) {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    } else {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }
}

function saveSettings() {
    appSettings.currency = currencyInput.value;
    appSettings.revenueColor = revenueColorInput.value;
    appSettings.costColor = costColorInput.value;
    
    settingsModal.style.display = 'none';
    alert('Settings saved!');
}

function startTour() {
    // Simple alert for now - could be enhanced with Shepherd.js
    alert('Welcome to INDRA Analytics! This tool helps you analyze campaign performance and ROI.');
}

// ==================== EVENT LISTENERS ====================

// A/B Test Analysis button
if (analyzeAbTestBtn) {
    analyzeAbTestBtn.addEventListener('click', analyzeAbTest);
}

// Channel Comparison button
if (compareChannelsBtn) {
    compareChannelsBtn.addEventListener('click', compareChannels);
}

// Form submission - prevent default to avoid double submission
if (form) {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        analyze(e);
    });
}

// Analyze button click handler
if (analyzeBtn) {
    analyzeBtn.addEventListener('click', function(e) {
        e.preventDefault();
        analyze(e);
    });
}

// Reset button
if (resetBtn) {
    resetBtn.addEventListener('click', () => {
        hideResults();
        showEmptyState();
        currentResult = null;
    });
}

// Save Campaign button
if (saveCampaignBtn) {
    saveCampaignBtn.addEventListener('click', saveCampaign);
}

// Generate Detailed Report button
if (generateDetailedReportBtn) {
    generateDetailedReportBtn.addEventListener('click', generateDetailedReport);
}

// Navigation buttons
if (dashboardBtn) {
    dashboardBtn.addEventListener('click', () => {
        dashboardSection.style.display = 'block';
        historySection.style.display = 'none';
        comparisonSection.style.display = 'none';
        mainContent.style.display = 'block';
        updateDashboard();
    });
}

if (historyBtn) {
    historyBtn.addEventListener('click', () => {
        historySection.style.display = 'block';
        dashboardSection.style.display = 'none';
        comparisonSection.style.display = 'none';
        mainContent.style.display = 'none';
        loadHistory();
    });
}

if (closeDashboard) {
    closeDashboard.addEventListener('click', () => {
        dashboardSection.style.display = 'none';
        mainContent.style.display = 'block';
    });
}

if (closeHistory) {
    closeHistory.addEventListener('click', () => {
        historySection.style.display = 'none';
        mainContent.style.display = 'block';
    });
}

if (closeComparison) {
    closeComparison.addEventListener('click', () => {
        comparisonSection.style.display = 'none';
        historySection.style.display = 'block';
    });
}

// Export buttons
if (exportSelectedCsv) {
    exportSelectedCsv.addEventListener('click', exportSelectedCampaigns);
}

if (exportAllCsv) {
    exportAllCsv.addEventListener('click', exportAllCampaigns);
}

if (compareSelected) {
    compareSelected.addEventListener('click', compareCampaigns);
}

// Theme toggle
if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
}

// Help button
if (helpBtn) {
    helpBtn.addEventListener('click', startTour);
}

// Settings button
if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
        settingsModal.style.display = 'flex';
    });
}

if (closeSettings) {
    closeSettings.addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });
}

if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener('click', saveSettings);
}

// File upload
if (csvFileInput) {
    csvFileInput.addEventListener('change', handleFileUpload);
}

if (downloadTemplateBtn) {
    downloadTemplateBtn.addEventListener('click', downloadTemplate);
}

// Collapsible sections
document.querySelectorAll('.collapsible-header').forEach(header => {
    header.addEventListener('click', () => {
        const content = header.nextElementSibling;
        const icon = header.querySelector('.fa-chevron-down');
        if (content.style.display === 'none') {
            content.style.display = 'block';
            if (icon) icon.classList.add('rotate');
        } else {
            content.style.display = 'none';
            if (icon) icon.classList.remove('rotate');
        }
    });
});

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    console.log('INDRA Analytics initialized');
    
    // Check URL params or show default state
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('dashboard') === 'true') {
        dashboardSection.style.display = 'block';
        mainContent.style.display = 'none';
        updateDashboard();
    } else {
        showEmptyState();
    }
});

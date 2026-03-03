/**
 * INDRA - Intelligent Network Data ROI Analytics
 * Ultra Premium Edition
 * Enhanced JavaScript for instant results display
 */

let currentResult = null;
let financialChart = null;

// DOM Elements
const analyzeBtn = document.getElementById('analyzeBtn');
const resetBtn = document.getElementById('resetBtn');
const saveBtn = document.getElementById('saveBtn');
const reportBtn = document.getElementById('reportBtn');
const form = document.getElementById('analyzeForm');

// Result Elements
const emptyState = document.getElementById('emptyState');
const resultsContainer = document.getElementById('resultsContainer');

// Input Elements
const inputs = {
    campaignName: document.getElementById('campaignName'),
    channel: document.getElementById('channel'),
    impressions: document.getElementById('impressions'),
    clicks: document.getElementById('clicks'),
    conversions: document.getElementById('conversions'),
    revenue: document.getElementById('revenue'),
    cost: document.getElementById('cost')
};

// Output Elements
const resultCampaignName = document.getElementById('resultCampaignName');
const ctrValue = document.getElementById('ctrValue');
const conversionValue = document.getElementById('conversionValue');
const roiValue = document.getElementById('roiValue');
const ctrBar = document.getElementById('ctrBar');
const conversionBar = document.getElementById('conversionBar');
const roiBar = document.getElementById('roiBar');
const revenueValue = document.getElementById('revenueValue');
const costValue = document.getElementById('costValue');
const netProfitValue = document.getElementById('netProfitValue');
const roasValue = document.getElementById('roasValue');
const cpcValue = document.getElementById('cpcValue');
const cpaValue = document.getElementById('cpaValue');
const rpmValue = document.getElementById('rpmValue');
const profitMarginValue = document.getElementById('profitMarginValue');
const impressionsValueEl = document.getElementById('impressionsValue');
const clicksValueEl = document.getElementById('clicksValue');
const conversionsValueEl = document.getElementById('conversionsValue');

// Format currency
function formatCurrency(val) {
    return '$' + parseFloat(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// Validate inputs
function validateInputs() {
    const impressions = parseFloat(inputs.impressions.value) || 0;
    const clicks = parseFloat(inputs.clicks.value) || 0;
    const conversions = parseFloat(inputs.conversions.value) || 0;
    const revenue = parseFloat(inputs.revenue.value) || 0;
    const cost = parseFloat(inputs.cost.value) || 0;

    if (impressions < 0 || clicks < 0 || conversions < 0 || revenue < 0 || cost < 0) {
        alert('All values must be positive numbers');
        return false;
    }

    if (clicks > impressions && impressions > 0) {
        alert('Clicks cannot exceed impressions');
        return false;
    }

    if (conversions > clicks && clicks > 0) {
        alert('Conversions cannot exceed clicks');
        return false;
    }

    return true;
}

// Main analyze function
async function analyze(event) {
    if (event) event.preventDefault();

    if (!validateInputs()) return;

    // Get input values
    const data = {
        name: inputs.campaignName.value || 'Campaign_' + Date.now(),
        channel: inputs.channel.value || 'Direct',
        impressions: parseFloat(inputs.impressions.value) || 0,
        clicks: parseFloat(inputs.clicks.value) || 0,
        conversions: parseFloat(inputs.conversions.value) || 0,
        revenue: parseFloat(inputs.revenue.value) || 0,
        cost: parseFloat(inputs.cost.value) || 0
    };

    // Calculate metrics locally for instant display
    const ctr = data.impressions > 0 ? (data.clicks / data.impressions * 100) : 0;
    const conversionRate = data.clicks > 0 ? (data.conversions / data.clicks * 100) : 0;
    const roi = data.cost > 0 ? ((data.revenue - data.cost) / data.cost * 100) : 0;
    const netProfit = data.revenue - data.cost;
    const roas = data.cost > 0 ? (data.revenue / data.cost) : 0;
    const cpc = data.clicks > 0 ? (data.cost / data.clicks) : 0;
    const cpa = data.conversions > 0 ? (data.cost / data.conversions) : 0;
    const rpm = data.impressions > 0 ? ((data.revenue / data.impressions) * 1000) : 0;
    const profitMargin = data.revenue > 0 ? ((netProfit / data.revenue) * 100) : 0;

    // Store result
    currentResult = {
        ...data,
        ctr: ctr.toFixed(2),
        conversion_rate: conversionRate.toFixed(2),
        roi: roi.toFixed(2)
    };

    // Display results immediately
    displayResults(data, { ctr, conversionRate, roi, netProfit, roas, cpc, cpa, rpm, profitMargin });

    // Smooth scroll to results
    setTimeout(() => {
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);

    // Send to server in background
    try {
        await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    } catch (e) {
        console.log('Background sync:', e);
    }
}

// Display results with animation
function displayResults(data, metrics) {
    // Hide empty state, show results
    emptyState.style.display = 'none';
    resultsContainer.classList.add('show');
    resultsContainer.style.display = 'block';

    // Update campaign name
    resultCampaignName.textContent = data.name;

    // Update key metrics with animation
    animateValue(ctrValue, metrics.ctr, '%');
    animateValue(conversionValue, metrics.conversionRate, '%');
    animateValue(roiValue, metrics.roi, '%');

    // Update progress bars
    ctrBar.style.width = Math.min(metrics.ctr * 10, 100) + '%';
    conversionBar.style.width = Math.min(metrics.conversionRate * 5, 100) + '%';
    roiBar.style.width = Math.min(Math.abs(metrics.roi), 100) + '%';
    roiBar.style.background = metrics.roi >= 0 ? 
        'linear-gradient(90deg, #10b981, #34d399)' : 
        'linear-gradient(90deg, #ef4444, #f87171)';

    // Update financial stats
    revenueValue.textContent = formatCurrency(data.revenue);
    costValue.textContent = formatCurrency(data.cost);
    netProfitValue.textContent = formatCurrency(metrics.netProfit);
    netProfitValue.className = 'stat-value ' + (metrics.netProfit >= 0 ? 'positive' : 'negative');
    roasValue.textContent = metrics.roas.toFixed(2) + 'x';

    // Update efficiency metrics
    cpcValue.textContent = formatCurrency(metrics.cpc);
    cpaValue.textContent = formatCurrency(metrics.cpa);
    rpmValue.textContent = formatCurrency(metrics.rpm);
    profitMarginValue.textContent = metrics.profitMargin.toFixed(1) + '%';
    profitMarginValue.className = 'stat-value ' + (metrics.profitMargin >= 0 ? 'positive' : 'negative');

    // Update funnel
    impressionsValueEl.textContent = data.impressions.toLocaleString();
    clicksValueEl.textContent = data.clicks.toLocaleString();
    conversionsValueEl.textContent = data.conversions.toLocaleString();

    // Render chart
    renderChart(data.revenue, data.cost);
}

// Animate value display
function animateValue(element, value, suffix) {
    if (!element) return;
    const target = parseFloat(value) || 0;
    const prefix = target >= 0 ? '+' : '';
    element.textContent = prefix + target.toFixed(2) + suffix;
}

// Render financial chart
function renderChart(revenue, cost) {
    const ctx = document.getElementById('financialChart').getContext('2d');
    
    if (financialChart) {
        financialChart.destroy();
    }

    financialChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Revenue', 'Cost'],
            datasets: [{
                label: 'Amount ($)',
                data: [revenue, cost],
                backgroundColor: [
                    'rgba(0, 212, 255, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderColor: [
                    '#00d4ff',
                    '#ef4444'
                ],
                borderWidth: 2,
                borderRadius: 8,
                barThickness: 60
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a1a1aa'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#a1a1aa',
                        font: {
                            weight: '600'
                        }
                    }
                }
            }
        }
    });
}

// Save campaign
async function saveCampaign() {
    if (!currentResult) return;

    try {
        const response = await fetch('/save-campaign', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentResult)
        });
        const result = await response.json();
        
        if (result.success) {
            alert('Campaign saved successfully!');
        } else {
            alert('Error: ' + result.error);
        }
    } catch (e) {
        alert('Failed to save campaign');
    }
}

// Generate report
async function generateReport() {
    if (!currentResult) return;

    try {
        const response = await fetch('/generate-detailed-report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentResult)
        });
        const result = await response.json();
        
        if (result.success) {
            const reportWindow = window.open('', '_blank');
            reportWindow.document.write(result.report);
            reportWindow.document.close();
        }
    } catch (e) {
        alert('Failed to generate report');
    }
}

// Reset form
function resetForm() {
    form.reset();
    resultsContainer.style.display = 'none';
    resultsContainer.classList.remove('show');
    emptyState.style.display = 'block';
    currentResult = null;
}

// Event Listeners
if (analyzeBtn) {
    analyzeBtn.addEventListener('click', analyze);
}

if (resetBtn) {
    resetBtn.addEventListener('click', resetForm);
}

if (saveBtn) {
    saveBtn.addEventListener('click', saveCampaign);
}

if (reportBtn) {
    reportBtn.addEventListener('click', generateReport);
}

// Form submit
if (form) {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        analyze(e);
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('INDRA Analytics Ultra Premium initialized');
});


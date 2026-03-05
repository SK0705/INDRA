const API_BASE = 'http://localhost:8000';

// ============================================
// RETRY UTILITY
// ============================================

/**
 * Fetch with automatic retry on network failure.
 * @param {string} url - The URL to fetch
 * @param {object} options - fetch() options
 * @param {number} retries - Number of retry attempts (default 2)
 * @param {number} delayMs - Delay between retries in ms (default 1000)
 */
async function fetchWithRetry(url, options = {}, retries = 2, delayMs = 1000) {
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            const response = await fetch(url, options);
            return response;
        } catch (err) {
            if (attempt < retries) {
                console.warn(`[INDRA] Fetch failed (attempt ${attempt + 1}/${retries + 1}), retrying in ${delayMs}ms...`, err);
                await new Promise(resolve => setTimeout(resolve, delayMs));
            } else {
                throw err;
            }
        }
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

const formatNumber = (num) => new Intl.NumberFormat('en-US').format(num || 0);
const formatCurrency = (num) => '₹' + (num || 0).toLocaleString('en-US', { minimumFractionDigits: 2 });
const formatPercent = (num) => ((num || 0) * 100).toFixed(2) + '%';
const formatRoi = (num) => (num || 0).toFixed(2) + 'x';

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<i class="fa-solid fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i> ${message}`;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// DASHBOARD FUNCTIONALITY
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    const dashboardSection = document.getElementById('dashboardSection');
    const inputCard = document.getElementById('inputCard');
    const historySection = document.getElementById('historySection');
    const abTestSection = document.getElementById('abTestSection');

    const dashboardBtn = document.getElementById('dashboardBtn');
    const historyBtn = document.getElementById('historyBtn');
    const liveModeBtn = document.getElementById('liveModeBtn');
    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    const closeDashboard = document.getElementById('closeDashboard');

    let isLiveMode = false;
    let autoRefreshInterval = null;
    let historyInterval = null;
    let current_data = [];
    let campaignChartInstance = null;

    // Global assignments moved to top for reliability
    window.deleteHistory = async (campaignId) => {
        if (!confirm('Are you sure you want to delete this campaign record?')) return;

        try {
            const response = await fetch(`${API_BASE}/delete_history/${campaignId}`, {
                method: 'GET'
            });

            if (response.ok) {
                showToast('Record deleted successfully', 'success');
                fetchHistoryData();
                fetchDashboardData();
            } else {
                showToast('Failed to delete record', 'error');
            }
        } catch (err) {
            console.error(err);
            showToast('Error deleting record', 'error');
        }
    };

    window.showCampaignReport = (campaignId) => {
        const campaign = current_data.find(c => c.campaign_id === campaignId);
        if (!campaign) return;

        const modal = document.getElementById('reportModal');

        // Populate Header
        document.getElementById('reportCampaignName').innerText = campaign.campaign_name;
        document.getElementById('reportCampaignId').innerText = `ID: ${campaign.campaign_id}`;

        // Calculate Metrics
        const roi = campaign.cost > 0 ? (campaign.revenue - campaign.cost) / campaign.cost : 0;
        const convRate = campaign.clicks > 0 ? (campaign.conversions / campaign.clicks) : 0;
        const cac = campaign.conversions > 0 ? (campaign.cost / campaign.conversions) : campaign.cost;
        const profit = campaign.revenue - campaign.cost;

        // Update Stats
        document.getElementById('reportRoi').innerText = roi.toFixed(2) + 'x';
        document.getElementById('reportConvRate').innerText = (convRate * 100).toFixed(2) + '%';
        document.getElementById('reportCac').innerText = formatCurrency(cac);
        document.getElementById('reportProfit').innerText = formatCurrency(profit);

        // Progress Bars
        document.getElementById('roiBar').style.width = Math.min(roi * 20, 100) + '%';
        document.getElementById('convBar').style.width = Math.min(convRate * 500, 100) + '%';

        // Details
        document.getElementById('reportImpressions').innerText = formatNumber(campaign.impressions);
        document.getElementById('reportClicks').innerText = formatNumber(campaign.clicks);
        document.getElementById('reportConversions').innerText = formatNumber(campaign.conversions);
        document.getElementById('reportCost').innerText = formatCurrency(campaign.cost);
        document.getElementById('reportRevenue').innerText = formatCurrency(campaign.revenue);

        // Channel Logic
        const sameChannelData = current_data.filter(c => c.channel === campaign.channel);
        const avgRoi = sameChannelData.length > 0 ? sameChannelData.reduce((acc, c) => acc + (c.cost > 0 ? (c.revenue - c.cost) / c.cost : 0), 0) / sameChannelData.length : 0;

        const pill = document.getElementById('benchmarkIndicator');
        if (roi >= avgRoi) {
            pill.innerText = 'ABOVE CHANNEL AVERAGE';
            pill.className = 'benchmark-pill above';
            document.getElementById('channelIntelligence').innerText = `This campaign is outperforming the ${campaign.channel} channel average by ${((roi - avgRoi) * 100).toFixed(1)}%. Maintain current strategy.`;
        } else {
            pill.innerText = 'BELOW CHANNEL AVERAGE';
            pill.className = 'benchmark-pill below';
            document.getElementById('channelIntelligence').innerText = `This campaign is underperforming compared to ${campaign.channel} benchmarks. Optimization recommended for better ROI.`;
        }

        // --- ENHANCED VISUALS: Chart.js Radar ---
        const ctx = document.getElementById('campaignChart').getContext('2d');
        if (campaignChartInstance) {
            campaignChartInstance.destroy();
        }

        // Normalize metrics for radar (0-100 scale)
        const radarMetrics = [
            Math.min(roi * 25, 100), // ROI Index
            Math.min((campaign.clicks / Math.max(campaign.impressions, 1)) * 1000, 100), // CTR Vector
            Math.min((campaign.conversions / Math.max(campaign.clicks, 1)) * 500, 100), // Conv %
            Math.min((campaign.revenue / Math.max(campaign.cost, 1)) * 20, 100) // Profitability
        ];

        campaignChartInstance = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['ROI INDEX', 'CTR VECTOR', 'CONV RATE', 'EFFICIENCY'],
                datasets: [{
                    label: 'Performance Vector',
                    data: radarMetrics,
                    backgroundColor: 'rgba(0, 229, 255, 0.2)',
                    borderColor: '#00e5ff',
                    pointBackgroundColor: '#00e5ff',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#00e5ff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        pointLabels: {
                            color: '#8892b0',
                            font: { family: 'Orbitron', size: 10 }
                        },
                        ticks: { display: false },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                },
                plugins: { legend: { display: false } }
            }
        });

        // --- ENHANCED ANALYSIS: STARK Intel ---
        const analysisContainer = document.getElementById('deepAnalysisContent');
        let analysisHTML = '';

        // ROI Intelligence
        if (roi > 2.5) {
            analysisHTML += `<div class="analysis-point"><i class="fa-solid fa-shield-halved"></i> <span><strong>S-CLASS ASSET:</strong> ROI exceeds 250%. Priority vector for budget expansion.</span></div>`;
        } else if (roi > 1) {
            analysisHTML += `<div class="analysis-point"><i class="fa-solid fa-check-double"></i> <span><strong>OPTIMAL YIELD:</strong> Healthy margin detected. Performance is within high-efficiency bounds.</span></div>`;
        } else if (roi < 0) {
            analysisHTML += `<div class="analysis-point"><i class="fa-solid fa-radiation"></i> <span><strong>CRITICAL FAILURE:</strong> Negative ROI detected. Immediate halt or restructuring required.</span></div>`;
        }

        // Funnel Intelligence
        const ctrRatio = campaign.clicks / Math.max(campaign.impressions, 1);
        if (ctrRatio > 0.1) {
            analysisHTML += `<div class="analysis-point"><i class="fa-solid fa-eye"></i> <span><strong>HIGH RESONANCE:</strong> CTR is exceptional. Creative assets are highly effective.</span></div>`;
        } else if (ctrRatio < 0.02) {
            analysisHTML += `<div class="analysis-point"><i class="fa-solid fa-low-vision"></i> <span><strong>LOW ENGAGEMENT:</strong> Ad creative failing to capture attention. Vector optimization needed.</span></div>`;
        }

        if (convRate > 0.08) {
            analysisHTML += `<div class="analysis-point"><i class="fa-solid fa-bolt"></i> <span><strong>PRECISION TARGETING:</strong> Conversion rate is peak-tier. Post-click experience is optimized.</span></div>`;
        } else if (convRate < 0.015) {
            analysisHTML += `<div class="analysis-point"><i class="fa-solid fa-filter"></i> <span><strong>FUNNEL FRICTION:</strong> High drop-off post-click. Friction detected on landing vector.</span></div>`;
        }

        // Channel Context
        if (roi > avgRoi * 1.5) {
            analysisHTML += `<div class="analysis-point"><i class="fa-solid fa-crown"></i> <span><strong>CHANNEL LEADER:</strong> Outperforming ${campaign.channel} benchmarks significantly.</span></div>`;
        }

        analysisContainer.innerHTML = analysisHTML || '<p class="text-muted">Analyzing performance vectors... No critical anomalies detected. Maintain current parameters.</p>';

        // --- ENHANCED VISUALS: Matplotlib Comparison ---
        const matplotlibContainer = document.getElementById('campaignMatplotlibChart');
        const matplotlibLoader = document.getElementById('matplotlibChartLoading');

        // Reset state
        matplotlibContainer.style.display = 'none';
        matplotlibLoader.style.display = 'block';

        // Reset scroll position
        document.querySelector('.modal-body').scrollTop = 0;

        fetch(`${API_BASE}/campaign_charts/${campaignId}`)
            .then(res => res.json())
            .then(data => {
                if (data.comparison_chart) {
                    matplotlibContainer.src = data.comparison_chart;
                    matplotlibContainer.style.display = 'block';
                    matplotlibLoader.style.display = 'none';
                }
            })
            .catch(err => {
                console.error("Matplotlib fetch failed:", err);
                matplotlibLoader.innerHTML = '<span class="text-danger">Failed to load comparison vectors.</span>';
            });

        modal.style.display = 'block';
    };

    // --- A/B TEST FORM HANDLER ---
    const abTestForm = document.getElementById('abTestForm');
    if (abTestForm) {
        abTestForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const variantA = {
                impressions: parseFloat(document.getElementById('abImpressionsA').value) || 0,
                clicks: parseFloat(document.getElementById('abClicksA').value) || 0,
                conversions: parseFloat(document.getElementById('abConversionsA').value) || 0,
                cost: parseFloat(document.getElementById('abCostA').value) || 0,
                revenue: parseFloat(document.getElementById('abRevenueA').value) || 0
            };

            const variantB = {
                impressions: parseFloat(document.getElementById('abImpressionsB').value) || 0,
                clicks: parseFloat(document.getElementById('abClicksB').value) || 0,
                conversions: parseFloat(document.getElementById('abConversionsB').value) || 0,
                cost: parseFloat(document.getElementById('abCostB').value) || 0,
                revenue: parseFloat(document.getElementById('abRevenueB').value) || 0
            };

            const submitBtn = abTestForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running Analysis...';

            try {
                const response = await fetch(`${API_BASE}/ab_test`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ variant_a: variantA, variant_b: variantB })
                });

                if (!response.ok) throw new Error('Server error');
                const result = await response.json();

                if (result.status !== 'success') {
                    showToast(result.message || 'Test failed.', 'error');
                    return;
                }

                const winner = result.better_variant;
                const winnerClass = winner === 'A' ? 'variant-a-win' : (winner === 'B' ? 'variant-b-win' : 'variant-tie');
                const sigBadge = result.significant
                    ? `<span class="sig-badge significant">✔ Statistically Significant</span>`
                    : `<span class="sig-badge not-significant">⚠ Not Statistically Significant</span>`;

                const ra = result.variant_a;
                const rb = result.variant_b;

                const resultsHTML = `
                    <div class="ab-result-card ${winnerClass}">
                        <div class="ab-verdict-header">
                            <div class="ab-winner-badge">
                                <i class="fa-solid fa-trophy"></i>
                                ${winner === 'Tie' ? 'TEST IS A TIE' : `VARIANT ${winner} WINS`}
                            </div>
                            ${sigBadge}
                        </div>
                        <p class="ab-verdict-text">${result.verdict}</p>
                        <p class="ab-pvalue">χ² P-Value: ${result.p_value.toFixed(4)} | Chi²: ${result.chi2.toFixed(2)}</p>
                        
                        <div class="ab-metrics-comparison">
                            <table class="ab-compare-table">
                                <thead>
                                    <tr>
                                        <th>Metric</th>
                                        <th class="${winner === 'A' ? 'winning-col' : ''}">Variant A</th>
                                        <th class="${winner === 'B' ? 'winning-col' : ''}">Variant B</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Conversion Rate</td>
                                        <td class="${ra.conversion_rate > rb.conversion_rate ? 'metric-better' : ''}">${ra.conversion_rate}%</td>
                                        <td class="${rb.conversion_rate > ra.conversion_rate ? 'metric-better' : ''}">${rb.conversion_rate}%</td>
                                    </tr>
                                    <tr>
                                        <td>Click-Through Rate</td>
                                        <td class="${ra.ctr > rb.ctr ? 'metric-better' : ''}">${ra.ctr}%</td>
                                        <td class="${rb.ctr > ra.ctr ? 'metric-better' : ''}">${rb.ctr}%</td>
                                    </tr>
                                    <tr>
                                        <td>ROI</td>
                                        <td class="${ra.roi > rb.roi ? 'metric-better' : ''}">${ra.roi}%</td>
                                        <td class="${rb.roi > ra.roi ? 'metric-better' : ''}">${rb.roi}%</td>
                                    </tr>
                                    <tr>
                                        <td>Cost per Acquisition</td>
                                        <td class="${ra.cac < rb.cac ? 'metric-better' : ''}">₹${ra.cac}</td>
                                        <td class="${rb.cac < ra.cac ? 'metric-better' : ''}">₹${rb.cac}</td>
                                    </tr>
                                    <tr>
                                        <td>Composite Score</td>
                                        <td class="${ra.score > rb.score ? 'metric-better' : ''}">${ra.score}</td>
                                        <td class="${rb.score > ra.score ? 'metric-better' : ''}">${rb.score}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>`;

                const container = document.getElementById('abResultsContainer');
                document.getElementById('abResultsContent').innerHTML = resultsHTML;
                container.style.display = 'block';
                container.scrollIntoView({ behavior: 'smooth', block: 'start' });
                showToast('A/B Test analysis complete!', 'success');

            } catch (err) {
                console.error('A/B Test error:', err);
                showToast('A/B Test failed. Please check your inputs.', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fa-solid fa-vial"></i> Run A/B Test';
            }
        });
    }

    // Button Navigation
    dashboardBtn.addEventListener('click', () => {
        showSection('dashboard');
    });

    historyBtn.addEventListener('click', () => {
        showSection('history');
    });

    // Live Mode Toggle
    liveModeBtn.addEventListener('click', () => {
        isLiveMode = !isLiveMode;
        const indicator = document.getElementById('liveIndicator');
        if (isLiveMode) {
            indicator.classList.add('active');
            liveModeBtn.classList.add('live-active');
            startLiveUpdates();
        } else {
            indicator.classList.remove('active');
            liveModeBtn.classList.remove('live-active');
            stopLiveUpdates();
        }
    });

    // Auto-refresh Toggle
    autoRefreshToggle.addEventListener('change', (e) => {
        if (e.target.checked) {
            startLiveUpdates();
        } else {
            stopLiveUpdates();
        }
    });

    // Close Dashboard
    if (closeDashboard) {
        closeDashboard.addEventListener('click', () => {
            showSection('input');
        });
    }

    // Show section helper
    function showSection(section) {
        if (section === 'dashboard') {
            dashboardSection.style.display = 'block';
            historySection.style.display = 'none';
            abTestSection.style.display = 'none';
            inputCard.style.display = 'none';
            fetchDashboardData();
        } else if (section === 'history') {
            dashboardSection.style.display = 'none';
            historySection.style.display = 'block';
            abTestSection.style.display = 'none';
            inputCard.style.display = 'none';
            fetchHistoryData();
        } else if (section === 'abtest') {
            dashboardSection.style.display = 'none';
            historySection.style.display = 'none';
            abTestSection.style.display = 'block';
            inputCard.style.display = 'none';
        } else {
            dashboardSection.style.display = 'none';
            historySection.style.display = 'none';
            abTestSection.style.display = 'none';
            inputCard.style.display = 'block';
        }
    }

    // Expose showSection globally for navigation buttons
    window.showSection = showSection;

    // Live Updates
    function startLiveUpdates() {
        if (autoRefreshInterval) clearInterval(autoRefreshInterval);
        autoRefreshInterval = setInterval(() => {
            if (dashboardSection.style.display === 'block') {
                fetchDashboardData();
            }
            if (historySection.style.display === 'block') {
                fetchHistoryData();
            }
        }, 2000);
    }

    function stopLiveUpdates() {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
    }

    // ============================================
    // CAMPAIGN FORM HANDLER
    // ============================================

    document.getElementById('analyzeForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const campaignName = document.getElementById('campaignName').value;
        const channel = document.getElementById('channel').value;

        const payload = {
            campaign_id: 'CMP-' + campaignName.substring(0, 6).toUpperCase() + '-' + Date.now().toString().slice(-4),
            campaign_name: campaignName,
            channel: channel,
            impressions: parseInt(document.getElementById('impressions').value),
            clicks: parseInt(document.getElementById('clicks').value),
            conversions: parseInt(document.getElementById('conversions').value),
            cost: parseFloat(document.getElementById('cost').value),
            revenue: parseFloat(document.getElementById('revenue').value),
            variant: 'None'
        };

        try {
            const response = await fetchWithRetry(`${API_BASE}/upload_campaign_data`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                showToast('Analysis Complete! Campaign data transmitted to INDRA.', 'success');
                document.getElementById('analyzeForm').reset();
                showSection('dashboard');
            } else {
                const err = await response.json().catch(() => ({}));
                showToast(err.message || 'Server returned an error. Please try again.', 'error');
            }
        } catch (err) {
            console.error('[INDRA] Campaign submit failed:', err);
            showToast('Transmission failed. Ensure server is running on port 8000.', 'error');
        }
    });

    // ============================================
    // CSV UPLOAD HANDLER
    // ============================================

    const csvFileInput = document.getElementById('csvFileInput');
    const browseBtn = document.getElementById('browseBtn');
    const uploadCsvBtn = document.getElementById('uploadCsvBtn');
    const dropZone = document.getElementById('dropZone');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const removeFileBtn = document.getElementById('removeFileBtn');

    let selectedFile = null;

    browseBtn.addEventListener('click', () => csvFileInput.click());

    csvFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    removeFileBtn.addEventListener('click', () => {
        selectedFile = null;
        csvFileInput.value = '';
        fileInfo.style.display = 'none';
        dropZone.style.display = 'flex';
        uploadCsvBtn.disabled = true;
    });

    function handleFileSelect(file) {
        if (!file.name.endsWith('.csv')) {
            showToast('Invalid file format. Please upload a CSV.', 'error');
            return;
        }

        selectedFile = file;
        fileName.innerText = file.name;
        fileInfo.style.display = 'flex';
        dropZone.style.display = 'none';
        uploadCsvBtn.disabled = false;
    }

    uploadCsvBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        const formData = new FormData();
        formData.append('file', selectedFile);

        uploadCsvBtn.disabled = true;
        uploadCsvBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';

        try {
            const response = await fetchWithRetry(`${API_BASE}/upload_csv`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                showToast(result.message || 'CSV Processed Successfully!', 'success');
                // Reset UI
                selectedFile = null;
                csvFileInput.value = '';
                fileInfo.style.display = 'none';
                dropZone.style.display = 'flex';

                // Switch to dashboard and refresh
                showSection('dashboard');
            } else {
                showToast(result.message || 'Upload failed. Check file format and try again.', 'error');
            }
        } catch (err) {
            console.error('[INDRA] CSV upload network error:', err);
            showToast('Network error during upload. Ensure the server is running on port 8000.', 'error');
        } finally {
            uploadCsvBtn.disabled = selectedFile === null;
            uploadCsvBtn.innerHTML = '<i class="fa-solid fa-upload"></i> Process Batch';
        }
    });

    // ============================================
    // DASHBOARD DATA FETCH
    // ============================================

    async function fetchDashboardData() {
        try {
            const [metricsRes, chartsRes, recsRes] = await Promise.all([
                fetch(`${API_BASE}/analytics_metrics`),
                fetch(`${API_BASE}/charts`),
                fetch(`${API_BASE}/ai_recommendations`)
            ]);

            const metrics = await metricsRes.json();
            const charts = await chartsRes.json();
            const recs = await recsRes.json();

            updateDashboardMetrics(metrics);
            updateDashboardCharts(charts);
            updateRecommendations(recs);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        }
    }

    function updateDashboardMetrics(metrics) {
        if (!metrics.aggregate) return;

        const agg = metrics.aggregate;

        // Stats Grid
        document.getElementById('totalCampaigns').innerText = agg.campaigns || 0;
        document.getElementById('totalRevenue').innerText = formatCurrency(agg.revenue);
        document.getElementById('totalCost').innerText = formatCurrency(agg.cost);
        document.getElementById('avgCtr').innerText = formatPercent(agg.ctr);

        // Live Ticker
        document.getElementById('liveImpressions').innerText = formatNumber(agg.impressions);
        document.getElementById('liveClicks').innerText = formatNumber(agg.clicks);
        document.getElementById('liveConversions').innerText = formatNumber(agg.conversions);
        document.getElementById('liveProfit').innerText = formatCurrency(agg.profit);
        document.getElementById('liveRoi').innerText = formatRoi(agg.roi);
    }

    function updateDashboardCharts(charts) {
        if (charts.roi_chart) {
            const roiImg = document.getElementById('roiChartImage');
            roiImg.src = charts.roi_chart;
            roiImg.style.display = 'block';
            document.getElementById('roiNoData').style.display = 'none';
        }

        if (charts.cac_chart) {
            const cacImg = document.getElementById('cacChartImage');
            cacImg.src = charts.cac_chart;
            cacImg.style.display = 'block';
            document.getElementById('cacNoData').style.display = 'none';
        }
    }

    function updateRecommendations(recs) {
        const container = document.getElementById('recommendationsContainer');
        if (recs.recommendations && recs.recommendations.length > 0) {
            container.innerHTML = recs.recommendations.map((r, i) => `
                <div class="recommendation-item">
                    <span class="rec-number">${i + 1}</span>
                    <span class="rec-text">${r}</span>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="text-muted">Analyze campaigns to generate recommendations.</p>';
        }
    }

    // ============================================
    // HISTORY SECTION
    // ============================================

    async function fetchHistoryData() {
        try {
            const response = await fetch(`${API_BASE}/history`);
            const data = await response.json();
            current_data = data;
            updateHistoryTable(data);
        } catch (error) {
            console.error('Error fetching history:', error);
        }
    }

    function updateHistoryTable(data) {
        const tbody = document.getElementById('historyTableBody');
        const noDataMsg = document.getElementById('historyNoData');

        if (!data || data.length === 0) {
            tbody.innerHTML = '';
            noDataMsg.style.display = 'block';
            return;
        }

        noDataMsg.style.display = 'none';

        // Sort by most recent (reverse order)
        const sortedData = [...data].reverse();

        tbody.innerHTML = sortedData.map(item => {
            const roi = item.cost > 0 ? ((item.revenue - item.cost) / item.cost).toFixed(2) + 'x' : 'N/A';
            const ctr = item.impressions > 0 ? (item.clicks / item.impressions * 100).toFixed(2) + '%' : 'N/A';

            return `
                <tr>
                    <td>${item.campaign_name || item.campaign_id || 'N/A'}</td>
                    <td>${item.channel || 'N/A'}</td>
                    <td>${formatNumber(item.impressions)}</td>
                    <td>${formatNumber(item.clicks)}</td>
                    <td>${formatNumber(item.conversions)}</td>
                    <td>${formatCurrency(item.cost)}</td>
                    <td>${formatCurrency(item.revenue)}</td>
                    <td>${roi}</td>
                    <td>${ctr}</td>
                    <td><span class="badge badge-${item.variant && item.variant !== 'None' ? 'variant' : 'single'}">${item.variant || 'Single'}</span></td>
                    <td style="text-align: center; white-space: nowrap;">
                        <button class="btn-nav" style="padding: 6px 10px; font-size: 0.8rem; border-color: var(--success); color: var(--success);" title="View Detailed Report" onclick="showCampaignReport('${item.campaign_id}')">
                            <i class="fa-solid fa-file-invoice"></i>
                        </button>
                        <button class="btn-delete" title="Delete Record" onclick="deleteHistory('${item.campaign_id}')">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // ============================================
    // A/B TESTING SECTION
    // ============================================

    // Add A/B Test navigation - create button if not exists
    const headerActions = document.querySelector('.header-actions');
    if (headerActions && !document.getElementById('abTestBtn')) {
        const abTestBtn = document.createElement('button');
        abTestBtn.id = 'abTestBtn';
        abTestBtn.className = 'btn-nav';
        abTestBtn.innerHTML = '<i class="fa-solid fa-vial"></i> A/B Test';
        abTestBtn.addEventListener('click', () => showSection('abtest'));
        headerActions.appendChild(abTestBtn);
    }



    // Initial fetch
    fetchDashboardData();
    fetchHistoryData();

    // Close Modal Logic
    document.getElementById('closeReportModal').addEventListener('click', () => {
        document.getElementById('reportModal').style.display = 'none';
    });

    window.onclick = (event) => {
        const modal = document.getElementById('reportModal');
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };
});


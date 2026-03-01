from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import io
import os
from datetime import datetime
import csv
from scipy import stats
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# Use 'Agg' backend for Matplotlib to run in a headless environment (no GUI)
matplotlib.use('Agg')

app = Flask(__name__, static_folder='frontend', static_url_path='')

# Enable CORS for frontend-backend communication
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///indra_campaigns.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODEL ---
class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    impressions = db.Column(db.Integer, nullable=False)
    clicks = db.Column(db.Integer, nullable=False)
    conversions = db.Column(db.Integer, nullable=False)
    revenue = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    ctr = db.Column(db.Float, nullable=False)
    conversion_rate = db.Column(db.Float, nullable=False)
    roi = db.Column(db.Float, nullable=False)
    
    # Multi-Channel Support
    channel = db.Column(db.String(50), default='Direct')  # e.g., Facebook, Google Ads, Email, Instagram, LinkedIn
    
    # A/B Testing Support
    test_variant = db.Column(db.String(50), default='Control')  # Control, Variant A, Variant B, etc.
    test_group = db.Column(db.String(100), nullable=True)  # Test ID to group related variants
    test_duration_days = db.Column(db.Integer, default=7)
    sample_size = db.Column(db.Integer, nullable=True)  # Number of users in the test
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'impressions': self.impressions,
            'clicks': self.clicks,
            'conversions': self.conversions,
            'revenue': self.revenue,
            'cost': self.cost,
            'ctr': self.ctr,
            'conversion_rate': self.conversion_rate,
            'roi': self.roi,
            'channel': self.channel,
            'test_variant': self.test_variant,
            'test_group': self.test_group,
            'test_duration_days': self.test_duration_days,
            'sample_size': self.sample_size,
            'roas': round((self.revenue / self.cost) if self.cost > 0 else 0, 2),
            'cac': round((self.cost / self.conversions) if self.conversions > 0 else 0, 2),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

def add_sample_data():
    """Populates the database with initial sample campaigns."""
    sample_campaigns = [
        Campaign(
            name='Summer Sale 2026',
            impressions=50000,
            clicks=3500,
            conversions=280,
            revenue=28000,
            cost=8500,
            ctr=7.0,
            conversion_rate=8.0,
            roi=229.41,
            channel='Facebook',
            test_variant='Control',
            test_group='summer_2026',
            sample_size=50000
        ),
        Campaign(
            name='Winter Promotion',
            impressions=45000,
            clicks=4050,
            conversions=405,
            revenue=40500,
            cost=9000,
            ctr=9.0,
            conversion_rate=10.0,
            roi=350.0,
            channel='Google Ads',
            test_variant='Variant A',
            test_group='winter_2026',
            sample_size=45000
        ),
        Campaign(
            name='Email Campaign',
            impressions=30000,
            clicks=2700,
            conversions=351,
            revenue=35100,
            cost=6000,
            ctr=9.0,
            conversion_rate=13.0,
            roi=485.0,
            channel='Email',
            test_variant='Control',
            test_group='email_2026',
            sample_size=30000
        ),
        Campaign(
            name='Instagram Campaign',
            impressions=75000,
            clicks=4500,
            conversions=225,
            revenue=18000,
            cost=10500,
            ctr=6.0,
            conversion_rate=5.0,
            roi=71.43,
            channel='Instagram',
            test_variant='Variant B',
            test_group='social_2026',
            sample_size=75000
        ),
        Campaign(
            name='LinkedIn B2B Push',
            impressions=20000,
            clicks=2200,
            conversions=242,
            revenue=24200,
            cost=5500,
            ctr=11.0,
            conversion_rate=11.0,
            roi=340.0,
            channel='LinkedIn',
            test_variant='Control',
            test_group='b2b_2026',
            sample_size=20000
        ),
    ]
    for campaign in sample_campaigns:
        db.session.add(campaign)
    db.session.commit()

# Create database tables
with app.app_context():
    db.create_all()
    # Initialize with fresh sample data if database is empty
    if Campaign.query.count() == 0:
        add_sample_data()

# --- V.E.C.T.O.R. THEME FOR MATPLOTLIB ---
def set_stark_theme():
    """Sets a V.E.C.T.O.R.-inspired theme for Matplotlib charts."""
    plt.style.use('dark_background')
    plt.rcParams['axes.facecolor'] = '#0A192F'  # Deep Navy
    plt.rcParams['figure.facecolor'] = '#0A192F'
    plt.rcParams['text.color'] = '#E0E0E0'      # Primary Text
    plt.rcParams['axes.labelcolor'] = '#A0A0A0' # Secondary Text
    plt.rcParams['xtick.color'] = '#A0A0A0'
    plt.rcParams['ytick.color'] = '#A0A0A0'
    plt.rcParams['grid.color'] = '#00BFFF' # Holographic Blue grid
    plt.rcParams['grid.alpha'] = 0.1

set_stark_theme()
# --- END THEME ---

# --- HELPER FUNCTIONS ---
def generate_comparison_insights(campaigns):
    """Generates textual insights for a list of campaigns."""
    insights = []
    if len(campaigns) == 2:
        c1 = campaigns[0]
        c2 = campaigns[1]
        
        # ROI Analysis
        diff_roi = c1.roi - c2.roi
        if diff_roi > 0:
            insights.append(f"ROI Analysis: {c1.name} outperformed {c2.name} by {diff_roi:.2f}% in ROI.")
        elif diff_roi < 0:
            insights.append(f"ROI Analysis: {c2.name} outperformed {c1.name} by {abs(diff_roi):.2f}% in ROI.")
        else:
            insights.append(f"ROI Analysis: Both campaigns have identical ROI ({c1.roi}%).")
            
        # CTR Analysis
        diff_ctr = c1.ctr - c2.ctr
        if diff_ctr > 0:
            insights.append(f"Engagement: {c1.name} had better engagement with {c1.ctr}% CTR vs {c2.ctr}%.")
        elif diff_ctr < 0:
            insights.append(f"Engagement: {c2.name} had better engagement with {c2.ctr}% CTR vs {c1.ctr}%.")
            
        # Cost Efficiency (CPA)
        cpa1 = c1.cost / c1.conversions if c1.conversions > 0 else 0
        cpa2 = c2.cost / c2.conversions if c2.conversions > 0 else 0
        
        if cpa1 > 0 and cpa2 > 0:
            if cpa1 < cpa2:
                insights.append(f"Cost Efficiency: {c1.name} acquired customers cheaper (₹{cpa1:.2f}/conv) than {c2.name} (₹{cpa2:.2f}/conv).")
            elif cpa2 < cpa1:
                insights.append(f"Cost Efficiency: {c2.name} acquired customers cheaper (₹{cpa2:.2f}/conv) than {c1.name} (₹{cpa1:.2f}/conv).")
                
    elif len(campaigns) > 2:
        best_roi = max(campaigns, key=lambda c: c.roi)
        best_ctr = max(campaigns, key=lambda c: c.ctr)
        insights.append(f"Top Performer: {best_roi.name} is the most profitable campaign with {best_roi.roi}% ROI.")
        insights.append(f"Highest Engagement: {best_ctr.name} leads in engagement with {best_ctr.ctr}% CTR.")
        
    return insights

def generate_automated_recommendations(campaigns):
    """Generates actionable recommendations based on data analysis."""
    recommendations = []
    
    if not campaigns:
        return []
        
    # Convert to DataFrame for easier analysis
    data = [c.to_dict() for c in campaigns]
    df = pd.DataFrame(data)
    
    # 1. ROI Analysis
    high_roi = df[df['roi'] > 200]
    if not high_roi.empty:
        channels = high_roi['channel'].unique()
        recommendations.append(f"🚀 **Scale Up:** Increase budget for high-performing channels: {', '.join(channels)}. They are generating >200% ROI.")
        
    negative_roi = df[df['roi'] < 0]
    if not negative_roi.empty:
        names = negative_roi['name'].head(3).tolist()
        recommendations.append(f"⚠️ **Stop/Optimize:** The following campaigns have negative ROI: {', '.join(names)}. Review targeting or creatives immediately.")

    # 2. CAC Analysis
    avg_cac = df['cac'].mean()
    high_cac = df[df['cac'] > (avg_cac * 1.5)]
    if not high_cac.empty:
        recommendations.append(f"💰 **Cost Alert:** Customer Acquisition Cost (CAC) is too high for {len(high_cac)} campaigns (Avg: ₹{avg_cac:.2f}). Focus on conversion rate optimization.")

    return recommendations

# --- STATISTICAL ANALYSIS FUNCTIONS ---

def chi_square_test(control_conversions, control_clicks, variant_conversions, variant_clicks):
    """
    Performs chi-square test for A/B test statistical significance.
    Returns: chi_square_stat, p_value, is_significant
    """
    # Create contingency table
    control_non_conversions = control_clicks - control_conversions
    variant_non_conversions = variant_clicks - variant_conversions
    
    contingency_table = np.array([
        [control_conversions, control_non_conversions],
        [variant_conversions, variant_non_conversions]
    ])
    
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
    
    # 0.05 significance level (95% confidence)
    is_significant = p_value < 0.05
    
    return chi2, p_value, is_significant

def calculate_confidence_interval(conversions, clicks, confidence=0.95):
    """
    Calculates confidence interval for conversion rate.
    Returns: (lower_bound, upper_bound, z_score)
    """
    conversion_rate = conversions / clicks if clicks > 0 else 0
    
    # Standard error for binomial proportion
    se = np.sqrt((conversion_rate * (1 - conversion_rate)) / clicks) if clicks > 0 else 0
    
    z_score = stats.norm.ppf((1 + confidence) / 2)  # 1.96 for 95% CI
    
    margin_of_error = z_score * se
    lower = max(0, conversion_rate - margin_of_error)
    upper = min(1, conversion_rate + margin_of_error)
    
    return lower * 100, upper * 100, z_score

def calculate_lift(control_value, variant_value):
    """Calculate percentage lift from control to variant."""
    if control_value == 0:
        return 0
    return ((variant_value - control_value) / control_value) * 100

def get_channel_performance(channel_name):
    """Get aggregated performance metrics by channel."""
    campaigns = Campaign.query.filter_by(channel=channel_name).all()
    
    if not campaigns:
        return None
    
    total_impressions = sum(c.impressions for c in campaigns)
    total_clicks = sum(c.clicks for c in campaigns)
    total_conversions = sum(c.conversions for c in campaigns)
    total_revenue = sum(c.revenue for c in campaigns)
    total_cost = sum(c.cost for c in campaigns)
    
    avg_ctr = np.mean([c.ctr for c in campaigns])
    avg_conversion_rate = np.mean([c.conversion_rate for c in campaigns])
    avg_roi = np.mean([c.roi for c in campaigns])
    
    return {
        'channel': channel_name,
        'total_campaigns': len(campaigns),
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'total_conversions': total_conversions,
        'total_revenue': round(total_revenue, 2),
        'total_cost': round(total_cost, 2),
        'net_profit': round(total_revenue - total_cost, 2),
        'avg_ctr': round(avg_ctr, 2),
        'avg_conversion_rate': round(avg_conversion_rate, 2),
        'avg_roi': round(avg_roi, 2),
        'roas': round((total_revenue / total_cost) if total_cost > 0 else 0, 2)
    }

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyzes campaign data using pandas and numpy for robust calculations."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided. Please fill in the form fields."}), 400
        
        # Extract and validate required fields
        impressions = float(data.get('impressions', 0) or 0)
        clicks = float(data.get('clicks', 0) or 0)
        conversions = float(data.get('conversions', 0) or 0)
        revenue = float(data.get('revenue', 0) or 0)
        cost = float(data.get('cost', 0) or 0)
        
        # Validate data
        if impressions < 0 or clicks < 0 or conversions < 0 or revenue < 0 or cost < 0:
            return jsonify({"error": "All values must be positive numbers."}), 400
        
        if clicks > impressions:
            return jsonify({"error": "Clicks cannot exceed impressions."}), 400
        
        if conversions > clicks:
            return jsonify({"error": "Conversions cannot exceed clicks."}), 400
        
        # Calculate metrics
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
        net_profit = revenue - cost
        roi = ((revenue - cost) / cost * 100) if cost > 0 else 0

        response = {
            "CTR (%)": round(float(ctr), 2),
            "Conversion Rate (%)": round(float(conversion_rate), 2),
            "ROI (%)": round(float(roi), 2)
        }
        
        return jsonify(response)

    except Exception as e:
        import traceback
        app.logger.error(f"Error in /analyze: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": f"Invalid data or server error: {str(e)}"}), 400

@app.route('/generate-report-image', methods=['POST'])
def generate_report_image():
    """Generates a financial summary chart image using Matplotlib."""
    data = request.get_json()
    revenue = data.get('revenue', 0)
    cost = data.get('cost', 0)

    fig, ax = plt.subplots(figsize=(8, 5))

    labels = ['Gross Revenue', 'Operational Cost']
    values = [revenue, cost]
    colors = ['#00BFFF', '#FF4500'] # Holographic Blue, Energetic Orange-Red

    bars = ax.bar(labels, values, color=colors, width=0.5)

    ax.set_ylabel('Amount (₹)', fontsize=12)
    ax.set_title('Financial Summary', fontsize=16, weight='bold', pad=20)
    ax.yaxis.grid(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + (max(values) * 0.02), f'₹{yval:,.2f}', ha='center', va='bottom', color=bar.get_color(), fontsize=11)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)

    return send_file(buf, mimetype='image/png')


@app.route('/generate-detailed-report', methods=['POST'])
def generate_detailed_report():
    """Generates a comprehensive HTML report with all campaign metrics."""
    data = request.get_json()
    
    try:
        # Extract data
        campaign_name = data.get('name', 'Unnamed Campaign')
        impressions = int(data.get('impressions', 0))
        clicks = int(data.get('clicks', 0))
        conversions = int(data.get('conversions', 0))
        revenue = float(data.get('revenue', 0))
        cost = float(data.get('cost', 0))
        
        # Calculate metrics
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
        roi = ((revenue - cost) / cost * 100) if cost > 0 else 0
        net_profit = revenue - cost
        cpc = cost / clicks if clicks > 0 else 0  # Cost per click
        cpa = cost / conversions if conversions > 0 else 0  # Cost per acquisition
        rpm = (revenue / impressions * 1000) if impressions > 0 else 0  # Revenue per mille
        
        # Create HTML report
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>INDRA Campaign Report - {campaign_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #0A192F 0%, #112240 100%);
            color: #E0E0E0;
            padding: 40px;
            min-height: 100vh;
        }}
        .report-container {{
            max-width: 900px;
            margin: 0 auto;
            background: rgba(17, 34, 64, 0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(0, 191, 255, 0.3);
        }}
        .report-header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid rgba(0, 191, 255, 0.3);
        }}
        .report-header h1 {{
            color: #00BFFF;
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(0, 191, 255, 0.5);
        }}
        .report-header .campaign-name {{
            font-size: 1.5rem;
            color: #D4AF37;
            font-weight: 600;
        }}
        .report-header .date {{
            color: #A0A0A0;
            margin-top: 10px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: rgba(0, 191, 255, 0.1);
            border: 1px solid rgba(0, 191, 255, 0.3);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 191, 255, 0.3);
        }}
        .metric-card.highlight {{
            background: linear-gradient(135deg, rgba(0, 191, 255, 0.2), rgba(0, 191, 255, 0.05));
            border-color: #00BFFF;
        }}
        .metric-card.positive {{ border-color: #4CAF50; }}
        .metric-card.negative {{ border-color: #FF4500; }}
        .metric-label {{
            font-size: 0.85rem;
            color: #A0A0A0;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        .metric-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #E0E0E0;
        }}
        .metric-value.positive {{ color: #4CAF50; }}
        .metric-value.negative {{ color: #FF4500; }}
        .section-title {{
            color: #00BFFF;
            font-size: 1.3rem;
            margin: 30px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(0, 191, 255, 0.3);
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .data-table th {{
            background: rgba(0, 191, 255, 0.1);
            padding: 15px;
            text-align: left;
            color: #00BFFF;
            font-weight: 600;
        }}
        .data-table td {{
            padding: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .data-table tr:hover {{
            background: rgba(0, 191, 255, 0.05);
        }}
        .performance-bar {{
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            margin-top: 10px;
            overflow: hidden;
        }}
        .performance-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 1s ease;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: #A0A0A0;
            font-size: 0.9rem;
        }}
        .insights {{
            background: rgba(212, 175, 55, 0.1);
            border: 1px solid rgba(212, 175, 55, 0.3);
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }}
        .insights h4 {{
            color: #D4AF37;
            margin-bottom: 15px;
        }}
        .insight-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            color: #E0E0E0;
        }}
        .insight-item i {{
            color: #D4AF37;
        }}
        @media print {{
            body {{ background: white; color: black; }}
            .report-container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1>📊 INDRA Campaign Report</h1>
            <div class="campaign-name">{campaign_name}</div>
            <div class="date">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card highlight">
                <div class="metric-label">Return on Investment</div>
                <div class="metric-value {'positive' if roi >= 0 else 'negative'}">{roi:.2f}%</div>
                <div class="performance-bar">
                    <div class="performance-fill" style="width: {min(abs(roi), 100)}%; background: {'#4CAF50' if roi >= 0 else '#FF4500'}"></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Net Profit</div>
                <div class="metric-value {'positive' if net_profit >= 0 else 'negative'}">₹{net_profit:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Revenue</div>
                <div class="metric-value">₹{revenue:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Click-Through Rate</div>
                <div class="metric-value">{ctr:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Conversion Rate</div>
                <div class="metric-value">{conversion_rate:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Cost</div>
                <div class="metric-value">₹{cost:,.2f}</div>
            </div>
        </div>
        
        <h3 class="section-title">📈 Detailed Metrics</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Impressions</td>
                    <td>{impressions:,}</td>
                    <td>Total times ad was displayed</td>
                </tr>
                <tr>
                    <td>Clicks</td>
                    <td>{clicks:,}</td>
                    <td>Total ad clicks received</td>
                </tr>
                <tr>
                    <td>Conversions</td>
                    <td>{conversions:,}</td>
                    <td>Total desired actions completed</td>
                </tr>
                <tr>
                    <td>Cost Per Click (CPC)</td>
                    <td>₹{cpc:.2f}</td>
                    <td>Average cost per click</td>
                </tr>
                <tr>
                    <td>Cost Per Acquisition (CPA)</td>
                    <td>₹{cpa:.2f}</td>
                    <td>Average cost per conversion</td>
                </tr>
                <tr>
                    <td>Revenue Per Mille (RPM)</td>
                    <td>₹{rpm:.2f}</td>
                    <td>Revenue per 1000 impressions</td>
                </tr>
            </tbody>
        </table>
        
        <div class="insights">
            <h4>💡 Key Insights</h4>
            <div class="insight-item">
                <i class="fa-solid fa-arrow-trend-up"></i>
                <span>{'Your campaign is profitable!' if roi > 0 else 'Your campaign is in loss. Consider optimizing your ad spend.'}</span>
            </div>
            <div class="insight-item">
                <i class="fa-solid fa-crosshairs"></i>
                <span>CTR of {ctr:.2f}% is {'above' if ctr > 2 else 'below'} industry average of 2%</span>
            </div>
            <div class="insight-item">
                <i class="fa-solid fa-bullseye"></i>
                <span>Conversion rate of {conversion_rate:.2f}% means {conversions} conversions from {clicks} clicks</span>
            </div>
            <div class="insight-item">
                <i class="fa-solid fa-coins"></i>
                <span>Each conversion costs ₹{cpa:.2f} on average</span>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by INDRA - Intelligent Network Data ROI Analytics</p>
            <p>© {datetime.now().year} INDRA Analytics</p>
            <p>Presented by:</p>
            <ul style="list-style-position: inside; padding-left:0; color:#A0A0A0; font-size:0.85rem;">
                <li>G.S.S. Akhil</li>
                <li>G. Seshidhar</li>
                <li>G.V. Bhadra Rao</li>
                <li>K.V.S. Srikar</li>
                <li>K. Vamsi Krishna</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
        
        return jsonify({
            "success": True,
            "report": html_content
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 400

@app.route('/generate-pdf-report', methods=['POST'])
def generate_pdf_report():
    """Generates a professional PDF report using ReportLab."""
    data = request.get_json()
    
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            'Title', parent=styles['Heading1'], alignment=TA_CENTER, textColor=colors.HexColor('#00BFFF')
        )
        elements.append(Paragraph(f"INDRA Campaign Report: {data.get('name', 'Unnamed')}", title_style))
        elements.append(Spacer(1, 20))

        # Metrics Data
        metrics_data = [
            ['Metric', 'Value'],
            ['Impressions', f"{int(data.get('impressions', 0)):,}"],
            ['Clicks', f"{int(data.get('clicks', 0)):,}"],
            ['Conversions', f"{int(data.get('conversions', 0)):,}"],
            ['Revenue', f"₹{float(data.get('revenue', 0)):,.2f}"],
            ['Cost', f"₹{float(data.get('cost', 0)):,.2f}"],
            ['Net Profit', f"₹{float(data.get('revenue', 0) - data.get('cost', 0)):,.2f}"],
            ['CTR', f"{(data.get('clicks', 0) / data.get('impressions', 1) * 100):.2f}%"],
            ['ROI', f"{((data.get('revenue', 0) - data.get('cost', 1)) / data.get('cost', 1) * 100):.2f}%"]
        ]

        # Table Style
        table = Table(metrics_data, colWidths=[200, 200])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A192F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F0F4F8')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        # Footer
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, textColor=colors.grey)
        elements.append(Paragraph(f"Generated by INDRA Analytics on {datetime.now().strftime('%Y-%m-%d')}", footer_style))

        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer, 
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"indra_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        )

    except Exception as e:
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 400

@app.route('/generate-comparison-pdf', methods=['POST'])
def generate_comparison_pdf():
    """Generates a PDF comparing two or more campaigns."""
    data = request.get_json()
    campaign_ids = data.get('campaign_ids', [])

    try:
        campaigns = Campaign.query.filter(Campaign.id.in_(campaign_ids)).all()
        if not campaigns:
            return jsonify({"error": "No campaigns found"}), 404

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            'Title', parent=styles['Heading1'], alignment=TA_CENTER, textColor=colors.HexColor('#00BFFF')
        )
        elements.append(Paragraph("INDRA Campaign Comparison Report", title_style))
        elements.append(Spacer(1, 20))

        # Header Row
        headers = ['Metric'] + [c.name[:15] for c in campaigns]
        
        # Data Rows
        rows = [
            ['Impressions'] + [f"{c.impressions:,}" for c in campaigns],
            ['Clicks'] + [f"{c.clicks:,}" for c in campaigns],
            ['Conversions'] + [f"{c.conversions:,}" for c in campaigns],
            ['Revenue'] + [f"₹{c.revenue:,.2f}" for c in campaigns],
            ['Cost'] + [f"₹{c.cost:,.2f}" for c in campaigns],
            ['CTR'] + [f"{c.ctr:.2f}%" for c in campaigns],
            ['ROI'] + [f"{c.roi:.2f}%" for c in campaigns]
        ]

        data_table = [headers] + rows

        # Dynamic Column Widths
        col_width = 450 / len(campaigns)
        table = Table(data_table, colWidths=[100] + [col_width] * len(campaigns))

        # Styling
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A192F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ])

        # Highlight Best ROI (Last Row)
        rois = [c.roi for c in campaigns]
        best_idx = rois.index(max(rois))
        style.add('BACKGROUND', (best_idx + 1, 7), (best_idx + 1, 7), colors.HexColor('#d4edda')) # Light Green

        table.setStyle(style)
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)

        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='comparison_report.pdf')

    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 400


@app.route('/export/selected-csv', methods=['POST'])
def export_selected_csv():
    """Export selected campaigns to CSV."""
    data = request.get_json()
    campaign_ids = data.get('campaign_ids', [])
    
    try:
        if not campaign_ids:
            return jsonify({"error": "No campaigns selected"}), 400
            
        campaigns = Campaign.query.filter(Campaign.id.in_(campaign_ids)).all()
        
        if not campaigns:
            return jsonify({"error": "No campaigns found"}), 404
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Name', 'Impressions', 'Clicks', 'Conversions', 
            'Revenue (₹)', 'Cost (₹)', 'CTR (%)', 'Conversion Rate (%)', 
            'ROI (%)', 'Created At'
        ])
        
        # Write data
        for c in campaigns:
            writer.writerow([
                c.id, c.name, c.impressions, c.clicks, c.conversions,
                round(c.revenue, 2), round(c.cost, 2), c.ctr, 
                c.conversion_rate, c.roi, c.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        
        # Convert to bytes
        output_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
        output_bytes.seek(0)
        
        return send_file(
            output_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'indra_selected_campaigns_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    except Exception as e:
        return jsonify({"error": f"Failed to export CSV: {str(e)}"}), 400


@app.route('/campaigns/<int:campaign_id>/report', methods=['GET'])
def campaign_single_report(campaign_id):
    """Generate a report for a single saved campaign."""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        
        # Prepare data for detailed report
        data = {
            'name': campaign.name,
            'impressions': campaign.impressions,
            'clicks': campaign.clicks,
            'conversions': campaign.conversions,
            'revenue': campaign.revenue,
            'cost': campaign.cost
        }
        
        # Call the detailed report function
        return generate_detailed_report_internal(data)
        
    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 400


def generate_detailed_report_internal(data):
    """Internal function to generate detailed report HTML."""
    campaign_name = data.get('name', 'Unnamed Campaign')
    impressions = int(data.get('impressions', 0))
    clicks = int(data.get('clicks', 0))
    conversions = int(data.get('conversions', 0))
    revenue = float(data.get('revenue', 0))
    cost = float(data.get('cost', 0))
    
    # Calculate metrics
    ctr = (clicks / impressions * 100) if impressions > 0 else 0
    conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
    roi = ((revenue - cost) / cost * 100) if cost > 0 else 0
    net_profit = revenue - cost
    cpc = cost / clicks if clicks > 0 else 0
    cpa = cost / conversions if conversions > 0 else 0
    rpm = (revenue / impressions * 1000) if impressions > 0 else 0
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>INDRA Campaign Report - {campaign_name}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/js/all.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #0A192F 0%, #112240 100%);
            color: #E0E0E0;
            padding: 40px;
            min-height: 100vh;
        }}
        .report-container {{
            max-width: 900px;
            margin: 0 auto;
            background: rgba(17, 34, 64, 0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(0, 191, 255, 0.3);
        }}
        .report-header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid rgba(0, 191, 255, 0.3);
        }}
        .report-header h1 {{
            color: #00BFFF;
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(0, 191, 255, 0.5);
        }}
        .report-header .campaign-name {{
            font-size: 1.5rem;
            color: #D4AF37;
            font-weight: 600;
        }}
        .report-header .date {{
            color: #A0A0A0;
            margin-top: 10px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: rgba(0, 191, 255, 0.1);
            border: 1px solid rgba(0, 191, 255, 0.3);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 191, 255, 0.3);
        }}
        .metric-card.highlight {{
            background: linear-gradient(135deg, rgba(0, 191, 255, 0.2), rgba(0, 191, 255, 0.05));
            border-color: #00BFFF;
        }}
        .metric-card.positive {{ border-color: #4CAF50; }}
        .metric-card.negative {{ border-color: #FF4500; }}
        .metric-label {{
            font-size: 0.85rem;
            color: #A0A0A0;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        .metric-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #E0E0E0;
        }}
        .metric-value.positive {{ color: #4CAF50; }}
        .metric-value.negative {{ color: #FF4500; }}
        .section-title {{
            color: #00BFFF;
            font-size: 1.3rem;
            margin: 30px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(0, 191, 255, 0.3);
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .data-table th {{
            background: rgba(0, 191, 255, 0.1);
            padding: 15px;
            text-align: left;
            color: #00BFFF;
            font-weight: 600;
        }}
        .data-table td {{
            padding: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .data-table tr:hover {{
            background: rgba(0, 191, 255, 0.05);
        }}
        .performance-bar {{
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            margin-top: 10px;
            overflow: hidden;
        }}
        .performance-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 1s ease;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: #A0A0A0;
            font-size: 0.9rem;
        }}
        .insights {{
            background: rgba(212, 175, 55, 0.1);
            border: 1px solid rgba(212, 175, 55, 0.3);
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }}
        .insights h4 {{
            color: #D4AF37;
            margin-bottom: 15px;
        }}
        .insight-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            color: #E0E0E0;
        }}
        .insight-item i {{
            color: #D4AF37;
        }}
        @media print {{
            body {{ background: white; color: black; }}
            .report-container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1>📊 INDRA Campaign Report</h1>
            <div class="campaign-name">{campaign_name}</div>
            <div class="date">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card highlight">
                <div class="metric-label">Return on Investment</div>
                <div class="metric-value {'positive' if roi >= 0 else 'negative'}">{roi:.2f}%</div>
                <div class="performance-bar">
                    <div class="performance-fill" style="width: {min(abs(roi), 100)}%; background: {'#4CAF50' if roi >= 0 else '#FF4500'}"></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Net Profit</div>
                <div class="metric-value {'positive' if net_profit >= 0 else 'negative'}">₹{net_profit:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Revenue</div>
                <div class="metric-value">₹{revenue:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Click-Through Rate</div>
                <div class="metric-value">{ctr:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Conversion Rate</div>
                <div class="metric-value">{conversion_rate:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Cost</div>
                <div class="metric-value">₹{cost:,.2f}</div>
            </div>
        </div>
        
        <h3 class="section-title">📈 Detailed Metrics</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Impressions</td>
                    <td>{impressions:,}</td>
                    <td>Total times ad was displayed</td>
                </tr>
                <tr>
                    <td>Clicks</td>
                    <td>{clicks:,}</td>
                    <td>Total ad clicks received</td>
                </tr>
                <tr>
                    <td>Conversions</td>
                    <td>{conversions:,}</td>
                    <td>Total desired actions completed</td>
                </tr>
                <tr>
                    <td>Cost Per Click (CPC)</td>
                    <td>₹{cpc:.2f}</td>
                    <td>Average cost per click</td>
                </tr>
                <tr>
                    <td>Cost Per Acquisition (CPA)</td>
                    <td>₹{cpa:.2f}</td>
                    <td>Average cost per conversion</td>
                </tr>
                <tr>
                    <td>Revenue Per Mille (RPM)</td>
                    <td>₹{rpm:.2f}</td>
                    <td>Revenue per 1000 impressions</td>
                </tr>
            </tbody>
        </table>
        
        <div class="insights">
            <h4>💡 Key Insights</h4>
            <div class="insight-item">
                <i class="fa-solid fa-arrow-trend-up"></i>
                <span>{'Your campaign is profitable!' if roi > 0 else 'Your campaign is in loss. Consider optimizing your ad spend.'}</span>
            </div>
            <div class="insight-item">
                <i class="fa-solid fa-crosshairs"></i>
                <span>CTR of {ctr:.2f}% is {'above' if ctr > 2 else 'below'} industry average of 2%</span>
            </div>
            <div class="insight-item">
                <i class="fa-solid fa-bullseye"></i>
                <span>Conversion rate of {conversion_rate:.2f}% means {conversions} conversions from {clicks} clicks</span>
            </div>
            <div class="insight-item">
                <i class="fa-solid fa-coins"></i>
                <span>Each conversion costs ₹{cpa:.2f} on average</span>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by INDRA - Intelligent Network Data ROI Analytics</p>
            <p>© {datetime.now().year} INDRA Analytics</p>
            <p>Presented by:</p>
            <ul style="list-style-position: inside; padding-left:0; color:#A0A0A0; font-size:0.85rem;">
                <li>G.S.S. Akhil</li>
                <li>G. Seshidhar</li>
                <li>G.V. Bhadra Rao</li>
                <li>K.V.S. Srikar</li >
                <li>K. Vamsi Krishna</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
    
    return jsonify({
        "success": True,
        "report": html_content
    })

# --- NEW ENDPOINTS FOR PROTOTYPE ---

@app.route('/save-campaign', methods=['POST'])
def save_campaign():
    """Save campaign data to database."""
    data = request.get_json()
    
    try:
        # The data comes from `currentResult` in JS, which is a mix of inputs and results.
        # Let's get everything from the posted JSON.
        
        impressions = int(data.get('impressions', 0))
        clicks = int(data.get('clicks', 0))
        conversions = int(data.get('conversions', 0))
        revenue = float(data.get('revenue', 0))
        cost = float(data.get('cost', 0))
        
        # Use 'name' from JS, fallback to 'campaign_name' for old versions, then generate.
        name = data.get('name') or data.get('campaign_name') or f"Campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Recalculating is safer to ensure DB consistency.
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
        roi = ((revenue - cost) / cost * 100) if cost > 0 else 0
        
        # Create campaign record with all fields
        campaign = Campaign(
            name=name,
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            revenue=revenue,
            cost=cost,
            ctr=round(ctr, 2),
            conversion_rate=round(conversion_rate, 2),
            roi=round(roi, 2),
            channel=data.get('channel', 'Direct'),
            test_variant=data.get('test_variant', 'Control'),
            test_group=data.get('test_group'),
            test_duration_days=data.get('test_duration_days', 7),
            sample_size=data.get('sample_size')
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Campaign saved successfully",
            "campaign": campaign.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        app.logger.error(f"Error in /save-campaign: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to save campaign: {str(e)}"}), 400

@app.route('/campaigns', methods=['GET'])
def get_all_campaigns():
    """Get all campaigns from database."""
    try:
        campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
        return jsonify({
            "success": True,
            "campaigns": [c.to_dict() for c in campaigns]
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch campaigns: {str(e)}"}), 400

@app.route('/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get a specific campaign by ID."""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        return jsonify({
            "success": True,
            "campaign": campaign.to_dict()
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch campaign: {str(e)}"}), 400

@app.route('/campaigns/<int:campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    """Delete a campaign by ID."""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        
        db.session.delete(campaign)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Campaign deleted successfully"
        })
    except Exception as e:
        return jsonify({"error": f"Failed to delete campaign: {str(e)}"}), 400

@app.route('/campaigns/compare', methods=['POST'])
def compare_campaigns():
    """Compare multiple campaigns."""
    data = request.get_json()
    campaign_ids = data.get('campaign_ids', [])
    
    try:
        campaigns = Campaign.query.filter(Campaign.id.in_(campaign_ids)).all()
        
        if not campaigns:
            return jsonify({"error": "No campaigns found"}), 404
        
        # Calculate aggregate statistics
        total_revenue = sum(c.revenue for c in campaigns)
        total_cost = sum(c.cost for c in campaigns)
        avg_ctr = np.mean([c.ctr for c in campaigns])
        avg_conversion = np.mean([c.conversion_rate for c in campaigns])
        avg_roi = np.mean([c.roi for c in campaigns])
        
        # Find best performers
        best_roi = max(campaigns, key=lambda c: c.roi)
        best_ctr = max(campaigns, key=lambda c: c.ctr)
        best_conversion = max(campaigns, key=lambda c: c.conversion_rate)
        
        insights = generate_comparison_insights(campaigns)
        
        return jsonify({
            "success": True,
            "comparison": {
                "campaigns": [c.to_dict() for c in campaigns],
                "summary": {
                    "total_campaigns": len(campaigns),
                    "total_revenue": round(total_revenue, 2),
                    "total_cost": round(total_cost, 2),
                    "net_profit": round(total_revenue - total_cost, 2),
                    "avg_ctr": round(avg_ctr, 2),
                    "avg_conversion_rate": round(avg_conversion, 2),
                    "avg_roi": round(avg_roi, 2)
                },
                "best_performers": {
                    "best_roi": best_roi.to_dict(),
                    "best_ctr": best_ctr.to_dict(),
                    "best_conversion": best_conversion.to_dict()
                },
                "insights": insights
            }
        })
    except Exception as e:
        return jsonify({"error": f"Failed to compare campaigns: {str(e)}"}), 400

@app.route('/export/csv', methods=['POST'])
def export_csv():
    """Export campaigns to CSV."""
    data = request.get_json()
    campaign_ids = data.get('campaign_ids', [])
    
    try:
        if campaign_ids:
            campaigns = Campaign.query.filter(Campaign.id.in_(campaign_ids)).all()
        else:
            campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Name', 'Impressions', 'Clicks', 'Conversions', 
            'Revenue (₹)', 'Cost (₹)', 'CTR (%)', 'Conversion Rate (%)', 
            'ROI (%)', 'Created At'
        ])
        
        # Write data
        for c in campaigns:
            writer.writerow([
                c.id, c.name, c.impressions, c.clicks, c.conversions,
                round(c.revenue, 2), round(c.cost, 2), c.ctr, 
                c.conversion_rate, c.roi, c.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        
        # Convert to bytes
        output_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
        output_bytes.seek(0)
        
        return send_file(
            output_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'indra_campaigns_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    except Exception as e:
        return jsonify({"error": f"Failed to export CSV: {str(e)}"}), 400

@app.route('/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Get dashboard statistics."""
    try:
        campaigns = Campaign.query.all()
        
        if not campaigns:
            return jsonify({
                "success": True,
                "stats": {
                    "total_campaigns": 0,
                    "total_revenue": 0,
                    "total_cost": 0,
                    "net_profit": 0,
                    "avg_ctr": 0,
                    "avg_conversion_rate": 0,
                    "avg_roi": 0,
                    "top_campaigns": [],
                    "recent_campaigns": []
                }
            })
        
        total_revenue = sum(c.revenue for c in campaigns)
        total_cost = sum(c.cost for c in campaigns)
        
        # Top 5 by ROI
        top_campaigns = sorted(campaigns, key=lambda c: c.roi, reverse=True)[:5]
        
        # Recent 5
        recent_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).limit(5).all()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_campaigns": len(campaigns),
                "total_revenue": round(total_revenue, 2),
                "total_cost": round(total_cost, 2),
                "net_profit": round(total_revenue - total_cost, 2),
                "avg_ctr": round(np.mean([c.ctr for c in campaigns]), 2),
                "avg_conversion_rate": round(np.mean([c.conversion_rate for c in campaigns]), 2),
                "avg_roi": round(np.mean([c.roi for c in campaigns]), 2),
                "top_campaigns": [c.to_dict() for c in top_campaigns],
                "recent_campaigns": [c.to_dict() for c in recent_campaigns]
            }
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch stats: {str(e)}"}), 400

@app.route('/dashboard/trends', methods=['GET'])
def dashboard_trends():
    """Get data for performance trends over time."""
    try:
        campaigns = Campaign.query.order_by(Campaign.created_at.asc()).all()
        
        if not campaigns:
            return jsonify({"success": True, "trends": {"dates": [], "roi": [], "ctr": []}})
            
        df = pd.DataFrame([c.to_dict() for c in campaigns])
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.set_index('created_at')
        
        # Resample by day and calculate mean for metrics
        trends = df.resample('D').agg({
            'roi': 'mean',
            'ctr': 'mean',
            'revenue': 'sum',
            'cost': 'sum'
        }).fillna(0) # fill non-existing days with 0
        
        # Reset index to get date as a column
        trends = trends.reset_index()
        
        return jsonify({
            "success": True,
            "trends": {
                "dates": trends['created_at'].dt.strftime('%Y-%m-%d').tolist(),
                "roi": trends['roi'].round(2).tolist(),
                "ctr": trends['ctr'].round(2).tolist(),
                "revenue": trends['revenue'].round(2).tolist()
            }
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch trend data: {str(e)}"}), 400

@app.route('/generate-comparison-chart', methods=['POST'])
def generate_comparison_chart():
    """Generate a comparison chart for multiple campaigns."""
    data = request.get_json()
    campaign_ids = data.get('campaign_ids', [])
    
    try:
        campaigns = Campaign.query.filter(Campaign.id.in_(campaign_ids)).all()
        
        if len(campaigns) < 2:
            return jsonify({"error": "Need at least 2 campaigns to compare"}), 400
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        names = [c.name[:15] + '...' if len(c.name) > 15 else c.name for c in campaigns]
        
        # CTR Comparison
        ctr_values = [c.ctr for c in campaigns]
        axes[0].bar(names, ctr_values, color='#00BFFF', alpha=0.8)
        axes[0].set_title('CTR (%) Comparison', fontsize=12, weight='bold')
        axes[0].set_ylabel('CTR (%)')
        axes[0].tick_params(axis='x', rotation=45)
        
        # Conversion Rate Comparison
        conv_values = [c.conversion_rate for c in campaigns]
        axes[1].bar(names, conv_values, color='#D4AF37', alpha=0.8)
        axes[1].set_title('Conversion Rate (%) Comparison', fontsize=12, weight='bold')
        axes[1].set_ylabel('Conversion Rate (%)')
        axes[1].tick_params(axis='x', rotation=45)
        
        # ROI Comparison
        roi_values = [c.roi for c in campaigns]
        colors = ['#4CAF50' if r > 0 else '#FF5252' for r in roi_values]
        axes[2].bar(names, roi_values, color=colors, alpha=0.8)
        axes[2].set_title('ROI (%) Comparison', fontsize=12, weight='bold')
        axes[2].set_ylabel('ROI (%)')
        axes[2].tick_params(axis='x', rotation=45)
        axes[2].axhline(y=0, color='white', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close(fig)
        buf.seek(0)
        
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": f"Failed to generate chart: {str(e)}"}), 400

@app.route('/import/campaigns', methods=['POST'])
def import_campaigns():
    """Import campaigns from CSV or Excel file."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Get file extension
        filename = file.filename.lower()
        
        # Read file based on extension
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return jsonify({"error": "Unsupported file format. Please use CSV or Excel files."}), 400
        
        # Normalize column names (handle various formats)
        column_mapping = {
            'campaign name': 'name',
            'campaign_name': 'name',
            'name': 'name',
            'impressions': 'impressions',
            'impression': 'impressions',
            'clicks': 'clicks',
            'click': 'clicks',
            'conversions': 'conversions',
            'conversion': 'conversions',
            'revenue': 'revenue',
            'sales': 'revenue',
            'cost': 'cost',
            'spend': 'cost',
            'costs': 'cost'
        }
        
        # Normalize column names
        df.columns = [col.lower().strip() for col in df.columns]
        df = df.rename(columns=column_mapping)
        
        # Validate required columns
        required_cols = ['name', 'impressions', 'clicks', 'conversions', 'revenue', 'cost']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return jsonify({
                "error": f"Missing required columns: {', '.join(missing_cols)}. Required columns: Name, Impressions, Clicks, Conversions, Revenue, Cost"
            }), 400
        
        # Convert columns to numeric, handling any errors
        for col in ['impressions', 'clicks', 'conversions', 'revenue', 'cost']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calculate metrics for each row
        saved_campaigns = []
        saved_campaign_objects = []
        errors = []
        
        for idx, row in df.iterrows():
            try:
                name = str(row['name']) if pd.notna(row['name']) else f"Campaign_{idx+1}"
                impressions = int(row['impressions'])
                clicks = int(row['clicks'])
                conversions = int(row['conversions'])
                revenue = float(row['revenue'])
                cost = float(row['cost'])
                channel = str(row['channel']) if 'channel' in df.columns and pd.notna(row['channel']) else 'Direct'
                variant = str(row['test_variant']) if 'test_variant' in df.columns and pd.notna(row['test_variant']) else 'Control'
                
                # Calculate metrics
                ctr = (clicks / impressions * 100) if impressions > 0 else 0
                conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
                roi = ((revenue - cost) / cost * 100) if cost > 0 else 0
                
                campaign = Campaign(
                    name=name,
                    impressions=impressions,
                    clicks=clicks,
                    conversions=conversions,
                    revenue=revenue,
                    cost=cost,
                    ctr=round(ctr, 2),
                    conversion_rate=round(conversion_rate, 2),
                    roi=round(roi, 2),
                    channel=channel,
                    test_variant=variant
                )
                
                db.session.add(campaign)
                saved_campaigns.append(name)
                saved_campaign_objects.append(campaign)
                
            except Exception as e:
                errors.append(f"Row {idx+1}: {str(e)}")
        
        # Commit all campaigns
        db.session.commit()
        
        insights = generate_comparison_insights(saved_campaign_objects)
        
        return jsonify({
            "success": True,
            "message": f"Successfully imported {len(saved_campaigns)} campaigns",
            "imported": len(saved_campaigns),
            "campaigns": saved_campaigns,
            "insights": insights,
            "errors": errors if errors else None
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to import file: {str(e)}"}), 400

@app.route('/import/template', methods=['GET'])
def get_import_template():
    """Generate a sample CSV template for import."""
    try:
        # Create sample data
        sample_data = [
            ['Name', 'Channel', 'Variant', 'Impressions', 'Clicks', 'Conversions', 'Revenue', 'Cost'],
            ['Summer Sale', 'Facebook', 'A', '10000', '500', '50', '5000', '2000'],
            ['Summer Sale', 'Facebook', 'B', '12000', '750', '80', '8000', '2500'],
            ['Google Search', 'Google Ads', 'Control', '20000', '1200', '150', '12000', '5000']
        ]
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        for row in sample_data:
            writer.writerow(row)
        
        output.seek(0)
        output_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
        output_bytes.seek(0)
        
        return send_file(
            output_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name='indra_template.csv'
        )
    except Exception as e:
        return jsonify({"error": f"Failed to generate template: {str(e)}"}), 400

# --- A/B TESTING ENDPOINTS ---

@app.route('/ab-test/analyze', methods=['POST'])
def analyze_ab_test():
    """Performs statistical analysis on A/B test results."""
    data = request.get_json()
    test_group = data.get('test_group')
    
    try:
        campaigns = Campaign.query.filter_by(test_group=test_group).all()
        
        if len(campaigns) < 2:
            return jsonify({"error": "Need at least 2 test variants to compare"}), 400
        
        # Separate control and variant
        control = next((c for c in campaigns if c.test_variant == 'Control'), campaigns[0])
        variants = [c for c in campaigns if c.test_variant != 'Control']
        
        results = []
        
        for variant in variants:
            # Chi-square test for conversion rate significance
            chi2, p_value, is_significant = chi_square_test(
                control.conversions, control.clicks,
                variant.conversions, variant.clicks
            )
            
            # Calculate lift
            ctr_lift = calculate_lift(control.ctr, variant.ctr)
            conv_lift = calculate_lift(control.conversion_rate, variant.conversion_rate)
            roi_lift = calculate_lift(control.roi, variant.roi)
            
            # Confidence intervals
            control_ci_lower, control_ci_upper, _ = calculate_confidence_interval(
                control.conversions, control.clicks
            )
            variant_ci_lower, variant_ci_upper, _ = calculate_confidence_interval(
                variant.conversions, variant.clicks
            )
            
            results.append({
                'control': {
                    'name': control.name,
                    'variant': control.test_variant,
                    'ctr': control.ctr,
                    'conversion_rate': control.conversion_rate,
                    'conversion_rate_ci': [round(control_ci_lower, 2), round(control_ci_upper, 2)],
                    'roi': control.roi,
                    'conversions': control.conversions,
                    'clicks': control.clicks
                },
                'variant': {
                    'name': variant.name,
                    'variant': variant.test_variant,
                    'ctr': variant.ctr,
                    'conversion_rate': variant.conversion_rate,
                    'conversion_rate_ci': [round(variant_ci_lower, 2), round(variant_ci_upper, 2)],
                    'roi': variant.roi,
                    'conversions': variant.conversions,
                    'clicks': variant.clicks
                },
                'statistical_test': {
                    'chi_square': round(chi2, 4),
                    'p_value': round(p_value, 6),
                    'is_significant': is_significant,
                    'confidence_level': '95%'
                },
                'lift': {
                    'ctr_lift_percent': round(ctr_lift, 2),
                    'conversion_lift_percent': round(conv_lift, 2),
                    'roi_lift_percent': round(roi_lift, 2)
                },
                'winner': variant.test_variant if conv_lift > 0 else control.test_variant,
                'recommendation': f"{variant.test_variant} shows {abs(round(conv_lift, 2))}% {'higher' if conv_lift > 0 else 'lower'} conversion rate" + 
                                 (f" (statistically significant, p={round(p_value, 4)})" if is_significant else " (not statistically significant)")
            })
        
        return jsonify({
            "success": True,
            "test_group": test_group,
            "duration_days": control.test_duration_days,
            "results": results
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to analyze A/B test: {str(e)}"}), 400

# --- MULTI-CHANNEL ENDPOINTS ---

@app.route('/channels', methods=['GET'])
def get_all_channels():
    """Get list of all unique channels."""
    try:
        channels = db.session.query(Campaign.channel).distinct().all()
        channel_list = [c[0] for c in channels]
        return jsonify({
            "success": True,
            "channels": channel_list
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch channels: {str(e)}"}), 400

@app.route('/channels/<channel_name>', methods=['GET'])
def get_channel_stats(channel_name):
    """Get performance stats for a specific channel."""
    try:
        stats = get_channel_performance(channel_name)
        
        if not stats:
            return jsonify({"error": f"No campaigns found for channel: {channel_name}"}), 404
        
        return jsonify({
            "success": True,
            "channel_stats": stats
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch channel stats: {str(e)}"}), 400

@app.route('/channels/comparison', methods=['POST'])
def compare_channels():
    """Compare performance across multiple channels."""
    data = request.get_json()
    channels = data.get('channels', [])
    
    try:
        if not channels:
            # Get all channels if none specified
            all_channels = db.session.query(Campaign.channel).distinct().all()
            channels = [c[0] for c in all_channels]
        
        comparison_data = []
        for channel in channels:
            stats = get_channel_performance(channel)
            if stats:
                comparison_data.append(stats)
        
        # Rank channels by ROI
        ranked_channels = sorted(comparison_data, key=lambda x: x['avg_roi'], reverse=True)
        
        return jsonify({
            "success": True,
            "channel_comparison": comparison_data,
            "ranked_by_roi": ranked_channels
        })
    except Exception as e:
        return jsonify({"error": f"Failed to compare channels: {str(e)}"}), 400

@app.route('/campaigns/by-channel/<channel_name>', methods=['GET'])
def get_campaigns_by_channel(channel_name):
    """Get all campaigns for a specific channel."""
    try:
        campaigns = Campaign.query.filter_by(channel=channel_name).all()
        
        if not campaigns:
            return jsonify({"error": f"No campaigns found for channel: {channel_name}"}), 404
        
        return jsonify({
            "success": True,
            "channel": channel_name,
            "campaigns": [c.to_dict() for c in campaigns]
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch campaigns by channel: {str(e)}"}), 400

@app.route('/dashboard/analytics', methods=['GET'])
def dashboard_analytics():
    """Get aggregated analytics for charts and recommendations."""
    try:
        campaigns = Campaign.query.all()
        if not campaigns:
            return jsonify({"success": True, "data": None})
            
        df = pd.DataFrame([c.to_dict() for c in campaigns])
        
        # 1. Channel Performance (ROI, CAC, Conversion Rate)
        channel_perf = df.groupby('channel').agg({
            'roi': 'mean',
            'cac': 'mean',
            'conversion_rate': 'mean',
            'revenue': 'sum'
        }).reset_index()
        
        # 2. Revenue Share
        revenue_share = df.groupby('channel')['revenue'].sum().reset_index()
        
        # 3. Variant Analysis (A/B)
        # Group by variant name to see global performance of "A" vs "B" vs "Control"
        variant_perf = df.groupby('test_variant').agg({
            'conversion_rate': 'mean',
            'ctr': 'mean'
        }).reset_index()
        
        # 4. Top Campaigns
        top_campaigns = df.nlargest(10, 'roi')[['name', 'roi', 'revenue', 'channel']].to_dict('records')
        
        # 5. Recommendations
        recommendations = generate_automated_recommendations(campaigns)
        
        return jsonify({
            "success": True,
            "charts": {
                "channel_roi": {
                    "labels": channel_perf['channel'].tolist(),
                    "data": channel_perf['roi'].round(2).tolist()
                },
                "channel_cac": {
                    "labels": channel_perf['channel'].tolist(),
                    "data": channel_perf['cac'].round(2).tolist()
                },
                "revenue_share": {
                    "labels": revenue_share['channel'].tolist(),
                    "data": revenue_share['revenue'].round(2).tolist()
                },
                "variant_comparison": {
                    "labels": variant_perf['test_variant'].tolist(),
                    "data": variant_perf['conversion_rate'].round(2).tolist()
                }
            },
            "top_campaigns": top_campaigns,
            "recommendations": recommendations
        })
    except Exception as e:
        return jsonify({"error": f"Failed to generate analytics: {str(e)}"}), 400

# -------------------------------------------------------------------------
# ADMIN / MAINTENANCE ROUTES
# -------------------------------------------------------------------------
@app.route('/admin/reset-db', methods=['POST'])
def reset_database():
    """Reset the entire database to its initial state with sample data.
    This is useful when getting the prototype up and running for the
    first time or when you want to clear all stored campaigns.
    NOTE: In a production system this endpoint should be secured.
    """
    try:
        # Close any existing sessions to prevent locking issues
        db.session.remove()
        
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()

        # Re-populate with sample data
        add_sample_data()

        return jsonify({"success": True, "message": "Database has been reset to its initial state."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    # ensure frontend directory exists before starting server
    if not os.path.exists('frontend'):
        app.logger.error("Error: 'frontend' directory not found. Please check your project structure.")
    else:
        # run without debug by default for prototype stability
        app.run(debug=False, port=5000)

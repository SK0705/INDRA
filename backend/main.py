import threading
import time
import random
import uuid
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.analytics import CampaignAnalytics

app = Flask(__name__, 
            static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend'),
            static_url_path='')
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

analytics_engine = CampaignAnalytics()

# In-memory storage for user data
current_data = []

@app.route('/upload_campaign_data', methods=['POST'])
def upload_campaign_data():
    """Allow manual uploading of campaign data."""
    data = request.json
    if not isinstance(data, list):
        data = [data]
        
    current_data.extend(data)
    if len(current_data) > 1000:
        del current_data[:-1000]
        
    df = pd.DataFrame(data)
    analytics_engine.update_history(df)
    return jsonify({"status": "success", "records_added": len(data)})

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    """Handle bulk CSV uploads for campaign analysis."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    
    if file and file.filename.endswith('.csv'):
        try:
            df = pd.read_csv(file)
            
            # Normalize column names (handle case-insensitive, spaces to underscores)
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            # Required columns validation
            required_cols = ['campaign_name', 'channel', 'impressions', 'clicks', 'conversions', 'cost', 'revenue']
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                return jsonify({"status": "error", "message": f"Missing columns: {', '.join(missing)}"}), 400
            
            # Convert NaN to appropriate defaults
            df = df.fillna({
                'impressions': 0, 'clicks': 0, 'conversions': 0, 
                'cost': 0.0, 'revenue': 0.0, 'variant': 'None'
            })
            
            # Additional cleanup/formatting
            if 'campaign_id' not in df.columns:
                df['campaign_id'] = [f"CSV-{uuid.uuid4().hex[:6].upper()}" for _ in range(len(df))]
            if 'variant' not in df.columns:
                df['variant'] = 'None'
                
            data_list = df.to_dict(orient='records')
            
            current_data.extend(data_list)
            if len(current_data) > 1000:
                del current_data[:-1000]
            
            analytics_engine.update_history(df)
            
            return jsonify({
                "status": "success", 
                "records_added": len(data_list),
                "message": f"Successfully processed {len(data_list)} records."
            })
            
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
            
    return jsonify({"status": "error", "message": "Invalid file format. Please upload a CSV."}), 400

@app.route('/analytics_metrics', methods=['GET'])
def get_analytics_metrics():
    if not current_data:
        return jsonify({"metrics": {}})
    df = pd.DataFrame(current_data)
    
    total_impressions = int(df['impressions'].sum())
    total_clicks = int(df['clicks'].sum())
    total_conversions = int(df['conversions'].sum())
    total_cost = float(df['cost'].sum())
    total_revenue = float(df['revenue'].sum())
    
    overall_ctr = total_clicks / max(total_impressions, 1)
    overall_conv_rate = total_conversions / max(total_clicks, 1)
    overall_cac = total_cost / max(total_conversions, 1)
    overall_roi = (total_revenue - total_cost) / max(total_cost, 0.01)
    
    # metrics by channel
    channel_groups = df.groupby('channel').agg({
        'cost': 'sum',
        'revenue': 'sum'
    }).reset_index()
    channel_groups['roi'] = (channel_groups['revenue'] - channel_groups['cost']) / np.maximum(channel_groups['cost'], 0.01)
    
    return jsonify({
        "aggregate": {
            "campaigns": len(df),
            "impressions": total_impressions,
            "clicks": total_clicks,
            "conversions": total_conversions,
            "cost": total_cost,
            "revenue": total_revenue,
            "profit": total_revenue - total_cost,
            "ctr": float(overall_ctr),
            "conversion_rate": float(overall_conv_rate),
            "cac": float(overall_cac),
            "roi": float(overall_roi)
        },
        "channels": channel_groups.to_dict(orient='records'),
        "recent": df.tail(5).to_dict(orient='records')
    })

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(current_data)

@app.route('/delete_history/<campaign_id>', methods=['GET'])
def delete_history(campaign_id):
    """Delete a specific campaign record."""
    global current_data
    # Remove from in-memory list
    current_data = [item for item in current_data if item.get('campaign_id') != campaign_id]
    
    # Remove from analytics engine
    analytics_engine.delete_record(campaign_id)
    
    return jsonify({"status": "success", "message": f"Record {campaign_id} deleted."})

@app.route('/charts', methods=['GET'])
def get_charts():
    if not current_data:
        return jsonify({})
        
    df = pd.DataFrame(current_data)
    df['roi'] = (df['revenue'] - df['cost']) / np.maximum(df['cost'], 0.01)
    df['cac'] = df['cost'] / np.maximum(df['conversions'], 1)
    
    grouped = df.groupby(['channel']).agg({
        'roi': 'mean',
        'cac': 'mean'
    }).reset_index()
    
    # Matplotlib Configuration for dark theme
    plt.style.use('dark_background')
    matplotlib.rcParams['axes.facecolor'] = '#0a1423'
    matplotlib.rcParams['figure.facecolor'] = '#0a1423'
    matplotlib.rcParams['text.color'] = '#00e5ff'
    matplotlib.rcParams['axes.labelcolor'] = '#00e5ff'
    matplotlib.rcParams['xtick.color'] = '#8ab4f8'
    matplotlib.rcParams['ytick.color'] = '#8ab4f8'
    matplotlib.rcParams['axes.edgecolor'] = '#00e5ff'
    
    # 1. ROI Chart
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    sns.barplot(data=grouped, x='channel', y='roi', ax=ax1, color='#00e5ff', alpha=0.8)
    ax1.set_title('Average ROI by Channel')
    ax1.set_xlabel('')
    ax1.set_ylabel('ROI (x)')
    plt.tight_layout()
    
    buf1 = io.BytesIO()
    fig1.savefig(buf1, format='png', transparent=True)
    buf1.seek(0)
    roi_b64 = base64.b64encode(buf1.read()).decode('utf-8')
    plt.close(fig1)
    
    # 2. CAC Chart
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    sns.lineplot(data=grouped, x='channel', y='cac', ax=ax2, color='#ff1744', marker='o', linewidth=2)
    ax2.set_title('Average CAC by Channel')
    ax2.set_xlabel('')
    ax2.set_ylabel('CAC (₹)')
    plt.tight_layout()
    
    buf2 = io.BytesIO()
    fig2.savefig(buf2, format='png', transparent=True)
    buf2.seek(0)
    cac_b64 = base64.b64encode(buf2.read()).decode('utf-8')
    plt.close(fig2)
    
    return jsonify({
        "roi_chart": f"data:image/png;base64,{roi_b64}",
        "cac_chart": f"data:image/png;base64,{cac_b64}"
    })

@app.route('/campaign_charts/<campaign_id>', methods=['GET'])
def get_campaign_charts(campaign_id):
    """Generate Matplotlib charts for a specific campaign comparison."""
    if not current_data:
        return jsonify({})
        
    df = pd.DataFrame(current_data)
    campaign = df[df['campaign_id'] == campaign_id]
    
    if campaign.empty:
        return jsonify({"error": "Campaign not found"}), 404
        
    campaign = campaign.iloc[0]
    channel_data = df[df['channel'] == campaign['channel']]
    
    # Calculate averages for comparison
    avg_roi = ((channel_data['revenue'] - channel_data['cost']) / np.maximum(channel_data['cost'], 0.01)).mean()
    camp_roi = (campaign['revenue'] - campaign['cost']) / max(campaign['cost'], 0.01)
    
    avg_conv = (channel_data['conversions'] / np.maximum(channel_data['clicks'], 1)).mean()
    camp_conv = campaign['conversions'] / max(campaign['clicks'], 1)
    
    # Matplotlib Configuration
    plt.style.use('dark_background')
    matplotlib.rcParams['axes.facecolor'] = '#0a1423'
    matplotlib.rcParams['figure.facecolor'] = '#0a1423'
    matplotlib.rcParams['text.color'] = '#00e5ff'
    
    # Create Comparison Chart
    fig, ax = plt.subplots(figsize=(7, 4))
    metrics = ['ROI', 'Conversion Rate']
    camp_vals = [camp_roi, camp_conv * 10] # Scale conv for visibility
    chan_vals = [avg_roi, avg_conv * 10]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    ax.bar(x - width/2, camp_vals, width, label='Current Campaign', color='#00e5ff', alpha=0.8)
    ax.bar(x + width/2, chan_vals, width, label='Channel Avg', color='#8ab4f8', alpha=0.5)
    
    ax.set_title(f'Performance Comparison: {campaign["campaign_name"]}')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.legend()
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', transparent=True)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    
    return jsonify({
        "comparison_chart": f"data:image/png;base64,{img_b64}"
    })

@app.route('/ab_test', methods=['POST'])
def run_ab_test():
    """Run an A/B test on two variant data dicts."""
    data = request.json
    if not data or 'variant_a' not in data or 'variant_b' not in data:
        return jsonify({"status": "error", "message": "Please provide variant_a and variant_b data."}), 400
    
    result = analytics_engine.ab_test(data['variant_a'], data['variant_b'])
    return jsonify(result)

@app.route('/ai_recommendations', methods=['GET'])
def get_ai_recommendations():
    if not current_data:
        return jsonify({"recommendations": ["Awaiting initial data stream..."]})
        
    df = pd.DataFrame(current_data)
    recs = analytics_engine.generate_recommendations(df)
        
    return jsonify({"recommendations": recs})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True, use_reloader=False)

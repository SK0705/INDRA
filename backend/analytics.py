import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
import warnings

warnings.filterwarnings('ignore')

class CampaignAnalytics:
    def __init__(self):
        self.historical_data = pd.DataFrame(columns=[
            'campaign_id', 'channel', 'impressions', 'clicks', 
            'conversions', 'cost', 'revenue', 'variant'
        ])
        self.roi_model = LinearRegression()
        self.model_trained = False

    def calculate_metrics(self, data: pd.DataFrame) -> dict:
        """Calculate CTR, Conversion Rate, CAC, and ROI for the given data."""
        metrics = {}
        for _, row in data.iterrows():
            clicks = max(row['clicks'], 1)
            impressions = max(row['impressions'], 1)
            conversions = max(row['conversions'], 1)
            cost = max(row['cost'], 0.01)
            revenue = row['revenue']
            
            ctr = clicks / impressions
            conv_rate = conversions / clicks
            cac = cost / conversions
            roi = (revenue - cost) / cost
            
            metrics[row['campaign_id']] = {
                'ctr': ctr,
                'conversion_rate': conv_rate,
                'cac': cac,
                'roi': roi,
                'channel': row['channel'],
                'variant': row['variant']
            }
        return metrics

    def update_history(self, new_data: pd.DataFrame):
        self.historical_data = pd.concat([self.historical_data, new_data], ignore_index=True)
        self._train_model()

    def delete_record(self, campaign_id: str):
        """Remove a record by campaign_id and retrain the model."""
        self.historical_data = self.historical_data[self.historical_data['campaign_id'] != campaign_id]
        self._train_model()

    def _train_model(self):
        """Train a simple model to predict ROI based on cost, clicks, and conversions."""
        if len(self.historical_data) > 10:
            df = self.historical_data.copy()
            df['roi'] = (df['revenue'] - df['cost']) / np.maximum(df['cost'], 0.01)
            
            X = df[['cost', 'clicks', 'conversions']]
            y = df['roi']
            
            try:
                self.roi_model.fit(X, y)
                self.model_trained = True
            except Exception as e:
                print(f"Model training failed: {e}")

    def predict_roi(self, cost: float, clicks: int, conversions: int) -> float:
        if not self.model_trained:
            return 0.0
        prediction = self.roi_model.predict(np.array([[cost, clicks, conversions]]))
        return prediction[0]

    def ab_test(self, variant_a: dict, variant_b: dict) -> dict:
        """
        Perform A/B testing on direct single-variant data dicts.
        Computes conversion rate, CTR, ROI, and CAC for each variant,
        then determines the winner based on a weighted composite score.
        Also performs a chi-square test on conversions/clicks for statistical significance.
        """
        def safe_div(a, b, default=0.0):
            return a / b if b and b > 0 else default

        # Metrics for Variant A
        a_clicks = max(float(variant_a.get('clicks', 0)), 1)
        a_impr = max(float(variant_a.get('impressions', 0)), 1)
        a_conv = float(variant_a.get('conversions', 0))
        a_cost = max(float(variant_a.get('cost', 0)), 0.01)
        a_rev = float(variant_a.get('revenue', 0))

        a_conv_rate = safe_div(a_conv, a_clicks)
        a_ctr = safe_div(a_clicks, a_impr)
        a_roi = safe_div(a_rev - a_cost, a_cost)
        a_cac = safe_div(a_cost, max(a_conv, 1))

        # Metrics for Variant B
        b_clicks = max(float(variant_b.get('clicks', 0)), 1)
        b_impr = max(float(variant_b.get('impressions', 0)), 1)
        b_conv = float(variant_b.get('conversions', 0))
        b_cost = max(float(variant_b.get('cost', 0)), 0.01)
        b_rev = float(variant_b.get('revenue', 0))

        b_conv_rate = safe_div(b_conv, b_clicks)
        b_ctr = safe_div(b_clicks, b_impr)
        b_roi = safe_div(b_rev - b_cost, b_cost)
        b_cac = safe_div(b_cost, max(b_conv, 1))

        # Composite score: conversion rate (50%) + ROI (30%) + CTR (20%)
        # Normalize ROI (can be negative)
        max_roi = max(abs(a_roi), abs(b_roi), 0.01)
        a_score = (a_conv_rate * 0.5) + ((a_roi / max_roi) * 0.3) + (a_ctr * 0.2)
        b_score = (b_conv_rate * 0.5) + ((b_roi / max_roi) * 0.3) + (b_ctr * 0.2)

        # Chi-square test for significance on conversion rates
        try:
            obs_a = [a_conv, max(a_clicks - a_conv, 0)]
            obs_b = [b_conv, max(b_clicks - b_conv, 0)]
            chi2, p_value = stats.chi2_contingency([obs_a, obs_b])[:2]
            if pd.isna(p_value):
                p_value = 1.0
        except Exception:
            chi2, p_value = 0.0, 1.0

        significant = bool(p_value <= 0.05)
        
        if abs(a_score - b_score) < 0.001:
            better_variant = "Tie"
        elif a_score > b_score:
            better_variant = "A"
        else:
            better_variant = "B"

        if not significant:
            verdict = "Inconclusive (not statistically significant)"
        else:
            verdict = f"Variant {better_variant} wins"

        return {
            "status": "success",
            "better_variant": better_variant,
            "verdict": verdict,
            "significant": significant,
            "p_value": float(p_value),
            "chi2": float(chi2) if not pd.isna(chi2) else 0.0,
            "variant_a": {
                "conversion_rate": round(a_conv_rate * 100, 2),
                "ctr": round(a_ctr * 100, 2),
                "roi": round(a_roi * 100, 2),
                "cac": round(a_cac, 2),
                "score": round(a_score, 4)
            },
            "variant_b": {
                "conversion_rate": round(b_conv_rate * 100, 2),
                "ctr": round(b_ctr * 100, 2),
                "roi": round(b_roi * 100, 2),
                "cac": round(b_cac, 2),
                "score": round(b_score, 4)
            }
        }

    def channel_comparison(self, data: pd.DataFrame) -> dict:
        """Compare channels by ROI."""
        if data.empty:
            return {}
            
        data['roi'] = (data['revenue'] - data['cost']) / np.maximum(data['cost'], 0.01)
        channel_roi = data.groupby('channel')['roi'].mean().to_dict()
        
        best_channel = max(channel_roi, key=channel_roi.get) if channel_roi else "N/A"
        
        return {
            "channel_performance": channel_roi,
            "best_channel": best_channel
        }

    def generate_recommendations(self, data: pd.DataFrame) -> list:
        """Generate AI recommendations based on current data."""
        if data.empty:
            return ["Need more data to generate recommendations."]
            
        recs = []
        data['roi'] = (data['revenue'] - data['cost']) / np.maximum(data['cost'], 0.01)
        channel_roi = data.groupby('channel')['roi'].mean()
        
        for channel, roi in channel_roi.items():
            if roi > 0.5:
                recs.append(f"High ROI on {channel} ({roi:.2f}). Consider increasing budget.")
            elif roi < 0:
                recs.append(f"Negative ROI on {channel} ({roi:.2f}). Reduce spending or optimize.")
                
        if not recs:
            recs.append("Campaigns are performing adequately. Continue monitoring.")
            
        return recs

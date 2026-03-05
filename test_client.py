import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.main import app
import traceback

try:
    with app.test_client() as client:
        # Mock some data so /charts doesn't return empty dict
        client.post('/upload_campaign_data', json={
            "campaign_id": "TEST",
            "campaign_name": "Test",
            "channel": "Direct",
            "impressions": 100,
            "clicks": 10,
            "conversions": 1,
            "cost": 10.0,
            "revenue": 50.0,
            "variant": "None"
        })
        response = client.get('/charts')
        print("Status:", response.status_code)
        if response.status_code == 500:
            print("Response:", response.data.decode())
except Exception as e:
    traceback.print_exc()

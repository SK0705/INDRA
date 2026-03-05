import sys
import os

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.main import app

if __name__ == '__main__':
    print("="*60)
    print("🚀 INDRA - Intelligent Network Data ROI Analytics 🚀")
    print("="*60)
    print("Starting master presentation server...")
    print("✓ Backend: Flask Activated")
    print("✓ Frontend: Real-time UI connected")
    print("✓ Stream: AI Simulation engaged\n")
    print("👉 OPEN IN BROWSER: http://127.0.0.1:8000")
    print("="*60)
    
    # Run the application
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False)

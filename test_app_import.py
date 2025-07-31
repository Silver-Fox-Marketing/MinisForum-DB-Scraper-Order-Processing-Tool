"""
Test the app import and basic functionality
"""
import sys
from pathlib import Path

# Add web_gui to path
web_gui_dir = Path(__file__).parent / "web_gui"
sys.path.insert(0, str(web_gui_dir))

try:
    print("Testing app import...")
    from app import app
    print("[SUCCESS] App imported successfully")
    
    # Test basic route
    print("Testing basic route...")
    with app.test_client() as client:
        response = client.get('/')
        print(f"Index route status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.data.decode()[:500]}")
        else:
            print("[SUCCESS] Basic route working")
            
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
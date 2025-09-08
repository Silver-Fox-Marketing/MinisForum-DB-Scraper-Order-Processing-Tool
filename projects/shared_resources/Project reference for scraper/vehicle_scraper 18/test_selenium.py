#!/usr/bin/env python3
"""
Simple test script to check if selenium and undetected_chromedriver work
"""

import sys
import traceback

def test_selenium():
    try:
        print("Testing selenium setup...")
        
        print("1. Importing undetected_chromedriver...")
        import undetected_chromedriver as uc
        print("   ✓ Import successful")
        
        print("2. Creating Chrome options...")
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        print("   ✓ Options created")
        
        print("3. Creating Chrome driver...")
        driver = uc.Chrome(options=options)
        print("   ✓ Driver created successfully")
        
        print("4. Testing navigation to Google...")
        driver.get("https://www.google.com")
        print("   ✓ Navigation successful")
        
        print("5. Getting page title...")
        title = driver.title
        print(f"   ✓ Page title: {title}")
        
        print("6. Closing driver...")
        driver.quit()
        print("   ✓ Driver closed successfully")
        
        print("\n✅ All tests passed! Selenium is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_selenium()
    sys.exit(0 if success else 1)
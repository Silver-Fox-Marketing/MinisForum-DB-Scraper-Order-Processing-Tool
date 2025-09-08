#!/usr/bin/env python3
"""
Debug Chrome/Selenium issues step by step
"""

import sys
import time

def test_step_by_step():
    try:
        print("=== CHROME/SELENIUM DEBUG TEST ===")
        
        # Test 1: Basic imports
        print("\nSTEP 1: Testing imports...")
        try:
            import undetected_chromedriver as uc
            from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
            print("✓ Imports successful")
        except Exception as e:
            print(f"✗ Import failed: {e}")
            return False
        
        # Test 2: Check Chrome installation
        print("\nSTEP 2: Checking Chrome installation...")
        try:
            import subprocess
            result = subprocess.run(['chrome', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                # Try alternative command
                result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
            print(f"✓ Chrome version: {result.stdout.strip()}")
        except Exception as e:
            print(f"✗ Chrome check failed: {e}")
            print("Chrome might not be in PATH, but that's okay for undetected_chromedriver")
        
        # Test 3: Create driver with minimal options
        print("\nSTEP 3: Creating Chrome driver (minimal setup)...")
        try:
            print("Creating driver with no options...")
            driver = uc.Chrome()
            print("✓ Driver created successfully")
            
            print("Checking if driver is alive...")
            print(f"Driver session ID: {driver.session_id}")
            print("✓ Driver is alive")
            
            # Test 4: Simple navigation
            print("\nSTEP 4: Testing navigation...")
            print("Navigating to data:text/html,<h1>Test</h1>...")
            driver.get("data:text/html,<h1>Test Page</h1><p>If you see this, navigation works!</p>")
            print("✓ Navigation successful")
            
            print("Waiting 2 seconds...")
            time.sleep(2)
            
            print("Getting page title...")
            title = driver.title
            print(f"✓ Page title: '{title}'")
            
            print("Getting page source length...")
            source_len = len(driver.page_source)
            print(f"✓ Page source length: {source_len} characters")
            
            # Test 5: Cleanup
            print("\nSTEP 5: Cleanup...")
            driver.quit()
            print("✓ Driver closed successfully")
            
            print("\n✅ ALL TESTS PASSED - Selenium is working!")
            return True
            
        except Exception as e:
            print(f"✗ Driver creation/operation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Chrome/Selenium debug test...")
    print("This test will create a Chrome window - DO NOT CLOSE IT MANUALLY")
    print("Let the script handle opening and closing Chrome\n")
    
    input("Press Enter to start the test...")
    
    success = test_step_by_step()
    
    if success:
        print("\n🎉 Your selenium setup is working correctly!")
        print("The issue might be with the specific website or scraper logic.")
    else:
        print("\n💥 There's an issue with your Chrome/Selenium setup.")
        print("Common solutions:")
        print("1. Update Chrome browser to latest version")
        print("2. pip install --upgrade undetected-chromedriver")
        print("3. pip install --upgrade selenium")
        print("4. Restart your computer")
    
    input("\nPress Enter to exit...")
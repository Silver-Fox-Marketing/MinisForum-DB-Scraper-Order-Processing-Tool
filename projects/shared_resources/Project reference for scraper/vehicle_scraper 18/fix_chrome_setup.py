#!/usr/bin/env python3
"""
Fix Chrome/ChromeDriver setup issues
"""

import subprocess
import sys
import os

def fix_chrome_setup():
    print("=== CHROME SETUP FIXER ===\n")
    
    # Step 1: Check Python and pip
    print("1. Checking Python setup...")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Step 2: Update/install required packages
    print("\n2. Updating selenium and undetected-chromedriver...")
    
    packages_to_update = [
        "selenium",
        "undetected-chromedriver",
        "beautifulsoup4",
        "requests"
    ]
    
    for package in packages_to_update:
        print(f"\nUpdating {package}...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", package
            ], capture_output=True, text=True, check=True)
            print(f"✓ {package} updated successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to update {package}: {e}")
            print(f"Output: {e.stdout}")
            print(f"Error: {e.stderr}")
    
    # Step 3: Check Chrome installation
    print("\n3. Checking Chrome browser...")
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe")
    ]
    
    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✓ Chrome found at: {path}")
            chrome_found = True
            break
    
    if not chrome_found:
        print("✗ Chrome browser not found in common locations")
        print("Please install Chrome from: https://www.google.com/chrome/")
        return False
    
    # Step 4: Test basic imports
    print("\n4. Testing imports...")
    try:
        import undetected_chromedriver as uc
        print(f"✓ undetected_chromedriver version: {uc.__version__}")
    except Exception as e:
        print(f"✗ Failed to import undetected_chromedriver: {e}")
        return False
    
    try:
        import selenium
        print(f"✓ selenium version: {selenium.__version__}")
    except Exception as e:
        print(f"✗ Failed to import selenium: {e}")
        return False
    
    # Step 5: Test driver creation with different methods
    print("\n5. Testing Chrome driver creation...")
    
    test_methods = [
        ("Method 1: Default undetected_chromedriver", lambda: uc.Chrome()),
        ("Method 2: With headless option", lambda: uc.Chrome(headless=True)),
        ("Method 3: With custom options", lambda: create_chrome_with_options()),
    ]
    
    for method_name, method_func in test_methods:
        print(f"\nTrying {method_name}...")
        try:
            driver = method_func()
            print("✓ Driver created successfully")
            print("Testing navigation...")
            driver.get("data:text/html,<h1>Test</h1>")
            print("✓ Navigation successful")
            driver.quit()
            print("✓ Driver closed successfully")
            print(f"🎉 SUCCESS: {method_name} works!")
            return True
        except Exception as e:
            print(f"✗ {method_name} failed: {e}")
            continue
    
    print("\n💥 All methods failed. Chrome/ChromeDriver setup needs manual fixing.")
    return False

def create_chrome_with_options():
    import undetected_chromedriver as uc
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    return uc.Chrome(options=options)

if __name__ == "__main__":
    print("This script will try to fix your Chrome/Selenium setup")
    input("Press Enter to continue...")
    
    success = fix_chrome_setup()
    
    if success:
        print("\n✅ Chrome setup is now working!")
        print("You can now try running your scraper again.")
    else:
        print("\n❌ Could not fix Chrome setup automatically.")
        print("\nManual steps to try:")
        print("1. Uninstall and reinstall Google Chrome")
        print("2. Run: pip uninstall selenium undetected-chromedriver")
        print("3. Run: pip install selenium==4.15.0 undetected-chromedriver")
        print("4. Restart your computer")
        print("5. Try running this script again")
    
    input("\nPress Enter to exit...")
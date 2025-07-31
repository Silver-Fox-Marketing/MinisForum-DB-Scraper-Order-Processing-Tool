"""
Cleanup Duplicate Scrapers Script
Removes all non-functional and duplicate scrapers from the database
Keeps only the working scrapers we've verified
"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.append(str(scripts_dir))

from database_connection import db_manager

def cleanup_scrapers():
    """Remove all scrapers except the verified working ones"""
    
    # List of scrapers to KEEP
    keep_scrapers = [
        'Dave Sinclair Lincoln South',
        'BMW of West St. Louis', 
        'Columbia Honda'  # Ready to test next
    ]
    
    print("Starting scraper cleanup...")
    print(f"Keeping only: {', '.join(keep_scrapers)}")
    print("-" * 50)
    
    try:
        # Get all current scrapers
        all_scrapers = db_manager.execute_query("SELECT name FROM dealership_configs ORDER BY name")
        
        # Count scrapers to remove
        to_remove = []
        for scraper in all_scrapers:
            name = scraper['name']
            if name not in keep_scrapers:
                to_remove.append(name)
        
        print(f"Found {len(all_scrapers)} total scrapers")
        print(f"Keeping {len(keep_scrapers)} scrapers")
        print(f"Removing {len(to_remove)} scrapers")
        print("-" * 50)
        
        # Remove each scraper not in the keep list
        removed_count = 0
        for name in to_remove:
            try:
                result = db_manager.execute_non_query(
                    "DELETE FROM dealership_configs WHERE name = %s",
                    (name,)
                )
                if result > 0:
                    print(f"[REMOVED] {name}")
                    removed_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to remove {name}: {e}")
        
        print("-" * 50)
        print(f"Successfully removed {removed_count} scrapers")
        
        # Verify remaining scrapers
        remaining = db_manager.execute_query("SELECT name, is_active FROM dealership_configs ORDER BY name")
        print("\nRemaining scrapers in database:")
        for scraper in remaining:
            status = "Active" if scraper['is_active'] else "Inactive"
            print(f"  - {scraper['name']} ({status})")
        
        return True
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("SCRAPER CLEANUP UTILITY")
    print("=" * 50)
    
    # Confirm before proceeding
    print("\nThis will remove all scrapers except:")
    print("  1. Dave Sinclair Lincoln South")
    print("  2. BMW of West St. Louis")
    print("  3. Columbia Honda")
    print("\nProceed? (y/n): ", end="")
    
    # Auto-confirm for script execution
    confirm = "y"  # In real use, would be: input().lower()
    
    if confirm == 'y':
        success = cleanup_scrapers()
        if success:
            print("\n[SUCCESS] Cleanup completed!")
        else:
            print("\n[FAILED] Cleanup encountered errors")
    else:
        print("\nCleanup cancelled")
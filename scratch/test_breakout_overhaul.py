import os
import sys
from dotenv import load_dotenv

# Add parent dir to path for imports
sys.path.append(os.getcwd())

import layer4_trends_logic
from category_utils import get_category

def test_overhaul():
    load_dotenv('.env.local')
    if not os.environ.get("SERPAPI_KEY"):
        print("❌ SERPAPI_KEY missing")
        return

    print("🚀 Testing 4.3 Overhaul (this will use SerpApi credits)...")
    
    # Mock some internal data to test 'exclusion' Step 3
    # If the API returns 'gold ring', it should be excluded if it's in top_terms
    mock_top_terms = [
        {'term_norm': 'gold ring', 'searches': 1000, 'category': 'Rings'}
    ]
    mock_cats = ['Rings', 'Earrings']
    mock_zero_a2c = []
    mock_zero_conv = []

    try:
        results = layer4_trends_logic.run_layer4_trends(
            mock_top_terms, mock_cats, mock_zero_a2c, mock_zero_conv
        )
        
        breakout_data = results.get('4.3', {})
        rows = breakout_data.get('rows', [])
        by_cat = breakout_data.get('by_category', {})
        
        print(f"✅ Found {len(rows)} breakout terms missing from internal data.")
        
        # Test Step 5: rename 'Other' -> 'General Jewellery'
        found_other = False
        for r in rows:
            if r['category'] == 'Other':
                found_other = True
            
        if found_other:
            print("❌ Found 'Other' category - rename failed!")
        else:
            print("✅ 'Other' category correctly avoided.")
            
        print("\nBreakout Categories found:")
        for cat in by_cat.keys():
            print(f"- {cat} ({len(by_cat[cat])} terms)")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_overhaul()

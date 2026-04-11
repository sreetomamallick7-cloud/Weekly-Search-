import io
import pandas as pd
import sys
import os
sys.path.append(os.getcwd())
try:
    from app import safe_read_csv
except ImportError:
    # If running from scratch/ folder
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app import safe_read_csv

# Mock FileStorage-like object
class MockFile:
    def __init__(self, content):
        self.content = content
    def read(self):
        return self.content

def test_safe_read_csv():
    print("🚀 Testing in-memory safe_read_csv...")
    
    # Test 1: Simple CSV with header at row 0
    csv_1 = b"query,searches\ngold ring,100\ndiamond necklace,50"
    df1 = safe_read_csv(MockFile(csv_1), "test1.csv")
    assert not df1.empty, "DF1 should not be empty"
    assert 'query' in df1.columns, "DF1 should have 'query' column"
    assert len(df1) == 2, "DF1 should have 2 rows"
    print("✅ Test 1 Passed: Simple CSV")

    # Test 2: CSV with metadata rows (typical for GA4/Search Console exports)
    csv_2 = b"Report Name: Search Terms\nDate Range: 2023-01-01 to 2023-03-01\n\nSearch term,Event count\ngold coin,10\nsilver bar,5"
    df2 = safe_read_csv(MockFile(csv_2), "test2.csv")
    assert not df2.empty, "DF2 should not be empty"
    assert 'search_term' in df2.columns, "DF2 should have 'search_term' column (renamed from 'Search term')"
    assert 'a2c_count' in df2.columns, "DF2 should have 'a2c_count' column (renamed from 'Event count')"
    assert len(df2) == 2, "DF2 should have 2 rows"
    print("✅ Test 2 Passed: Metadata skipping")

    # Test 3: Empty file
    df3 = safe_read_csv(MockFile(b""), "empty.csv")
    assert df3.empty, "DF3 should be empty"
    print("✅ Test 3 Passed: Empty file")

    print("\n🎉 All in-memory upload tests passed!")

if __name__ == "__main__":
    test_safe_read_csv()

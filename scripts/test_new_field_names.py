#!/usr/bin/env python3
"""
Test script for the new field naming scheme.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import geopandas as gpd
from scripts.generate_dnbr_utils import load_aoi
from dnbr.generators import generate_dnbr
from dnbr.fire_metadata import create_fire_metadata


def test_new_field_names():
    """Test the new field naming scheme."""
    print("🧪 Testing new field naming scheme...")
    
    try:
        # Load AOI
        aoi_gdf = load_aoi("data/dummy_data/fire.geojson")
        
        # Create fire metadata
        fire_metadata = create_fire_metadata("sa_fire", geojson_path="data/dummy_data/fire.geojson")
        
        # Generate analysis
        analysis = generate_dnbr(
            aoi_gdf, 
            method="dummy", 
            data_path="data/dummy_data/fire.geojson",
            fire_metadata=fire_metadata
        )
        
        # Test raw raster path
        if analysis.raw_raster_path:
            print(f"✅ Raw raster path: {analysis.raw_raster_path}")
        else:
            print("❌ Missing raw raster path")
            return False
        
        # Test published URLs (should be None initially)
        if analysis.published_dnbr_raster_url is None:
            print("✅ Published dNBR raster URL is None (as expected)")
        else:
            print(f"❌ Published dNBR raster URL should be None: {analysis.published_dnbr_raster_url}")
            return False
        
        if analysis.published_vector_url is None:
            print("✅ Published vector URL is None (as expected)")
        else:
            print(f"❌ Published vector URL should be None: {analysis.published_vector_url}")
            return False
        
        # Test JSON serialization
        json_str = analysis.to_json()
        print("✅ JSON serialization works")
        
        # Test JSON deserialization
        analysis_from_json = analysis.from_json(json_str)
        if analysis_from_json.raw_raster_path == analysis.raw_raster_path:
            print("✅ JSON deserialization preserves raw raster path")
        else:
            print("❌ JSON deserialization failed to preserve raw raster path")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_published_urls_simulation():
    """Simulate setting published URLs."""
    print("🧪 Testing published URLs simulation...")
    
    try:
        # Load AOI
        aoi_gdf = load_aoi("data/dummy_data/fire.geojson")
        
        # Create fire metadata
        fire_metadata = create_fire_metadata("sa_fire", geojson_path="data/dummy_data/fire.geojson")
        
        # Generate analysis
        analysis = generate_dnbr(
            aoi_gdf, 
            method="dummy", 
            data_path="data/dummy_data/fire.geojson",
            fire_metadata=fire_metadata
        )
        
        # Simulate publisher setting published URLs
        analysis._published_dnbr_raster_url = "s3://bucket/aoi_id/ulid/dnbr.cog.tif"
        analysis._published_vector_url = "s3://bucket/aoi_id/ulid/aoi.geojson"
        
        # Test published URLs
        if analysis.published_dnbr_raster_url:
            print(f"✅ Published dNBR raster URL: {analysis.published_dnbr_raster_url}")
        else:
            print("❌ Missing published dNBR raster URL")
            return False
        
        if analysis.published_vector_url:
            print(f"✅ Published vector URL: {analysis.published_vector_url}")
        else:
            print("❌ Missing published vector URL")
            return False
        
        # Test JSON serialization with published URLs
        json_str = analysis.to_json()
        print("✅ JSON serialization with published URLs works")
        
        # Test JSON deserialization with published URLs
        analysis_from_json = analysis.from_json(json_str)
        if (analysis_from_json.published_dnbr_raster_url == analysis.published_dnbr_raster_url and
            analysis_from_json.published_vector_url == analysis.published_vector_url):
            print("✅ JSON deserialization preserves published URLs")
        else:
            print("❌ JSON deserialization failed to preserve published URLs")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing New Field Naming Scheme")
    print("=" * 50)
    
    tests = [
        ("New Field Names", test_new_field_names),
        ("Published URLs Simulation", test_published_urls_simulation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

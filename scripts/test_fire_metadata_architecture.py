#!/usr/bin/env python3
"""
Test script for the new FireMetadata architecture.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import geopandas as gpd
from scripts.generate_dnbr_utils import load_aoi
from dnbr.generators import generate_dnbr
from dnbr.fire_metadata import create_fire_metadata, SAFireMetadata


def test_fire_metadata_creation():
    """Test fire metadata creation."""
    print("🧪 Testing fire metadata creation...")
    
    try:
        fire_metadata = create_fire_metadata("sa_fire", geojson_path="data/dummy_data/fire.geojson")
        
        print(f"✅ Provider: {fire_metadata.get_provider()}")
        print(f"✅ Fire ID: {fire_metadata.get_id()}")
        print(f"✅ Fire Date: {fire_metadata.get_date()}")
        
        # Verify the fire ID format
        expected_pattern = r"bushfire_\d{8}"
        import re
        if re.match(expected_pattern, fire_metadata.get_id()):
            print("✅ Fire ID format is correct")
        else:
            print(f"❌ Fire ID format is incorrect: {fire_metadata.get_id()}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Fire metadata creation failed: {e}")
        return False


def test_analysis_with_fire_metadata():
    """Test analysis with fire metadata."""
    print("🧪 Testing analysis with fire metadata...")
    
    try:
        # Load AOI
        aoi_gdf = load_aoi("data/dummy_data/fire.geojson")
        
        # Create fire metadata
        fire_metadata = create_fire_metadata("sa_fire", geojson_path="data/dummy_data/fire.geojson")
        
        # Generate analysis with fire metadata
        analysis = generate_dnbr(
            aoi_gdf, 
            method="dummy", 
            fire_metadata=fire_metadata
        )
        
        # Verify fire metadata was stored
        if analysis.get_aoi_id():
            print(f"✅ Analysis has aoi_id: {analysis.get_aoi_id()}")
        else:
            print("❌ Analysis missing aoi_id")
            return False
        
        if analysis.get_fire_date():
            print(f"✅ Analysis has fire_date: {analysis.get_fire_date()}")
        else:
            print("❌ Analysis missing fire_date")
            return False
        
        if analysis.get_provider():
            print(f"✅ Analysis has provider: {analysis.get_provider()}")
        else:
            print("❌ Analysis missing provider")
            return False
        
        # Check fire metadata object
        if analysis.fire_metadata:
            print(f"✅ Analysis has fire_metadata object: {type(analysis.fire_metadata)}")
        else:
            print("❌ Analysis missing fire_metadata object")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis with fire metadata failed: {e}")
        return False


def test_analysis_without_fire_metadata():
    """Test analysis without fire metadata (should still work)."""
    print("🧪 Testing analysis without fire metadata...")
    
    try:
        # Load AOI
        aoi_gdf = load_aoi("data/dummy_data/fire.geojson")
        
        # Generate analysis without fire metadata
        analysis = generate_dnbr(aoi_gdf, method="dummy")
        
        # Should still work, just without fire metadata
        if analysis.generator_type == "dummy":
            print("✅ Analysis created successfully without fire metadata")
            print(f"✅ Generator type: {analysis.generator_type}")
            print(f"✅ AOI ID: {analysis.get_aoi_id()} (should be None)")
            print(f"✅ Provider: {analysis.get_provider()} (should be None)")
            return True
        else:
            print(f"❌ Analysis has wrong generator type: {analysis.generator_type}")
            return False
        
    except Exception as e:
        print(f"❌ Analysis without fire metadata failed: {e}")
        return False


def test_json_serialization():
    """Test JSON serialization with fire metadata."""
    print("🧪 Testing JSON serialization...")
    
    try:
        # Load AOI
        aoi_gdf = load_aoi("data/dummy_data/fire.geojson")
        
        # Create fire metadata
        fire_metadata = create_fire_metadata("sa_fire", geojson_path="data/dummy_data/fire.geojson")
        
        # Generate analysis with fire metadata
        analysis = generate_dnbr(
            aoi_gdf, 
            method="dummy", 
            fire_metadata=fire_metadata
        )
        
        # Test JSON serialization
        json_str = analysis.to_json()
        print("✅ JSON serialization works")
        
        # Test JSON deserialization
        analysis_from_json = analysis.from_json(json_str)
        if analysis_from_json.get_aoi_id() == analysis.get_aoi_id():
            print("✅ JSON deserialization preserves aoi_id")
        else:
            print("❌ JSON deserialization failed to preserve aoi_id")
            return False
        
        if analysis_from_json.get_provider() == analysis.get_provider():
            print("✅ JSON deserialization preserves provider")
        else:
            print("❌ JSON deserialization failed to preserve provider")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ JSON serialization test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing FireMetadata Architecture")
    print("=" * 50)
    
    tests = [
        ("Fire Metadata Creation", test_fire_metadata_creation),
        ("Analysis with Fire Metadata", test_analysis_with_fire_metadata),
        ("Analysis without Fire Metadata", test_analysis_without_fire_metadata),
        ("JSON Serialization", test_json_serialization),
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

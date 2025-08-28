#!/usr/bin/env python3
"""
Test script for the publisher functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import geopandas as gpd
from scripts.generate_dnbr_utils import load_aoi
from dnbr.generators import generate_dnbr
from dnbr.publisher import extract_fire_metadata, generate_cog_from_file


def test_fire_metadata_extraction():
    """Test fire metadata extraction from GeoJSON."""
    print("🧪 Testing fire metadata extraction...")
    
    try:
        fire_id, fire_date = extract_fire_metadata("data/fire.geojson")
        print(f"✅ Fire ID: {fire_id}")
        print(f"✅ Fire Date: {fire_date}")
        
        # Verify the fire ID format
        expected_pattern = r"bushfire_\d{8}"
        import re
        if re.match(expected_pattern, fire_id):
            print("✅ Fire ID format is correct")
        else:
            print(f"❌ Fire ID format is incorrect: {fire_id}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Fire metadata extraction failed: {e}")
        return False


def test_cog_generation():
    """Test COG generation from existing raster file."""
    print("🧪 Testing COG generation...")
    
    try:
        # Check if the dummy raster file exists
        dummy_raster_path = "data/dummy/fire_severity.tif"
        if not os.path.exists(dummy_raster_path):
            print(f"❌ Dummy raster file not found: {dummy_raster_path}")
            return False
        
        print(f"✅ Found dummy raster file: {dummy_raster_path}")
        
        # Generate COG
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.cog.tif', delete=False) as temp_file:
            cog_path = temp_file.name
        
        try:
            generate_cog_from_file(dummy_raster_path, cog_path)
            
            # Verify COG file was created and has reasonable size
            if os.path.exists(cog_path):
                file_size = os.path.getsize(cog_path)
                print(f"✅ COG generated: {cog_path} ({file_size} bytes)")
                
                # Basic validation that it's a valid GeoTIFF
                import rasterio
                with rasterio.open(cog_path) as src:
                    print(f"✅ COG validation: {src.width}x{src.height}, {src.count} bands")
                    print(f"✅ COG CRS: {src.crs}")
                    print(f"✅ COG bounds: {src.bounds}")
                
                return True
            else:
                print("❌ COG file was not created")
                return False
                
        finally:
            # Clean up
            if os.path.exists(cog_path):
                os.unlink(cog_path)
        
    except Exception as e:
        print(f"❌ COG generation failed: {e}")
        return False


def test_dummy_generator():
    """Test dummy generator returns correct metadata."""
    print("🧪 Testing dummy generator...")
    
    try:
        # Load AOI and generate dummy analysis
        aoi_gdf = load_aoi("data/fire.geojson")
        analysis = generate_dnbr(aoi_gdf, method="dummy")
        
        # Check that the analysis has the expected metadata
        if analysis.generator_type != "dummy":
            print(f"❌ Expected generator_type 'dummy', got '{analysis.generator_type}'")
            return False
        
        if not hasattr(analysis, '_result_path'):
            print("❌ Analysis missing _result_path attribute")
            return False
        
        expected_path = "data/dummy/fire_severity.tif"
        if analysis._result_path != expected_path:
            print(f"❌ Expected _result_path '{expected_path}', got '{analysis._result_path}'")
            return False
        
        print(f"✅ Dummy generator returned correct metadata")
        print(f"✅ Generator type: {analysis.generator_type}")
        print(f"✅ Result path: {analysis._result_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dummy generator test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing Publisher Functionality")
    print("=" * 50)
    
    tests = [
        ("Fire Metadata Extraction", test_fire_metadata_extraction),
        ("Dummy Generator", test_dummy_generator),
        ("COG Generation", test_cog_generation),
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

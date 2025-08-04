#!/usr/bin/env python3
"""
Fire Severity Mapping - AOI Processor (Steel Thread)

This script takes an AOI GeoJSON file and generates a dummy fire severity raster.
This is a minimal implementation to test the end-to-end pipeline.
"""

import sys
import json
import numpy as np
import rasterio
from rasterio.transform import from_bounds
import geopandas as gpd
import folium
from pathlib import Path


def load_aoi(aoi_path):
    """Load the Area of Interest from GeoJSON file."""
    try:
        gdf = gpd.read_file(aoi_path)
        return gdf
    except Exception as e:
        print(f"Error loading AOI file {aoi_path}: {e}")
        sys.exit(1)


def generate_dnbr_raster(aoi_gdf, output_path="outputs/fire_severity.tif"):
    """Generate a dNBR (differenced Normalized Burn Ratio) raster based on the AOI bounds.
    
    Currently generates dummy data for the steel thread implementation.
    Future implementation will calculate actual dNBR from pre/post-fire satellite imagery.
    """
    
    # Get the bounds of the AOI
    bounds = aoi_gdf.total_bounds  # [minx, miny, maxx, maxy]
    
    # Create a dummy raster with some "fire severity" values
    # For now, just create a simple pattern
    width, height = 256, 256
    
    # Create dummy severity values (0-4 scale: 0=unburned, 4=high severity)
    # Create a gradient pattern for visualization
    x_coords = np.linspace(0, 1, width)
    y_coords = np.linspace(0, 1, height)
    X, Y = np.meshgrid(x_coords, y_coords)
    
    # Create a dummy severity pattern (center is "high severity", edges are "low")
    severity = 4 * np.exp(-((X - 0.5)**2 + (Y - 0.5)**2) / 0.1)
    severity = np.clip(severity, 0, 4)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Create the raster file
    transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], width, height)
    
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=severity.dtype,
        crs=aoi_gdf.crs,
        transform=transform,
        nodata=-9999
    ) as dst:
        dst.write(severity, 1)
    
    print(f"Generated dNBR raster: {output_path}")
    return output_path


def create_leaflet_map(aoi_gdf, raster_path, output_path="outputs/fire_severity_map.html"):
    """Create a Leaflet map showing the AOI and the generated raster."""
    
    # Calculate center of AOI
    center_lat = aoi_gdf.geometry.centroid.y.mean()
    center_lon = aoi_gdf.geometry.centroid.x.mean()
    
    # Create the map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    # Add the AOI boundary
    folium.GeoJson(
        aoi_gdf,
        name='Area of Interest',
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'red',
            'weight': 2
        }
    ).add_to(m)
    
    # Add a placeholder for the raster (since we can't directly overlay GeoTIFF in Folium)
    # For now, we'll add a colored rectangle representing the raster bounds
    bounds = aoi_gdf.total_bounds
    folium.Rectangle(
        bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
        color='orange',
        fill=True,
        fillColor='orange',
        fillOpacity=0.3,
        popup='Dummy Fire Severity Raster (Orange overlay)'
    ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Fire Severity Legend</b></p>
    <p><span style="color:green;">Green</span> - Low Severity (0-1)</p>
    <p><span style="color:orange;">Orange</span> - Medium Severity (1-3)</p>
    <p><span style="color:red;">Red</span> - High Severity (3-4)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save the map
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    m.save(output_path)
    print(f"Generated Leaflet map: {output_path}")


def main():
    """Main function to process AOI and generate outputs."""
    if len(sys.argv) != 2:
        print("Usage: python process_aoi.py <aoi_geojson_path>")
        sys.exit(1)
    
    aoi_path = sys.argv[1]
    print(f"Processing AOI: {aoi_path}")
    
    # Load the AOI
    aoi_gdf = load_aoi(aoi_path)
    print(f"Loaded AOI with {len(aoi_gdf)} features")
    
    # Generate dNBR raster
    raster_path = generate_dnbr_raster(aoi_gdf)
    
    # Create Leaflet map
    map_path = create_leaflet_map(aoi_gdf, raster_path)
    
    print("✅ Steel thread pipeline completed successfully!")
    print(f"📊 Raster output: {raster_path}")
    print(f"🗺️  Map output: {map_path}")


if __name__ == "__main__":
    main() 
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
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap


def load_aoi(aoi_path):
    """Load the Area of Interest from GeoJSON file."""
    try:
        gdf = gpd.read_file(aoi_path)
        return gdf
    except Exception as e:
        print(f"Error loading AOI file {aoi_path}: {e}")
        sys.exit(1)


def generate_dnbr_raster(aoi_gdf, output_path="docs/outputs/fire_severity.tif"):
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


def create_raster_overlay(raster_path, output_path="docs/outputs/fire_severity_overlay.png"):
    """Convert the GeoTIFF to a PNG overlay for the map."""
    
    # Read the raster
    with rasterio.open(raster_path) as src:
        data = src.read(1)
        bounds = src.bounds
    
    # Create a custom colormap for fire severity
    colors = ['green', 'yellow', 'orange', 'red']
    n_bins = 4
    cmap = LinearSegmentedColormap.from_list('fire_severity', colors, N=n_bins)
    
    # Normalize data to 0-1 range for colormap
    data_norm = np.clip(data, 0, 4) / 4.0
    
    # Create the image
    fig, ax = plt.subplots(figsize=(10, 10))
    im = ax.imshow(data_norm, cmap=cmap, vmin=0, vmax=1)
    ax.axis('off')
    
    # Save as PNG with transparent background
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0, transparent=True, dpi=150)
    plt.close()
    
    print(f"Generated raster overlay: {output_path}")
    return output_path, bounds


def create_leaflet_map(aoi_gdf, raster_path, output_path="docs/outputs/fire_severity_map.html"):
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
    
    # Generate raster overlay
    overlay_path, raster_bounds = create_raster_overlay(raster_path)
    
    # Add the raster as an image overlay
    folium.raster_layers.ImageOverlay(
        name='Fire Severity (dNBR)',
        image=overlay_path,
        bounds=[[raster_bounds.bottom, raster_bounds.left], 
                [raster_bounds.top, raster_bounds.right]],
        opacity=0.7,
        popup='Fire Severity Raster (dNBR)'
    ).add_to(m)
    
    # Add the AOI boundary on top
    # Drop non-geometry columns to avoid serialization issues
    aoi_geometry = aoi_gdf[['geometry']].copy()
    folium.GeoJson(
        aoi_geometry,
        name='Fire Boundary',
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'red',
            'weight': 3,
            'opacity': 0.8
        },
        popup='Fire Boundary'
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Fire Severity Legend</b></p>
    <p><span style="color:green;">Green</span> - Low Severity (0-1)</p>
    <p><span style="color:yellow;">Yellow</span> - Low-Medium (1-2)</p>
    <p><span style="color:orange;">Orange</span> - Medium-High (2-3)</p>
    <p><span style="color:red;">Red</span> - High Severity (3-4)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save the map
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    m.save(output_path)
    print(f"Generated Leaflet map: {output_path}")
    return output_path


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


# Script entry point moved to __main__.py
# Test trigger Tue Aug  5 10:58:23 ACST 2025

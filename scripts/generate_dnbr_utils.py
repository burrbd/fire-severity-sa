#!/usr/bin/env python3
"""
Fire Severity Mapping - AOI Processor Utilities

This module contains utility functions for AOI processing and map generation.
The actual dNBR generation is handled by the polymorphic analysis system.
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


def load_aoi(aoi_path):
    """Load the Area of Interest from GeoJSON file."""
    try:
        gdf = gpd.read_file(aoi_path)
        return gdf
    except Exception as e:
        print(f"Error loading AOI file {aoi_path}: {e}")
        sys.exit(1)


def create_dnbr_colormap():
    """Create a colormap for dNBR visualization.
    
    Returns:
        matplotlib.colors.LinearSegmentedColormap: Colormap for dNBR values
    """
    # Create a custom colormap: green (unburned) to red (burned)
    colors = ['green', 'yellow', 'orange', 'red']
    return mcolors.LinearSegmentedColormap.from_list('fire_severity', colors)


def create_raster_overlay_image(raster_path, output_path=None):
    """Create a colored overlay image from the dNBR raster.
    
    Args:
        raster_path: Path to the dNBR raster file
        output_path: Output path for the overlay image (if None, will be in same dir as raster)
    
    Returns:
        tuple: (overlay_path, bounds) for use in map creation
    """
    import os
    
    # If no output path specified, place it in the same directory as the raster
    if output_path is None:
        raster_dir = os.path.dirname(raster_path)
        output_path = os.path.join(raster_dir, "fire_severity_overlay.png")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the raster data and bounds
    with rasterio.open(raster_path) as src:
        data = src.read(1)
        bounds = src.bounds
    
    # Normalize data to 0-1 range for visualization
    data_normalized = (data - data.min()) / (data.max() - data.min())
    
    # Get the colormap
    cmap = create_dnbr_colormap()
    
    # Apply colormap to normalized data
    colored_data = cmap(data_normalized)
    
    # Save as PNG
    plt.figure(figsize=(10, 10))
    plt.imshow(colored_data)
    plt.axis('off')
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0, transparent=True, dpi=150)
    plt.close()
    
    print(f"Generated raster overlay image: {output_path}")
    return output_path, bounds


def create_leaflet_map(aoi_gdf, raster_path, output_path="docs/outputs/fire_severity_map.html"):
    """Create a Leaflet map showing the AOI boundary and dNBR raster overlay."""
    
    # Create the map centered on South Australia
    m = folium.Map(
        location=[-34.5, 138.5],  # Center on South Australia
        zoom_start=6,
        tiles='CartoDB positron',
        prefer_canvas=True
    )
    
    # Generate the raster overlay image in the same directory as the raster (ULID folder)
    import os
    raster_dir = os.path.dirname(raster_path)
    output_dir = os.path.dirname(output_path)
    
    # Ensure both directories exist
    os.makedirs(raster_dir, exist_ok=True)  # Ensure ULID directory exists
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists
    
    overlay_filename = "fire_severity_overlay.png"
    overlay_path = os.path.join(raster_dir, overlay_filename)
    
    overlay_path, raster_bounds = create_raster_overlay_image(raster_path, overlay_path)
    
    # Add the raster as an image overlay using the full path for Folium
    image_overlay = folium.raster_layers.ImageOverlay(
        name='Fire Severity (dNBR)',
        image=overlay_path,
        bounds=[[raster_bounds.bottom, raster_bounds.left], 
                [raster_bounds.top, raster_bounds.right]],
        opacity=0.7,
        popup='Fire Severity Raster (dNBR)'
    ).add_to(m)
    
    # Add the AOI boundary with simple styling
    aoi_geometry = aoi_gdf[['geometry']].copy()
    folium.GeoJson(
        aoi_geometry,
        name='Fire Boundary',
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': '#000000',
            'weight': 2,
            'opacity': 0.8
        },
        popup='Fire Boundary'
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl(position='topright').add_to(m)
    
    # Save the map
    m.save(output_path)
    
    # Post-process the HTML to update the base64 image data
    with open(output_path, 'r') as f:
        html_content = f.read()
    
    # Convert the PNG to base64 and update the HTML
    import re
    import base64
    
    # Read the PNG file and convert to base64
    with open(overlay_path, 'rb') as img_file:
        img_data = img_file.read()
        img_base64 = base64.b64encode(img_data).decode('utf-8')
    
    # Replace the existing base64 image data with the new one
    html_content = re.sub(
        r'data:image/png;base64,[^"]*',
        f'data:image/png;base64,{img_base64}',
        html_content
    )
    
    # Write the modified HTML back
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Generated map with dNBR raster overlay: {output_path}")
    return output_path

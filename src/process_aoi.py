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


def load_aoi(aoi_path):
    """Load the Area of Interest from GeoJSON file."""
    try:
        gdf = gpd.read_file(aoi_path)
        return gdf
    except Exception as e:
        print(f"Error loading AOI file {aoi_path}: {e}")
        sys.exit(1)


def calculate_dnbr_values(aoi_gdf, width=50, height=50):
    """Calculate dNBR values based on fire boundary position.
    
    This is a placeholder function that generates dummy dNBR values.
    Replace this with actual dNBR calculation from pre/post-fire satellite imagery.
    
    Args:
        aoi_gdf: GeoDataFrame containing the fire boundary
        width: Raster width in pixels
        height: Raster height in pixels
    
    Returns:
        tuple: (dnbr_values, bounds) where dnbr_values is a 2D numpy array
    """
    # Get the bounds of the AOI
    bounds = aoi_gdf.total_bounds  # [minx, miny, maxx, maxy]
    
    # Create coordinate arrays for the raster
    x_coords = np.linspace(bounds[0], bounds[2], width)
    y_coords = np.linspace(bounds[1], bounds[3], height)
    X, Y = np.meshgrid(x_coords, y_coords)
    
    # Create points from the coordinate grids
    points = gpd.points_from_xy(X.flatten(), Y.flatten(), crs=aoi_gdf.crs)
    points_gdf = gpd.GeoDataFrame(geometry=points)
    
    # Check which points are inside the fire boundary
    inside_fire = points_gdf.within(aoi_gdf.unary_union)
    inside_fire = inside_fire.values.reshape(height, width)
    
    # Create dNBR values based on position
    # Inside fire boundary: random positive values (burned areas)
    # Outside fire boundary: random negative values (unburned areas)
    dnbr_values = np.where(
        inside_fire,
        np.random.uniform(0.1, 2.0, (height, width)),  # Burned: 0.1 to 2.0
        np.random.uniform(-2.0, -0.1, (height, width))  # Unburned: -2.0 to -0.1
    )
    
    return dnbr_values, bounds


def generate_dnbr_raster_tile(dnbr_values, bounds, aoi_gdf, output_path="docs/outputs/fire_severity.tif"):
    """Generate a GeoTIFF raster file from dNBR values.
    
    Args:
        dnbr_values: 2D numpy array of dNBR values
        bounds: Geographic bounds [minx, miny, maxx, maxy]
        aoi_gdf: GeoDataFrame for CRS information
        output_path: Output file path
    
    Returns:
        str: Path to the generated raster file
    """
    height, width = dnbr_values.shape
    
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
        dtype='float32',  # Use float32 for efficiency
        crs=aoi_gdf.crs,
        transform=transform,
        nodata=-9999
    ) as dst:
        dst.write(dnbr_values, 1)
    
    print(f"Generated dNBR raster tile: {output_path}")
    return output_path


def create_dnbr_colormap():
    """Create a colormap for dNBR visualization.
    
    Returns:
        matplotlib.colors.LinearSegmentedColormap: Colormap for dNBR values
    """
    # Create a custom colormap: green (unburned) to red (burned)
    colors = ['green', 'yellow', 'orange', 'red']
    return mcolors.LinearSegmentedColormap.from_list('fire_severity', colors)


def generate_dnbr_raster(aoi_gdf, output_path="docs/outputs/fire_severity.tif"):
    """Generate a dNBR raster based on the AOI bounds.
    
    This function orchestrates the dNBR calculation and raster generation process.
    
    Args:
        aoi_gdf: GeoDataFrame containing the fire boundary
        output_path: Output file path
    
    Returns:
        str: Path to the generated raster file
    """
    # Calculate dNBR values
    dnbr_values, bounds = calculate_dnbr_values(aoi_gdf)
    
    # Generate the raster tile
    raster_path = generate_dnbr_raster_tile(dnbr_values, bounds, aoi_gdf, output_path)
    
    return raster_path


def create_raster_overlay_image(raster_path, output_path="docs/outputs/fire_severity_overlay.png"):
    """Create a colored overlay image from the dNBR raster.
    
    Args:
        raster_path: Path to the dNBR raster file
        output_path: Output path for the overlay image
    
    Returns:
        tuple: (overlay_path, bounds) for use in map creation
    """
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
    
    # Generate the raster overlay image
    overlay_path, raster_bounds = create_raster_overlay_image(raster_path)
    
    # Add the raster as an image overlay
    folium.raster_layers.ImageOverlay(
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
    print(f"Generated map with dNBR raster overlay: {output_path}")
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

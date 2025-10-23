import os
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
import osmnx as ox
import pandas as pd
from typing import Sequence, Union
from PIL import Image
from pyproj import Transformer
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from shapely.geometry import box
import re

# Global Variables
assets  = f"/home/honney/projects/gps-animation/assets"
output  = f"/home/honney/projects/gps-animation/output"
TILE_SIZE = 256

def bbox_to_box(bbox: Sequence[float]) -> box:
    min_lon, min_lat, max_lon, max_lat = bbox
    return box(min_lon, min_lat, max_lon, max_lat)

def save_osm_detail_map(bbox: Sequence[float], filename=f"{output}/detail.png", dpi=300) -> Union[str, os.PathLike]:
    """
    Saves a map image from OpenStreetMap that is precisely cropped to the given bbox.
    """
    # Create a GeoDataFrame from the bounding box, starting in standard lat/lon
    bbox_poly = bbox_to_box(bbox)
    gdf = gpd.GeoDataFrame(
        {"geometry": [bbox_poly]},
        crs="EPSG:4326"
    )

    # Project the GeoDataFrame to Web Mercator (EPSG:3857)
    gdf_mercator = gdf.to_crs(epsg=3857)

    # Get the exact bounds from the projected GeoDataFrame
    minx, miny, maxx, maxy = gdf_mercator.total_bounds

    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 8), dpi=dpi)

    # Set the axes limits to the exact bounding box
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    # Turn off the axis labels, ticks, etc.
    ax.axis("off")
    
    # Add the basemap, which will now conform to the set limits
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=15) # 17 very small stuff

    # Save the figure without any extra padding
    plt.tight_layout(pad=0)
    plt.savefig(filename, dpi=dpi, bbox_inches="tight", pad_inches=0, transparent=True)
    plt.close()

    if os.path.isfile(filename): 
        print(f"Successfully saved map to {filename}")
        return filename
    
def save_satellite_map(bbox: Sequence[float], filename=f"{output}/satellite.png", dpi=300) -> str:
    bbox_poly = bbox_to_box(bbox)

    gdf = gpd.GeoDataFrame(
        {"geometry": [bbox_poly]},
        crs="EPSG:4326"
    ).to_crs(epsg=3857)

    ax = gdf.plot(facecolor="none", edgecolor="none")  # no bbox outline
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    plt.axis("off")
    plt.savefig(filename, dpi=dpi, bbox_inches="tight")
    plt.close()

    if os.path.isfile(filename): return filename
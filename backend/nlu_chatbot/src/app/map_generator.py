"""
Map Generator for Maritime NLU
Generates geopandas and folium maps for vessel visualization
"""
import geopandas as gpd
import folium
from folium import plugins
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import logging
import math

logger = logging.getLogger(__name__)


class MapGenerator:
    """Generate maps for vessel tracking and visualization"""
    
    @staticmethod
    def create_vessel_track_map(
        track_data: List[Dict[str, Any]],
        vessel_name: str,
        center: Optional[Tuple[float, float]] = None,
        zoom_start: int = 10
    ) -> folium.Map:
        """Create a folium map with vessel track"""
        
        if not track_data:
            logger.warning("No track data provided")
            return None
        
        # Extract coordinates
        coords = []
        for point in track_data:
            lat = point.get('LAT')
            lon = point.get('LON')
            if lat is not None and lon is not None:
                coords.append((lat, lon))
        
        if not coords:
            logger.warning("No valid coordinates in track data")
            return None
        
        # Determine center
        if center is None:
            center = (coords[0][0], coords[0][1])
        
        # Create map
        m = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles='OpenStreetMap'
        )
        
        # Add track line
        folium.PolyLine(
            coords,
            color='blue',
            weight=2,
            opacity=0.7,
            popup=f'{vessel_name} Track'
        ).add_to(m)
        
        # Add markers for each point
        for i, (lat, lon) in enumerate(coords):
            point = track_data[i]
            timestamp = point.get('BaseDateTime', 'Unknown')
            sog = point.get('SOG', 'N/A')
            cog = point.get('COG', 'N/A')
            
            popup_text = f"""
            <b>{vessel_name}</b><br>
            Time: {timestamp}<br>
            Position: {lat:.4f}, {lon:.4f}<br>
            Speed: {sog} knots<br>
            Course: {cog}°
            """
            
            # Use different colors for start, end, and middle points
            if i == 0:
                color = 'green'  # Start
                prefix = 'Start'
            elif i == len(coords) - 1:
                color = 'red'  # End
                prefix = 'End'
            else:
                color = 'blue'  # Middle
                prefix = f'Point {i}'
            
            folium.CircleMarker(
                location=(lat, lon),
                radius=5,
                popup=folium.Popup(popup_text, max_width=300),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
        
        return m
    
    @staticmethod
    def create_vessel_position_map(
        vessel_data: Dict[str, Any],
        vessel_name: str,
        zoom_start: int = 10
    ) -> folium.Map:
        """Create a folium map with single vessel position"""
        
        lat = vessel_data.get('LAT')
        lon = vessel_data.get('LON')
        
        if lat is None or lon is None:
            logger.warning("No valid position data")
            return None
        
        # Create map
        m = folium.Map(
            location=(lat, lon),
            zoom_start=zoom_start,
            tiles='OpenStreetMap'
        )
        
        # Add marker
        sog = vessel_data.get('SOG', 'N/A')
        cog = vessel_data.get('COG', 'N/A')
        timestamp = vessel_data.get('BaseDateTime', 'Unknown')
        
        popup_text = f"""
        <b>{vessel_name}</b><br>
        Time: {timestamp}<br>
        Position: {lat:.4f}, {lon:.4f}<br>
        Speed: {sog} knots<br>
        Course: {cog}°
        """
        
        folium.Marker(
            location=(lat, lon),
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color='blue', icon='ship', prefix='fa')
        ).add_to(m)
        
        return m
    
    @staticmethod
    def create_prediction_map(
        current_position: Tuple[float, float],
        predicted_position: Tuple[float, float],
        vessel_name: str,
        duration_minutes: int,
        zoom_start: int = 10
    ) -> folium.Map:
        """Create a folium map with current and predicted positions"""
        
        # Calculate center
        center_lat = (current_position[0] + predicted_position[0]) / 2
        center_lon = (current_position[1] + predicted_position[1]) / 2
        
        # Create map
        m = folium.Map(
            location=(center_lat, center_lon),
            zoom_start=zoom_start,
            tiles='OpenStreetMap'
        )
        
        # Add current position (green)
        folium.Marker(
            location=current_position,
            popup=f'<b>{vessel_name}</b><br>Current Position',
            icon=folium.Icon(color='green', icon='circle', prefix='fa')
        ).add_to(m)
        
        # Add predicted position (red)
        folium.Marker(
            location=predicted_position,
            popup=f'<b>{vessel_name}</b><br>Predicted Position<br>({duration_minutes} min)',
            icon=folium.Icon(color='red', icon='circle', prefix='fa')
        ).add_to(m)
        
        # Add line between positions
        folium.PolyLine(
            [current_position, predicted_position],
            color='orange',
            weight=2,
            opacity=0.7,
            popup=f'Predicted trajectory ({duration_minutes} min)'
        ).add_to(m)
        
        return m
    
    @staticmethod
    def create_geopandas_track(
        track_data: List[Dict[str, Any]],
        vessel_name: str
    ) -> Optional[gpd.GeoDataFrame]:
        """Create a geopandas GeoDataFrame from track data"""
        
        if not track_data:
            logger.warning("No track data provided")
            return None
        
        # Extract coordinates and create geometry
        from shapely.geometry import Point
        
        geometry = []
        data = []
        
        for point in track_data:
            lat = point.get('LAT')
            lon = point.get('LON')
            
            if lat is not None and lon is not None:
                geometry.append(Point(lon, lat))
                data.append({
                    'vessel_name': vessel_name,
                    'timestamp': point.get('BaseDateTime', 'Unknown'),
                    'lat': lat,
                    'lon': lon,
                    'sog': point.get('SOG'),
                    'cog': point.get('COG'),
                    'heading': point.get('Heading'),
                    'mmsi': point.get('MMSI')
                })
        
        if not geometry:
            logger.warning("No valid coordinates for geopandas")
            return None
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(
            data,
            geometry=geometry,
            crs='EPSG:4326'
        )
        
        return gdf
    
    @staticmethod
    def geopandas_to_geojson(gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Convert GeoDataFrame to GeoJSON"""
        try:
            return gdf.__geo_interface__
        except Exception as e:
            logger.error(f"Error converting to GeoJSON: {e}")
            return None
    
    @staticmethod
    def create_heatmap(
        track_data: List[Dict[str, Any]],
        vessel_name: str,
        zoom_start: int = 10
    ) -> folium.Map:
        """Create a heatmap of vessel positions"""
        
        if not track_data:
            logger.warning("No track data provided")
            return None
        
        # Extract coordinates
        coords = []
        for point in track_data:
            lat = point.get('LAT')
            lon = point.get('LON')
            if lat is not None and lon is not None:
                coords.append([lat, lon])
        
        if not coords:
            logger.warning("No valid coordinates for heatmap")
            return None
        
        # Create map
        center = coords[0]
        m = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles='OpenStreetMap'
        )
        
        # Add heatmap layer
        plugins.HeatMap(
            coords,
            name=f'{vessel_name} Density',
            min_opacity=0.2,
            radius=15,
            blur=25,
            max_zoom=1
        ).add_to(m)
        
        folium.LayerControl().add_to(m)
        
        return m


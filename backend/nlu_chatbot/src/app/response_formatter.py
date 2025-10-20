"""
Response Formatter for Maritime NLU
Converts backend responses into human-friendly sentences
"""
from typing import Dict, Any, Optional
from datetime import datetime
import math


class ResponseFormatter:
    """Format backend responses into human-readable text"""
    
    @staticmethod
    def format_show_response(response: Dict[str, Any]) -> str:
        """Format SHOW intent response"""
        if 'message' in response and response['message']:
            return response['message']
        
        if 'error' in response:
            return f"I couldn't find information about that vessel. {response['error']}"
        
        vessel_name = response.get('VesselName', 'Unknown Vessel')
        lat = response.get('LAT')
        lon = response.get('LON')
        sog = response.get('SOG')  # Speed Over Ground in knots
        cog = response.get('COG')  # Course Over Ground in degrees
        timestamp = response.get('BaseDateTime', 'Unknown Time')
        
        if lat is None or lon is None:
            return f"I found {vessel_name}, but position data is not available."
        
        # Format position
        lat_dir = "N" if lat >= 0 else "S"
        lon_dir = "E" if lon >= 0 else "W"
        lat_abs = abs(lat)
        lon_abs = abs(lon)
        
        position_str = f"{lat_abs:.4f}° {lat_dir}, {lon_abs:.4f}° {lon_dir}"
        
        # Build response
        response_text = f"**{vessel_name}** is currently at position {position_str}"
        
        # Add speed if available
        if sog is not None and sog > 0:
            response_text += f" traveling at {sog:.1f} knots"
        
        # Add course if available
        if cog is not None:
            direction = ResponseFormatter._get_compass_direction(cog)
            response_text += f" heading {direction} ({cog:.0f}°)"
        
        # Add timestamp
        if timestamp and timestamp != 'Unknown Time':
            response_text += f" as of {timestamp}"
        
        response_text += "."
        
        # Add track info if available
        if 'track' in response and response['track']:
            track_count = len(response['track'])
            response_text += f"\n\nI have {track_count} position records for this vessel in the database."
        
        return response_text
    
    @staticmethod
    def format_predict_response(response: Dict[str, Any]) -> str:
        """Format PREDICT intent response"""
        if 'message' in response and response['message']:
            return response['message']
        
        if 'error' in response:
            return f"I couldn't predict the vessel's position. {response['error']}"
        
        vessel_name = response.get('VesselName', 'Unknown Vessel')
        predicted_lat = response.get('predicted_lat')
        predicted_lon = response.get('predicted_lon')
        duration = response.get('duration_minutes', 0)
        current_lat = response.get('LAT')
        current_lon = response.get('LON')
        sog = response.get('SOG')
        
        if predicted_lat is None or predicted_lon is None:
            return f"I couldn't calculate a prediction for {vessel_name}."
        
        # Format predicted position
        lat_dir = "N" if predicted_lat >= 0 else "S"
        lon_dir = "E" if predicted_lon >= 0 else "W"
        lat_abs = abs(predicted_lat)
        lon_abs = abs(predicted_lon)
        
        position_str = f"{lat_abs:.4f}° {lat_dir}, {lon_abs:.4f}° {lon_dir}"
        
        # Calculate distance traveled
        distance_nm = None
        if current_lat is not None and current_lon is not None and sog is not None:
            distance_nm = ResponseFormatter._haversine_distance(
                current_lat, current_lon, predicted_lat, predicted_lon
            )
        
        # Build response
        response_text = f"Based on current speed and course, **{vessel_name}** "
        response_text += f"will be at position {position_str} "
        response_text += f"in {duration} minutes"
        
        if distance_nm is not None:
            response_text += f" (approximately {distance_nm:.1f} nautical miles away)"
        
        response_text += "."
        
        return response_text
    
    @staticmethod
    def format_verify_response(response: Dict[str, Any]) -> str:
        """Format VERIFY intent response"""
        if 'message' in response and response['message']:
            return response['message']
        
        if 'error' in response:
            return f"I couldn't verify the vessel's movement. {response['error']}"
        
        vessel_name = response.get('VesselName', 'Unknown Vessel')
        is_consistent = response.get('is_consistent', False)
        anomalies = response.get('anomalies', [])
        
        # Build response
        if is_consistent:
            response_text = f"✅ **{vessel_name}**'s movement appears consistent and normal."
        else:
            response_text = f"⚠️ **{vessel_name}** has some unusual movement patterns:\n"
            
            for anomaly in anomalies:
                anomaly_type = anomaly.get('type', 'Unknown')
                details = anomaly.get('details', '')
                
                if anomaly_type == 'large_jump':
                    response_text += f"  • Large position jump: {details}\n"
                elif anomaly_type == 'course_change':
                    response_text += f"  • Sudden course change: {details}\n"
                else:
                    response_text += f"  • {anomaly_type}: {details}\n"
        
        return response_text.strip()
    
    @staticmethod
    def format_response(intent: str, response: Dict[str, Any]) -> str:
        """Format response based on intent type"""
        if intent == "SHOW":
            return ResponseFormatter.format_show_response(response)
        elif intent == "PREDICT":
            return ResponseFormatter.format_predict_response(response)
        elif intent == "VERIFY":
            return ResponseFormatter.format_verify_response(response)
        else:
            # Generic response
            if 'message' in response:
                return response['message']
            return "I processed your request but couldn't generate a response."
    
    @staticmethod
    def _get_compass_direction(degrees: float) -> str:
        """Convert degrees to compass direction"""
        directions = [
            "North", "NNE", "NE", "ENE",
            "East", "ESE", "SE", "SSE",
            "South", "SSW", "SW", "WSW",
            "West", "WNW", "NW", "NNW"
        ]
        index = int((degrees + 11.25) / 22.5) % 16
        return directions[index]
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in nautical miles using Haversine formula"""
        R = 3440.065  # Earth's radius in nautical miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c


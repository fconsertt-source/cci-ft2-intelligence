from typing import List, Any
from datetime import datetime
from src.domain.models.temperature_exposure import TemperatureExposure

class ExposureMapper:
    """
    Responsible for converting raw temperature readings (with timestamps)
    into pure domain TemperatureExposure objects (with duration).
    
    This enforces the architectural rule: 'Application calculates, Domain decides'.
    """
    
    @staticmethod
    def map_to_domain(readings: List[Any]) -> List[TemperatureExposure]:
        """
        Maps a list of objects having 'value' (temp) and 'timestamp' 
        to a list of TemperatureExposure objects.
        """
        if not readings or len(readings) < 2:
            return []
            
        # Ensure readings are sorted by timestamp
        # We assume readings have .timestamp and .value attributes (DTOs)
        try:
            sorted_readings = sorted(readings, key=lambda r: r.timestamp)
        except AttributeError:
            # Fallback for dicts if necessary
            sorted_readings = sorted(readings, key=lambda r: r['timestamp'])

        exposures = []
        
        for i in range(len(sorted_readings) - 1):
            current = sorted_readings[i]
            next_reading = sorted_readings[i+1]
            
            # Extract values safely
            temp = getattr(current, 'value', None)
            if temp is None and isinstance(current, dict):
                 temp = current.get('value')

            t1 = getattr(current, 'timestamp', None)
            if t1 is None and isinstance(current, dict):
                t1 = current.get('timestamp')
                
            t2 = getattr(next_reading, 'timestamp', None)
            if t2 is None and isinstance(next_reading, dict):
                t2 = next_reading.get('timestamp')

            # Calculate duration
            if t1 and t2 and temp is not None:
                duration_seconds = (t2 - t1).total_seconds()
                duration_minutes = duration_seconds / 60.0
                
                if duration_minutes > 0:
                    exposures.append(TemperatureExposure(
                        temperature=float(temp),
                        duration_minutes=duration_minutes
                    ))
                
        return exposures
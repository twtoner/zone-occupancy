from __future__ import annotations # enables hinting of on a class method of the class itself
from json import JSONDecodeError  
import warnings
import geojson
import shapely
from shapely import Polygon
from typing import List
from itertools import combinations
from numbers import Number
import shapely.plotting

def validate_coordinates(coordinates: List[List[float]]):
    '''
    Ensure that 'coordinates' is a valid list of coordinate pairs.
    Refactored from validation checking in both class initializations.
    '''
    # Check validity of coordinates list
    if type(coordinates) is not list or len(coordinates) == 0:
        raise ValueError("Coordinates must be a list of coordinates.")
    
    # Check validity of content of coordinates
    if not all([type(v) is list and len(v) == 2 and all([isinstance(vv, Number) for vv in v])for v in coordinates]):
        raise ValueError("Each coordinate must be a list of two numerical values.")


class Vehicle:
    '''
    Represents a vehicle with a polygonal boundary. Allows setting and calculating
    of buffer zones based on communication delay.

    Attributes:
        vertices (List[List[float]]): Coordinates in meters of the vertices of the vehicle's polygon.
        update_age (float): Time in seconds since the last position update was received.
    '''
    BUFFER_EXPANSION_RATE = 3.0   # m/s bound expansion rate due to communication delay
    def __init__(self, vertices: List[List[float]]):
        '''
        Initializes a new Vehicle instance with specified boundary vertices.

        This constructor validates and sets the vertices that define the vehicle's polygonal boundary.
        It also initializes the update age to zero, indicating no time has passed since the last known update.

        Args:
            vertices (List[List[float]]): A list of vertex coordinates in meters where each vertex is represented 
            as a list of two floats [x, y]. This list defines the boundary of the vehicle as a polygon.

        '''
        # Validate argument
        validate_coordinates(vertices)

        self.vertices = vertices  # boundary coordinates (m)
        self.update_age = 0.0  # duration since last GPS update (sec)

    def set_update_age(self, age: float):
        '''
        Sets the update age of the vehicle, representing the time elapsed in seconds since the last known GPS update.

        Args:
            age (float): The time in seconds since the last GPS update. Must be a non-negative number.
        '''
        if not isinstance(age, Number) or age < 0:
            raise ValueError("age must be a nonnegative number")

        self.update_age = age

    def get_bounds(self) -> Polygon:
        '''
        Returns the current bounds in meters of the vehicle as a shapely.Polygon object,
        taking into account any expansion due to communication delays.

        Returns:
            Polygon: The polygon representing the vehicle's current bounds.
        '''
        ## No communication delay: return vertices directly
        # NOTE: Optional early return to avoid unnecessary computation.
        if self.update_age == 0.0:
            return Polygon(self.vertices)

        ## Communication delay: dilate vehicle bounds with buffer
        # Calculate buffer distance
        buffer_dist = self.update_age * self.BUFFER_EXPANSION_RATE
        # Dilate bounds by buffer distance and return
        return Polygon(self.vertices).buffer(buffer_dist, join_style='mitre')


class Zone:
    '''
    Represents a planar zone defined by a polygon.

    Attributes:
        zonetype (str): The type of zone, e.g., 'autonomousOperatingZone' or 'singleTruckZone'.
        bounds (Polygon): The polygonal boundaries of the zone in meters.
    '''

    def __init__(self, zonetype: str, coordinates: List[List[List[float]]]):
        '''
        Initializes a Zone object with a specific type and planar boundaries.
        
        Args:
            zonetype (str): The type of zone, e.g., 'autonomousOperatingZone' or 'singleTruckZone'.
            coordinates (List[List[List[float]]]): A list of lists of lists where each innermost list 
                contains two floats representing a vertex. The first list of vertices forms the outer 
                boundary (shell) of the zone, and any subsequent lists form holes within the zone.
                Based on the GeoJSON geometry convention of specifying regions with holes.
        '''
        # Validate arguments        
        if not isinstance(zonetype, str):
            ValueError('zonetype must be a string')
        
        if isinstance(coordinates, list):
            shell = coordinates[0]
            holes = coordinates[1:]
            validate_coordinates(shell)
            if len(holes) > 0:
                for hole in holes:
                    validate_coordinates(hole)
        else:
            raise ValueError("coordinates must contain list of list of coordinate pairs.")

        self.zonetype = zonetype
        self.bounds = Polygon(shell=coordinates[0], holes=coordinates[1:])

    def get_bounds(self) -> Polygon:
        '''
        Retrieves the polygonal bounds of the zone.

        Returns:
            Polygon: The polygon representing the zone's boundaries.
        '''
        return self.bounds
    
    @classmethod
    # Function 0
    def from_geojson(cls, filename: str) -> List[Zone]:
        '''
        Parses a GeoJSON file to extract zones as Zone objects.

        Note that we return an empty list of zones in most cases of 
        invalid files or filenames, expecting that use case of the user
        iterating over a list of zone files and preferring an empty return to 
        an exception.

        Args:
            filename (str): Path to the GeoJSON file.

        Returns:
            List[Zone]: A list of Zone objects parsed from the GeoJSON file.
        '''        
        # Decode GeoJSON file
        try:
            with open(filename, "rb") as f:
                gjson = geojson.load(f)
        except TypeError as te:
            warnings.warn(f'Input {filename} not a valid string.')
            return []  
        except FileNotFoundError as fnfe:
            warnings.warn(f'File {filename} not found.')
            return []  
        except JSONDecodeError as jde:
            warnings.warn(f'File {filename} must encoded as a JSON file.')
            return []
        
        # Ensure file contains expected fields
        if 'features' not in gjson.keys():
            warnings.warn(f'GeoJSON file {filename} contains no field features.')
            return []
        
        if 'type' not in gjson.keys():
            warnings.warn(f'GeoJSON file {filename} contains no field type.')
            return []

        # Warn if empty
        if len(gjson.features) == 0:
            warnings.warn(f'GeoJSON file {filename} contains empty feature list.')

        # Extract geometry and zoneType from features, if any
        zones = []
        for i, feature in enumerate(gjson.features):
            # Check for feature validity
            if feature.type != "Feature":
                print("GeoJSON file contains an invalid feature; skipping")
                continue
            if "zoneType" not in feature.properties:
                print(f"GeoJSON feature {i} contains an invalid zoneType; skipping")
                continue
            if "geometry" not in feature:
                print(f"GeoJSON feature {i} does not contain geometry; skipping")
                continue
            if feature.geometry.type != "Polygon":
                print(f"GeoJSON feature {i} contains geometry that is not a Polygon; skipping")
                continue

            # Extract zone type and geometry to create Zone object
            zone = Zone(
                zonetype=feature.properties["zoneType"],
                coordinates=feature.geometry.coordinates,
            )
            zones.append(zone)
        
        return zones


## Assigned functions

# Function 0 (see Zone.from_geojson)

# Function 1
def vehicle_contained_in_zone(zone: Zone, vehicle: Vehicle) -> bool:
    '''
    Determines whether a Vehicle is entirely contained within a Zone.

    Args:
        zone (Zone): The zone to check against.
        vehicle (Vehicle): The vehicle to check.

    Returns:
        bool: True if the vehicle is entirely within the zone, False otherwise.
    '''
    # Extract Polygon bounds from zone and vehicle and use 
    # shapely's .contains method to check containment. 
    if not isinstance(zone, Zone):
        raise ValueError('zone must be a Zone')
    if not isinstance(vehicle, Vehicle):
        raise ValueError('vehicle must be a Vehicle')
    return shapely.contains(zone.get_bounds(), vehicle.get_bounds())


# Function 2
def vehicle_intersects_zone(zone: Zone, vehicle: Vehicle) -> bool:
    '''
    Checks if a Vehicle intersects with a Zone.

    Args:
        zone (Zone): The zone to check against.
        vehicle (Vehicle): The vehicle to check.

    Returns:
        bool: True if the vehicle intersects the zone, False otherwise.
    '''
    # Extract Polygon bounds from zone and vehicle and use 
    # shapely's .intersects method to check intersection. 
    if not isinstance(zone, Zone):
        raise ValueError('zone must be a Zone')
    if not isinstance(vehicle, Vehicle):
        raise ValueError('vehicle must be a Vehicle')
    return shapely.intersects(zone.get_bounds(), vehicle.get_bounds())


# Function 3
def vehicle_intersects_occupied_zone(zone: Zone, target_vehicle: Vehicle, other_vehicles: List[Vehicle]) -> bool:
    '''
    Determines if a Vehicle intersects a Zone that is also intersected by other Vehicles.

    Args:
        zone (Zone): The zone to check.
        target_vehicle (Vehicle): The target vehicle to check.
        other_vehicles (List[Vehicle]): Other vehicles to consider.

    Returns:
        bool: True if the target vehicle and any other vehicle intersect the zone, False otherwise.
    '''
    if not isinstance(zone, Zone):
        raise ValueError('zone must be a Zone')
    if not isinstance(target_vehicle, Vehicle):
        raise ValueError('target_vehicle must be a Vehicle')
    if not isinstance(other_vehicles, list) or not all([isinstance(v, Vehicle) for v in other_vehicles]):
        raise ValueError('other_vehicles must be a list of Vehicles')

    # First check if the target vehicle intersects the zone
    target_vehicle_intersects = vehicle_intersects_zone(zone, target_vehicle)
    if not target_vehicle_intersects:
        return False
    # If the target vehicle does intersect, check zone intersection of other vehicles
    zone_occupied = any([vehicle_intersects_zone(zone, v) for v in other_vehicles])
    return zone_occupied


# Function 4
def vehicles_intersect(vehicles: List[Vehicle]) -> bool:
    '''
    Determines if any of the vehicles' boundaries intersect with one another.

    Args:
        vehicles (List[Vehicle]): The list of vehicles to check.
x
    Returns:
        bool: True if any pair of vehicles intersect, False otherwise.
    '''
    if not isinstance(vehicles, list) or not all([isinstance(v, Vehicle) for v in vehicles]):
        raise ValueError('other_vehicles must be a list of Vehicles')
    
    # Extract all Polygon bounds from vehicles
    all_bounds = [vehicle.get_bounds() for vehicle in vehicles]
    
    # Check intersection of all vehicle bounds pair-wise
    for pair in combinations(all_bounds, 2):
        if shapely.intersects(*pair):
            return True
    return False

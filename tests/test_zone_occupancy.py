from copy import deepcopy
import unittest
from zone_occupancy.zone_occupancy import (
    Vehicle,
    Zone,
    validate_coordinates,
    vehicle_contained_in_zone,
    vehicle_intersects_zone,
    vehicle_intersects_occupied_zone,
    vehicles_intersect,
)
import numpy as np


class TestValidateCoordinates(unittest.TestCase):
    def test_init_none(self):
        self.assertRaises(ValueError, validate_coordinates, None)

    def test_init_empty(self):
        self.assertRaises(ValueError, validate_coordinates, [])

    def test_init_badlist_1(self):
        self.assertRaises(ValueError, validate_coordinates, [1, 2, 3, 4])

    def test_init_badlist_2(self):
        self.assertRaises(ValueError, validate_coordinates, [[1, 2], ["three", 4]])


class TestVehicle(unittest.TestCase):

    def test_set_update_age_none(self):
        vehicle = Vehicle([[0, 0], [0, 1], [1, 1], [1, 0]])
        self.assertRaises(ValueError, vehicle.set_update_age, None)

    def test_set_update_age_negative(self):
        vehicle = Vehicle([[0, 0], [0, 1], [1, 1], [1, 0]])
        self.assertRaises(ValueError, vehicle.set_update_age, -1.0)

    def test_get_bounds(self):
        vehicle = Vehicle([[0, 0], [0, 1], [1, 1], [1, 0]])
        # Update vehicle age and get new boundary
        new_age = 2.0
        vehicle.set_update_age(new_age)
        new_bounds = vehicle.get_bounds()
        # Calculate expected new vertices
        buffer_dist = new_age * vehicle.BUFFER_EXPANSION_RATE
        expected_vertices = np.array(
            [
                [-buffer_dist, -buffer_dist],
                [-buffer_dist, 1 + buffer_dist],
                [1 + buffer_dist, 1 + buffer_dist],
                [1 + buffer_dist, -buffer_dist],
            ]
        )
        # Get actual new vertices
        x, y = new_bounds.exterior.coords.xy
        actual_vertices = np.array([[xx, yy] for xx, yy in zip(x, y)])

        # Compare vertices (vertices may be in different orders in actual_ and expected_
        diffs = np.array(
            [
                [np.linalg.norm(ev - av) for ev in expected_vertices]
                for av in actual_vertices
            ]
        )
        vertex_diffs = np.min(diffs, axis=0)

        # Assert that the differences are zero (within acceptable tolerance, say 1e-6)
        self.assertTrue(np.all(vertex_diffs < 1e-6))


class TestZone(unittest.TestCase):

    def test_from_geojson_none(self):
        self.assertEqual(len(Zone.from_geojson(None)), 0)

    def test_from_geojson_empty(self):
        self.assertEqual(len(Zone.from_geojson("zone_empty.json")), 0)

    def test_from_geojson_not_json(self):
        self.assertEqual(len(Zone.from_geojson("empty.txt")), 0)

    def test_from_geojson_does_not_exist(self):
        self.assertEqual(len(Zone.from_geojson("dne.txt")), 0)


class TestVehicleContainedInZone(unittest.TestCase):

    def test_in_zone(self):
        vehicle = Vehicle([[-0.1, -0.1], [-0.1, 0.1], [0.1, 0.1], [0.1, -0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertEqual(vehicle_contained_in_zone(zone, vehicle), True)

    def test_outside_zone(self):
        vehicle = Vehicle([[10-0.1, 10-0.1], [10-0.1, 10+0.1], [10+0.1, 10+0.1], [10+0.1, 10-0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertEqual(vehicle_contained_in_zone(zone, vehicle), False)

    def test_vehicle_intersecting_zone(self):
        # shift in_zone vehicle to right by 0.2
        vehicle = Vehicle([[0.2-0.1, -0.1], [0.2-0.1, 0.1], [0.2+0.1, 0.1], [0.2+0.1, -0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertEqual(vehicle_contained_in_zone(zone, vehicle), False)

    def test_invalid_args(self):
        vehicle = Vehicle([[-0.1, -0.1], [-0.1, 0.1], [0.1, 0.1], [0.1, -0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertRaises(ValueError, vehicle_contained_in_zone, vehicle, zone)
        self.assertRaises(ValueError, vehicle_contained_in_zone, zone, None)
        self.assertRaises(ValueError, vehicle_contained_in_zone, None, zone)

class TestVehicleIntersectsZone(unittest.TestCase):

    def test_in_zone(self):
        vehicle = Vehicle([[-0.1, -0.1], [-0.1, 0.1], [0.1, 0.1], [0.1, -0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertEqual(vehicle_intersects_zone(zone, vehicle), True)

    def test_outside_zone(self):
        vehicle = Vehicle([[10-0.1, 10-0.1], [10-0.1, 10+0.1], [10+0.1, 10+0.1], [10+0.1, 10-0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertEqual(vehicle_intersects_zone(zone, vehicle), False)

    def test_vehicle_intersecting_zone(self):
        # shift in_zone vehicle to right by 0.2
        vehicle = Vehicle([[0.2-0.1, -0.1], [0.2-0.1, 0.1], [0.2+0.1, 0.1], [0.2+0.1, -0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertEqual(vehicle_intersects_zone(zone, vehicle), True)

    def test_invalid_args(self):
        vehicle = Vehicle([[-0.1, -0.1], [-0.1, 0.1], [0.1, 0.1], [0.1, -0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertRaises(ValueError, vehicle_intersects_zone, vehicle, zone)
        self.assertRaises(ValueError, vehicle_intersects_zone, zone, None)
        self.assertRaises(ValueError, vehicle_intersects_zone, None, zone)

class TestVehicleIntersectsOccupiedZone(unittest.TestCase):

    def test_not_intersects_unoccupied(self):
        outside_vehicle1 = Vehicle([[10-0.1, 10-0.1], [10-0.1, 10+0.1], [10+0.1, 10+0.1], [10+0.1, 10-0.1]])
        outside_vehicle2 = Vehicle([[5-0.1, 5-0.1], [5-0.1, 5+0.1], [5+0.1, 5+0.1], [5+0.1, 5-0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertEqual(vehicle_intersects_occupied_zone(zone, outside_vehicle1, [outside_vehicle2]), False)
        self.assertEqual(vehicle_intersects_occupied_zone(zone, outside_vehicle2, [outside_vehicle1]), False)

    def test_intersects_unoccupied(self):
        outside_vehicle1 = Vehicle([[10-0.1, 10-0.1], [10-0.1, 10+0.1], [10+0.1, 10+0.1], [10+0.1, 10-0.1]])
        intersecting_vehicle1 = Vehicle([[0.2-0.1, -0.1], [0.2-0.1, 0.1], [0.2+0.1, 0.1], [0.2+0.1, -0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertEqual(vehicle_intersects_occupied_zone(zone, intersecting_vehicle1, [outside_vehicle1]), False)

    def test_not_intersects_occupied(self):
        outside_vehicle1 = Vehicle([[10-0.1, 10-0.1], [10-0.1, 10+0.1], [10+0.1, 10+0.1], [10+0.1, 10-0.1]])
        intersecting_vehicle1 = Vehicle([[0.2-0.1, -0.1], [0.2-0.1, 0.1], [0.2+0.1, 0.1], [0.2+0.1, -0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertEqual(vehicle_intersects_occupied_zone(zone, outside_vehicle1, [intersecting_vehicle1]), False)

    def test_intersects_occupied(self):
        intersecting_vehicle1 = Vehicle([[0.2-0.1, -0.1], [0.2-0.1, 0.1], [0.2+0.1, 0.1], [0.2+0.1, -0.1]])
        intersecting_vehicle2 = Vehicle([[-0.2-0.1, -0.1], [-0.2-0.1, 0.1], [-0.2+0.1, 0.1], [-0.2+0.1, -0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertEqual(vehicle_intersects_occupied_zone(zone, intersecting_vehicle1, [intersecting_vehicle2]), True)

    def test_invalid_args(self):
        intersecting_vehicle1 = Vehicle([[0.2-0.1, -0.1], [0.2-0.1, 0.1], [0.2+0.1, 0.1], [0.2+0.1, -0.1]])
        zone = Zone("name", [[[-0.2, -0.2], [-0.2, 0.2], [0.2, 0.2], [0.2, -0.2]]])
        self.assertRaises(ValueError, vehicle_intersects_occupied_zone, None, None, None)
        self.assertRaises(ValueError, vehicle_intersects_occupied_zone, zone, intersecting_vehicle1, intersecting_vehicle1)
        self.assertRaises(ValueError, vehicle_intersects_occupied_zone, intersecting_vehicle1, [intersecting_vehicle1], zone)

class TestVehiclesIntersect(unittest.TestCase):

    def test_not_intersecting(self):        
        vehicle1 = Vehicle([[-0.1, -0.1], [-0.1, 0.1], [0.1, 0.1], [0.1, -0.1]])
        vehicle2 = Vehicle([[10-0.1, 10-0.1], [10-0.1, 10+0.1], [10+0.1, 10+0.1], [10+0.1, 10-0.1]])
        self.assertEqual(vehicles_intersect([vehicle1, vehicle2]), False)

    def test_intersecting(self):        
        vehicle1 = Vehicle([[-0.1, -0.1], [-0.1, 0.1], [0.1, 0.1], [0.1, -0.1]])
        vehicle2 = Vehicle([[0.09-0.1, -0.1], [0.09-0.1, 0.1], [0.09+0.1, 0.1], [0.09+0.1, -0.1]])
        self.assertEqual(vehicles_intersect([vehicle1, vehicle2]), True)

    def test_intersecting_after_delay(self):
        vehicle1 = Vehicle([[-0.1, -0.1], [-0.1, 0.1], [0.1, 0.1], [0.1, -0.1]])
        vehicle2 = Vehicle([[10-0.1, 10-0.1], [10-0.1, 10+0.1], [10+0.1, 10+0.1], [10+0.1, 10-0.1]])
        self.assertEqual(vehicles_intersect([vehicle1, vehicle2]), False)
        vehicle1.set_update_age(10.0)
        self.assertEqual(vehicles_intersect([vehicle1, vehicle2]), True)

    def test_invalid_args(self):
        vehicle1 = Vehicle([[-0.1, -0.1], [-0.1, 0.1], [0.1, 0.1], [0.1, -0.1]])
        self.assertRaises(ValueError, vehicles_intersect, None)
        self.assertRaises(ValueError, vehicles_intersect, [vehicle1, None])
        self.assertRaises(ValueError, vehicles_intersect, vehicle1)


if __name__ == "__main__":
    unittest.main()

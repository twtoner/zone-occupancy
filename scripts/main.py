from zone_occupancy.zone_occupancy import (
    Vehicle,
    Zone,
    vehicle_contained_in_zone,
    vehicle_intersects_zone,
    vehicle_intersects_occupied_zone,
    vehicles_intersect,
)
import shapely
import matplotlib.pyplot as plt

'''
Main script intended to address the questions posed in the prompt.
'''

def main():
    # Import zones from GeoJSON file
    zones = Zone.from_geojson('data/zone.json')

    # Specify vehicles
    vehicle1 = Vehicle(vertices=[[1, 4], [3, 6], [5, 4], [3, 2]])
    vehicle2 = Vehicle(vertices=[[-2, -2], [-6, -2], [-6, -4], [-2, -4]])
    vehicle3 = Vehicle(vertices=[[-3, 9], [-3, 11], [-5, 11], [-5, 9]])
    vehicles = [vehicle1, vehicle2, vehicle3]

    ## Questions
    # Question 1
    print('Is the vehicle contained in the autonomous operating zone?')
    autonomous_op_zone = [z for z in zones if z.zonetype == 'autonomousOperatingZone'][0]
    for i, vehicle in enumerate(vehicles):
        vehicle_contained = vehicle_contained_in_zone(autonomous_op_zone, vehicle)
        print(f'Vehicle {i+1} contained in autonomous operating zone: {vehicle_contained}')

    # Question 2
    print('\nIs any part of the vehicle intersecting the single truck zone?')
    single_truck_zone = [z for z in zones if z.zonetype == 'singleTruckZone'][0]
    for i, vehicle in enumerate(vehicles):
        vehicle_intersects = vehicle_intersects_zone(single_truck_zone, vehicle)
        print(f'Vehicle {i+1} is intersecting the single truck zone: {vehicle_intersects}')

    # Question 3
    print('\nIs any part of the vehicle intersecting the single truck zone that is already occupied by another vehicle?')
    for i, vehicle in enumerate(vehicles):
        other_vehicles = [v for v in vehicles if v is not vehicle]
        vehicle_intersects_occupied = vehicle_intersects_occupied_zone(single_truck_zone, vehicle, other_vehicles)
        print(f'Vehicle {i+1} is intersecting the single truck zone while it is already occuped by another vehicle: {vehicle_intersects_occupied}')

    # Question 4:
    print('\nIf vehicle 2 has been missing for 5 seconds, are any vehicle buffers intersecting?')
    vehicles_intersect_wo_delay = vehicles_intersect(vehicles)
    # Update the communication delay of vehicle 2
    vehicle2.set_update_age(5.0)
    vehicles_intersect_delay = vehicles_intersect(vehicles)
    print(f'Vehicle buffers intersect without communication loss: {vehicles_intersect_wo_delay}')
    print(f'Vehicle buffers intersect after a 5 second communication loss of vehicle 2: {vehicles_intersect_delay}\n')

    # Visualization
    vehicle2.set_update_age(0.0)  # return to 0.0 for plotting purposes
    for vehicle in vehicles:
        shapely.plotting.plot_polygon(vehicle.get_bounds())

    for zone in zones:
        shapely.plotting.plot_polygon(zone.get_bounds())

    shapely.plotting.plot_polygon(vehicle1.get_bounds(), color='red', label='vehicle 1')
    shapely.plotting.plot_polygon(vehicle2.get_bounds(), color='orange', label='vehicle 2')
    shapely.plotting.plot_polygon(vehicle3.get_bounds(), color='blue', label='vehicle 3')

    vehicle2.set_update_age(5.0)
    shapely.plotting.plot_polygon(vehicle2.get_bounds(), color='yellow', label='vehicle 2 after 5 seconds')

    shapely.plotting.plot_polygon(autonomous_op_zone.get_bounds(), color='purple', label='autonomous operating zone')
    shapely.plotting.plot_polygon(single_truck_zone.get_bounds(), color='green', label='single truck zone')

    plt.xlabel('East coordinates (m)')
    plt.ylabel('North coordinates (m)')
    plt.legend(loc='lower right')
    try:    # user may try to run from inside the scripts folder instead of in root folder
        plt.savefig('scripts/scene.png', dpi=600)
    except:
        pass
    plt.show()


if __name__ == '__main__':
    main()

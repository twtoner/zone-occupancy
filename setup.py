from setuptools import setup, find_packages

setup(
    name='zone_occupancy',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'shapely',
        'geojson',
    ],
    entry_points={
        'console_scripts': [
            'zone_occupancy=zone_occupancy.main:main'
        ]
    },
    python_requires='>=3.8',
)

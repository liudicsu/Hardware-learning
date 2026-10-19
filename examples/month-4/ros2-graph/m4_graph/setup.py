from glob import glob

from setuptools import find_packages, setup

package_name = 'm4_graph'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # install the launch and config folders, so `ros2 launch` and the YAML path work
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='Month 4 lesson 2: a multi-node graph with a custom msg, srv and action',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'sensor_node = m4_graph.sensor_node:main',
            'config_node = m4_graph.config_node:main',
            'aggregator_node = m4_graph.aggregator_node:main',
            'collect_client = m4_graph.collect_client:main',
        ],
    },
)

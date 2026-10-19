from glob import glob

from setuptools import setup

package_name = 'm4_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/urdf', glob('urdf/*.xacro')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='Month 4 lesson 5: m4bot through ros2_control, and a DriveDistance action',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'drive_distance = m4_control.drive_distance:main',
        ],
    },
)

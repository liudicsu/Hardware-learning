from setuptools import find_packages, setup

package_name = 'm4_hello'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='Month 4 lesson 1: a first ROS 2 node',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'hello_node = m4_hello.hello_node:main'
        ],
    },
)

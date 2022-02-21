from setuptools import find_packages, setup

VERSION='4.0.2'
DESCRIPTION='Library with useful functions for robotics labs.'
LONG_DESCRIPTION='This library have functions to generate tree differents trajectories, robot dinamyc and kinematic is computed using Pinocchio library.'

CLASSIFIERS=[   'Development Status :: Production/Stable',
                'Intented Audience :: Education',
                'Operating System :: Linux :: Ubuntu 20.04',
                'License :: OSI Approved :: MIT License',
                'Programming Language :: Python :: 3'
            ]

KEYWORDS = ['python3', 'robotics']

setup(
    name='labpythonlib',
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    url='',
    author='Jhon Charaja',
    author_email='jhon.charaja@usp.br',
    license='MIT',
    packages=find_packages(include=['labpythonlib']),
    install_requires=['']
)
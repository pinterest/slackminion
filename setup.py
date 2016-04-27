from setuptools import setup, find_packages
from slackminion.plugins.core import version

setup(
        name='slackminion',
        version=version,
        packages=find_packages(exclude=['test_plugins']),
        url='https://github.com/arcticfoxnv/slackminion',
        license='MIT',
        author='Nick King',
        author_email='',
        description='A python bot framework for slack',
        install_requires=[
            'bottle',
            'PyYAML',
            'requests',
            'Rocket',
            'six',
            'slackclient',
            'websocket-client',
        ],
        entry_points={
            'console_scripts': [
                'slackminion = slackminion.__main__:main',
            ]
        },
        classifiers=[
            "Programming Language :: Python",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Development Status :: 2 - Pre-Alpha",
            "Topic :: Communications :: Chat",
        ]
)

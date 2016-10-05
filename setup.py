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
        package_data={'slackminion': ['templates/*']},
        install_requires=[
            'Flask',
            'PyYAML',
            'requests',
            'six',
            'slackclient',
            'websocket-client',
        ],
        setup_requires=[
            'pytest-runner'
        ],
        tests_require=[
            'pytest==2.6.4',
            'pytest-cov==2.2.1',
            'codeclimate-test-reporter==0.1.2',
            'coverage==4.1'
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

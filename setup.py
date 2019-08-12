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
            'Flask>=0.10.1',
            'itsdangerous>=0.24',
            'Jinja2>=2.6',
            'MarkupSafe>=0.23',
            'PyYAML>=3.10',
            'requests >=2.11, <3.0a0',
            'six >=1.10, <2.0a0',
            'slackclient==1.3.1',
            'websocket-client >=0.35, <0.55.0',
            'Werkzeug>=0.10.4',
        ],
        setup_requires=[
            'pytest-runner'
        ],
        tests_require=[
            'pytest==4.4.1',
            'pytest-cov==2.6.1',
            'codeclimate-test-reporter==0.1.2',
            'coverage==4.5.2',
            'mock==3.0.5',
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

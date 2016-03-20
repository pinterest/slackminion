from setuptools import setup

setup(
        name='slackminion',
        version='0.1.8',
        packages=['slackminion', 'slackminion.plugins'],
        url='https://github.com/arcticfoxnv/slackminion',
        license='MIT',
        author='Nick King',
        author_email='',
        description='',
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

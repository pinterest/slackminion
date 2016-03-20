from setuptools import setup

setup(
        name='slackminion',
        version='0.1.4',
        packages=['slackminion', 'slackminion.plugins'],
        url='https://github.com/arcticfoxnv/slackminion',
        license='MIT',
        author='',
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
        }
)

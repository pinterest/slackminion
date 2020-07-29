# slackminion
A python bot framework for slack

![Build Status](https://github.com/pinterest/slackminion/workflows/CI/badge.svg) [![Code Climate](https://codeclimate.com/github/pinterest/slackminion/badges/gpa.svg)](https://codeclimate.com/github/pinterest/slackminion) [![Test Coverage](https://codeclimate.com/github/pinterest/slackminion/badges/coverage.svg)](https://codeclimate.com/github/pinterest/slackminion/coverage)

## Running
It is recommended that you set up a virtual environment in which to run slackminion. Install the app:

```
$ python setup.py install
```

Run the application using the built-in `slackminion` command. Use a config.yaml to customize the plugins you wish to run. You can test your plugin configuration before running a live app:

```
# Generate a plugin report:
$ slackminion --config config.yaml --test

# Run a live bot:
$ slackminion --config config.yaml
```

See the documentation for more information and details on how to write a plugin.

## Documentation
http://slackminion.readthedocs.org/

## Contributing
It is recommended that you set up a virtual environment in which to run slackminion. Bootstrapping the application should be pretty straightforward:

```
$ python setup.py develop
$ python setup.py test
```

All tests should pass before and after you make your commits.

## Python3 Support

As of Version 0.10, slackminion requires Python >= 3.6.  This is due to both the upgrade of the slack client (which requries Python3), and the usage of async functions and f-strings within the slackminion code.  If you need Python 2.x, please pin version >= 0.9.x of slackminion.

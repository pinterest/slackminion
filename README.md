# slackminion
A python bot framework for slack

[![Build Status](https://travis-ci.org/arcticfoxnv/slackminion.svg?branch=master)](https://travis-ci.org/arcticfoxnv/slackminion) [![Code Climate](https://codeclimate.com/github/arcticfoxnv/slackminion/badges/gpa.svg)](https://codeclimate.com/github/arcticfoxnv/slackminion) [![Test Coverage](https://codeclimate.com/github/arcticfoxnv/slackminion/badges/coverage.svg)](https://codeclimate.com/github/arcticfoxnv/slackminion/coverage)

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


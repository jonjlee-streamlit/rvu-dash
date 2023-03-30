#!/bin/bash
# Run to upgrade python tools and dependencies to latest version

echo ***** Upgrade pipenv and pip *****
pip install --user --upgrade pipenv
pip install --upgrade pip

# Activate the virtual environment for the project in a subshell
# that upgrades all dependencies to their latest available versions
#
# Pipfile specifies package versions ="*" (eg streamlit = "*"), so we'll upgrade to the latest major/minor version.
# Note, this may break code if there are incompatible major version changes
echo ***** Upgrade all packages *****
pipenv update

echo ***** Current package versions *****
pipenv run pip freeze

echo Run "pipenv shell" to start virtual environment.

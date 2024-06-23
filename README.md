# PyPlanet-dbcleanup
PyPlanet app providing an admin command for cleaning up the database. The clean-up will remove maps and associated models (karma votes, records, map folder content, scores) from the database for maps that are no longer on the server.

## Installation
* ``cd pyplanet/apps``
* ``git clone https://github.com/TheMaximum/PyPlanet-dbcleanup.git dbcleanup``
* Edit ``pyplanet/settings/apps.py``:
  * Add ``'apps.dbcleanup'`` as new line in the file

## Update plugin
* ``cd pyplanet/apps/dbcleanup``
* ``git pull``
* Restart PyPlanet

## Plugin commands
* `//db clean` or `//database clean` - starts the database clean-up (provides an overview of maps to be cleaned)

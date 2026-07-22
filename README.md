# canipypi

Check whether PyPI will accept a project name.

## Usage

```console
$ canipypi unicodemath requests
unicodemath: appears available
requests: conflicts with existing project 'requests'
```

Several names are checked with a single download of the PyPI index. The command exits with status 0 when every name appears available, 1 when a public PyPI rule rejects any of them, and 2 when PyPI cannot be queried.

`pypi_names` caches its download for the life of the process, so repeated `check_name` calls share one fetch of the PyPI index; an explicit project-name collection can also be passed:

```python
from canipypi import check_name, pypi_names

projects = pypi_names()
result = check_name('unicodemath', projects)
result.available
```

`canipypi` checks project-name syntax, conflicts with Python standard-library modules, standard PyPI name normalization, and Warehouse's stricter similarity normalization.

PyPI's explicit prohibited-name list is private. An available result is therefore not a guarantee, and another user may register the name before you do.

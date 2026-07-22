import argparse
from dataclasses import dataclass
from functools import cache
from itertools import chain

import httpx, stdlib_list
from packaging.utils import InvalidName, canonicalize_name

_SIMPLE_URL = 'https://pypi.org/simple/'
_SIMPLE_ACCEPT = 'application/vnd.pypi.simple.v1+json'
_ULTRA_TRANS = str.maketrans({'.': None, '_': None, '-': None, 'i': '1', 'l': '1', 'o': '0'})

def _namespace_stdlib_list(module_list):
    for module_name in module_list:
        parts = module_name.split(".")
        for i, _ in enumerate(parts):
            yield ".".join(parts[: i + 1])

_STDLIB_NAMES = {
    canonicalize_name(s.rstrip("-_.").lstrip("-_."))
    for s in chain.from_iterable(
        _namespace_stdlib_list(stdlib_list.stdlib_list(version))
        for version in stdlib_list.short_versions
    )
}


@dataclass(frozen=True)
class NameCheck:
    name: str
    reason: str | None = None
    conflict: str | None = None

    @property
    def available(self): return self.reason is None


def ultranormalize(name):
    "Apply Warehouse's extra normalization for confusable project names."
    return name.lower().translate(_ULTRA_TRANS)


@cache
def pypi_names():
    "Return all registered project names from PyPI."
    response = httpx.get(_SIMPLE_URL, headers={'Accept': _SIMPLE_ACCEPT}, follow_redirects=True, timeout=30)
    response.raise_for_status()
    return [project['name'] for project in response.json()['projects']]


def check_name(name, projects=None):
    "Check a project name against the public rules enforced by PyPI."
    try: normalized = canonicalize_name(name, validate=True)
    except InvalidName: return NameCheck(name, 'invalid')

    if normalized in _STDLIB_NAMES: return NameCheck(name, 'stdlib')
    if projects is None: projects = pypi_names()

    similar = None
    ultranormalized = ultranormalize(name)
    for project in projects:
        if canonicalize_name(project) == normalized: return NameCheck(name, 'existing', project)
        if similar is None and ultranormalize(project) == ultranormalized: similar = project
    if similar is not None: return NameCheck(name, 'similar', similar)
    return NameCheck(name)


def _message(result):
    if result.available: return f'{result.name}: appears available'
    if result.reason == 'invalid': return f'{result.name}: invalid project name'
    if result.reason == 'stdlib': return f'{result.name}: conflicts with a Python standard-library module'
    return f'{result.name}: {"conflicts with" if result.reason == "existing" else "is too similar to"} existing project {result.conflict!r}'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Check whether PyPI will accept a project name.')
    parser.add_argument('names', nargs='+', metavar='name')
    args = parser.parse_args(argv)
    ok = True
    for name in args.names:
        try: result = check_name(name)
        except httpx.HTTPError as error: parser.exit(2, f'canipypi: PyPI request failed: {error}\n')
        print(_message(result))
        ok = ok and result.available
    return int(not ok)

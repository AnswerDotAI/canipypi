"""PyPI release sizes and authenticated release deletion."""
import json

import httpx
from packaging.utils import canonicalize_name
from packaging.version import Version


def release_sizes(project):
    "Return the uploaded bytes for each release of a PyPI project."
    project = canonicalize_name(project, validate=True)
    response = httpx.get(f'https://pypi.org/pypi/{project}/json')
    response.raise_for_status()
    return {version: sum(f['size'] for f in files) for version, files in response.json()['releases'].items()}


_DELETE_RELEASE = r'''async ({project, version}) => {
    if (location.origin !== 'https://pypi.org') throw new Error('Use a browser tab logged into https://pypi.org');
    const listing = `/manage/project/${encodeURIComponent(project)}/releases/`;
    const target = `/manage/project/${encodeURIComponent(project)}/release/${encodeURIComponent(version)}/`;
    const parse = html => new DOMParser().parseFromString(html, 'text/html');
    const find = doc => [...doc.forms].find(f => f.getAttribute('action') === target && f.elements.namedItem('confirm_delete_version'));
    const initial = await fetch(listing);
    if (!initial.ok) throw new Error(`Cannot read ${project} releases: HTTP ${initial.status}`);
    const form = find(parse(await initial.text()));
    if (!form) throw new Error(`No delete form for ${project} ${version}; check the release and your PyPI login`);
    for (const input of form.querySelectorAll('input[type="checkbox"]')) input.checked = true;
    form.elements.namedItem('confirm_delete_version').value = version;
    const response = await fetch(target, {method:'POST', body:new URLSearchParams(new FormData(form))});
    const remaining = parse(await response.text());
    if (!response.ok || new URL(response.url).pathname !== listing || find(remaining))
        throw new Error(`Deletion failed for ${project} ${version}: HTTP ${response.status}; check your PyPI login`);
    return version;
}'''


async def delete_release(
    page, # A fastcdp Page logged into PyPI
    project, # Project name
    version, # Release version to permanently delete
):
    "Permanently delete one release and verify its removal."
    args = json.dumps({'project': canonicalize_name(project, validate=True), 'version': version})
    return await page.eval(f'({_DELETE_RELEASE})({args})')


async def prune_releases(page, project, keep=5):
    "Permanently delete older releases, retaining the newest `keep` versions."
    if keep < 1: raise ValueError('keep must be at least 1')
    versions = sorted(release_sizes(project), key=Version)
    return [await delete_release(page, project, version) for version in versions[:-keep]]

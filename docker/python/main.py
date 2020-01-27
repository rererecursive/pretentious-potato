#!/usr/bin/python3
import json
import re
import requests
import sys
from tqdm import tqdm


"""
1. Parse the requirements file
2. For each package, pull the latest version
3. Compare the versions:
    3a. Print the packages that are latest in one block.
    3b. Print the packages with newer versions in another block.
"""

def get_package_names(filename, packages_to_ignore):
    packages = []

    with open(filename) as fh:
        contents = sorted(fh.readlines())
        contents = list(filter(lambda l: not l.strip().startswith('#'), contents))

    if packages_to_ignore:
        packages_to_ignore = sorted(packages_to_ignore.split('|'))
        print("Ignoring packages:", packages_to_ignore)
        contents = list(filter(lambda l: l not in packages_to_ignore, contents))

    for i, line in enumerate(contents):
        package = re.split('<=|>=|==', line.strip())
        packages.append({'name': package[0], 'current': package[1]})

    return packages


def pull_package_versions(package_name):
    url = "https://pypi.python.org/pypi/%s/json" % package_name
    response = requests.get(url)
    contents = json.loads(response.content)
    versions = sorted(list(contents["releases"].keys()), reverse=True)

    return versions[0]


def get_longest_name(packages):
    # For formatting purposes
    names = [p['name'] for p in packages]
    longest_name = sorted(names, key=len, reverse=True)[0]
    return len(longest_name) + 1


def get_longest_current_version(packages):
    # For formatting purposes
    names = [p['current'] for p in packages]
    longest_name = sorted(names, key=len, reverse=True)[0]
    return len(longest_name)


def get_version(package):
    def tryint(x):
        try:
            return int(x)
        except ValueError:
            return x

    return tuple(tryint(x) for x in re.split('([0-9]+)', package))

def main():
    file = sys.argv[1].split('=')[1]
    package_type = sys.argv[2].split('=')[1]
    ignore = sys.argv[3].split('=')[1]

    packages = get_package_names(file, ignore)

    print("Fetching version information for %d packages..." % len(packages))
    for package in tqdm(packages):
        latest = pull_package_versions(package['name'])
        package['latest'] = latest

    available_packages = list(filter(lambda p: get_version(p['current']) < get_version(p['latest']), packages))
    latest_packages = list(filter(lambda p: get_version(p['current']) >= get_version(p['latest']), packages))

    longest_name_length = get_longest_name(packages)
    longest_current_version = get_longest_current_version(packages)

    if available_packages:
        print('\nAvailable:')

        for package in available_packages:
            print('  {:{}} {:{}} =>  {}'.format(package['name'], longest_name_length, package['current'], longest_current_version, package['latest']))

    if latest_packages:
        print('\nLatest [OK]:')

        for package in latest_packages:
            print('  {:{}} {}'.format(package['name'], longest_name_length, package['latest']))

    # TODO: support 'ignore'
    # TODO: write the 'latest' version to /tmp, and use it if specified in the config
    with open('/tmp/' + file, 'w') as fh:
        for p in packages:
            fh.write('%s==%s\n' % (p['name'], p['latest']))

    print('\nWrote latest package versions to: /tmp/%s' % file)

main()

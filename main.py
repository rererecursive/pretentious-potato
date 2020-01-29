#!/usr/bin/python3
import re
import sys
import tqdm

from handlers import PipHandler, CrateHandler, NpmHandler, GemHandler

"""
1. Read the packages file
2. For each package, pull its latest version number
3. Compare the versions:
    3a. Print the packages that are 'latest' in one block.
    3b. Print the packages with newer versions in another block.
"""

def main():
    handler = get_handler(sys.argv)
    packages = handler.read_packages_from_file()

    print("Fetching version information for %d packages..." % len(packages))
    for package in tqdm.tqdm(packages):
        latest = handler.pull_latest_version(package['name'])
        package['latest'] = latest

    available_packages = list(filter(lambda p: get_version(p['current']) < get_version(p['latest']), packages))
    latest_packages = list(filter(lambda p: get_version(p['current']) >= get_version(p['latest']), packages))

    longest_name_length = get_longest_name(packages)
    longest_current_version = get_longest_current_version(packages)

    # TODO: add the time the new package was added (e.g. '2 months ago')
    if available_packages:
        print('\nAvailable:')

        for package in available_packages:
            print('  {:{}} {:{}} =>  {}'.format(package['name'], longest_name_length, package['current'], longest_current_version, package['latest']))

    if latest_packages:
        print('\nLatest [OK]:')

        for package in latest_packages:
            print('  {:{}} {}'.format(package['name'], longest_name_length, package['latest']))

    handler.write_packages_to_file(packages)
    print('\nWrote latest package versions to: %s' % handler.get_destination())


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


def get_handler(user_args):
    file = sys.argv[1].split('=')[1]
    package_type = sys.argv[2].split('=')[1]
    to_ignore = sys.argv[3].split('=')[1]
    overwrite = sys.argv[4].split('=')[1]

    if to_ignore:
        to_ignore = to_ignore.split('|')
    else:
        to_ignore = []

    if overwrite.lower() == 'true':
        overwrite = True
    else:
        overwrite = False

    types = ['pip', 'gem', 'crate', 'npm']
    params = {'filename': file, 'packages_to_ignore': to_ignore, 'overwrite': overwrite}

    if package_type == 'pip':
        return PipHandler(**params, url='https://pypi.python.org/pypi/[PKG]/json')
    if package_type == 'gem':
        return GemHandler(**params, url='https://rubygems.org/api/v1/gems/[PKG].json')
    if package_type == 'crate':
        return CrateHandler(**params, url='https://crates.io/api/v1/crates/[PKG]')
    if package_type == 'npm':
        return NpmHandler(**params, url='https://api.npms.io/v2/package/[PKG]')

    # TODO: proper error
    print("ERROR: unsupported package type '%s'. Available types: %s" % (package_type, types), file=sys.stderr)
    exit(1)

main()

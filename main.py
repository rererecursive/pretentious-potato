#!/usr/bin/python3
import json
import re
import requests
import sys
import toml
import tqdm


"""
1. Parse the requirements file
2. For each package, pull the latest version
3. Compare the versions:
    3a. Print the packages that are latest in one block.
    3b. Print the packages with newer versions in another block.
"""

def pull_nodejs_versions(package_name):
    url = "https://api.npms.io/v2/package/%s" % package_name
    response = requests.get(url)
    contents = json.loads(response.content)
    version = contents['collected']['metadata']['version']

    return version

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

    if package_type == 'pip':
        return PipHandler(filename=file, packages_to_ignore=to_ignore, url='https://pypi.python.org/pypi/[PKG]/json')
    if package_type == 'gem':
        return GemHandler(filename=file, packages_to_ignore=to_ignore, url='https://rubygems.org/api/v1/gems/[PKG].json')
    if package_type == 'crate':
        return CrateHandler(filename=file, packages_to_ignore=to_ignore, url='https://crates.io/api/v1/crates/[PKG]')

# TODO:
#   - package reader
#   - package puller
#   - package installer
#   - package writer

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

    if available_packages:
        print('\nAvailable:')

        for package in available_packages:
            print('  {:{}} {:{}} =>  {}'.format(package['name'], longest_name_length, package['current'], longest_current_version, package['latest']))

    if latest_packages:
        print('\nLatest [OK]:')

        for package in latest_packages:
            print('  {:{}} {}'.format(package['name'], longest_name_length, package['latest']))

    handler.write_packages_to_file(packages)
    print('\nWrote latest package versions to: /tmp/%s' % handler.filename)

class PackageHandler:
    def __init__(self, filename, packages_to_ignore, url):
        self.filename = filename
        self.packages_to_ignore = packages_to_ignore
        self.url = url

    def read_packages_from_file(self):
        pass

    def pull_latest_version(self, package_name):
        pass

    def pull_package_info(self, package_name):
        url = self.url.replace('[PKG]', package_name)
        response = requests.get(url)
        return json.loads(response.content)

    def write_packages_to_file(self, packages):
        pass


class PipHandler(PackageHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read_packages_from_file(self):
        packages = []

        with open(self.filename) as fh:
            contents = sorted(fh.readlines())
            contents = list(filter(lambda l: not l.strip().startswith('#'), contents))

        if self.packages_to_ignore:
            packages_to_ignore = sorted(self.packages_to_ignore.split('|'))
            print("Ignoring packages:", packages_to_ignore)
            contents = list(filter(lambda l: l not in packages_to_ignore, contents))

        for line in contents:
            package = re.split('<=|>=|==', line.strip())
            packages.append({'name': package[0], 'current': package[1]})

        return packages

    def pull_latest_version(self, package_name):
        info = self.pull_package_info(package_name)
        return sorted(list(info['releases'].keys()), reverse=True)[0]

    def write_packages_to_file(self, packages):
        with open('/tmp/' + self.filename, 'w') as fh:
            for p in packages:
                fh.write('%s==%s\n' % (p['name'], p['latest']))


class GemHandler(PackageHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def pull_latest_version(self, package_name):
        info = self.pull_package_info(package_name)
        return info['version']

    def read_packages_from_file(self):
        packages = []

        with open(self.filename) as fh:
            self.contents = fh.readlines()
            contents = sorted(self.contents)
            contents = list(filter(lambda l: l.strip().startswith('gem'), contents))

        if self.packages_to_ignore:
            packages_to_ignore = sorted(self.packages_to_ignore.split('|'))
            print("Ignoring packages:", packages_to_ignore)
            contents = list(filter(lambda l: l not in packages_to_ignore, contents))

        for line in contents:
            package = line.split()
            if len(package) < 3:
                version = 'None'   # TODO: this needs to be put into the 'Available' list
            else:
                version = package[2]

            pattern = "('|~|>|,)"
            packages.append({'name': re.sub(pattern, '', package[1]), 'current': re.sub(pattern, '', version)})

        return packages

    def write_packages_to_file(self, packages):
        contents = self.contents

        for i, line in enumerate(contents):
            tokens = line.strip().split()

            if not tokens or not tokens[0] == 'gem':
                continue

            for p in packages:
                if p['name'] == re.sub("('|~|>|,)", '', tokens[1]):
                    # Overwrite the version with the latest
                    try:
                        tokens[2] = "'%s'\n" % p['latest']
                    except IndexError:
                        tokens[1] += ','
                        tokens.append("'%s'\n" % p['latest'])

                    break

            line = " ".join(tokens)
            contents[i] = line

        with open('/tmp/' + self.filename, 'w') as fh:
            fh.write(''.join(contents))


class CrateHandler(PackageHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read_packages_from_file(self):
        packages = []

        with open(self.filename) as fh:
            self.contents = toml.load(fh)
            contents = self.contents['dependencies']

        if self.packages_to_ignore:
            packages_to_ignore = sorted(self.packages_to_ignore.split('|'))
            print("Ignoring packages:", packages_to_ignore)

            for p in packages_to_ignore:
                contents.pop(p)

        for key, value in contents.items():
            if type(value) == str:
                packages.append({'name': key, 'current': value.replace('^', '')})
            elif type(value) == dict:
                packages.append({'name': key, 'current': value['version'].replace('^', '')})

        return packages

    def pull_latest_version(self, package_name):
        info = self.pull_package_info(package_name)
        return info['crate']['newest_version']

    def write_packages_to_file(self, packages):
        for p in packages:
            original_val = self.contents['dependencies'][p['name']]

            if type(original_val) == str:
                self.contents['dependencies'][p['name']] = p['latest']
            elif type(original_val) == dict:
                self.contents['dependencies'][p['name']]['version'] = p['latest']

        with open('/tmp/' + self.filename, 'w') as fh:
            toml.dump(self.contents, fh)

main()

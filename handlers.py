import json
import re
import requests
import toml

class PackageHandler:
    def __init__(self, filename, packages_to_ignore, url, overwrite):
        self.filename = filename
        self.packages_to_ignore = sorted(packages_to_ignore)
        self.url = url
        self.overwrite = overwrite

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

    def get_destination(self):
        if self.overwrite:
            return self.filename
        else:
            return '/tmp/' + self.filename


class PipHandler(PackageHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read_packages_from_file(self):
        packages = []

        with open(self.filename) as fh:
            contents = sorted(fh.readlines())
            contents = list(filter(lambda l: not l.strip().startswith('#'), contents))

        if self.packages_to_ignore:
            print("Ignoring packages:", self.packages_to_ignore)
            contents = list(filter(lambda l: l not in self.packages_to_ignore, contents))

        for line in contents:
            package = re.split('<=|>=|==', line.strip())
            packages.append({'name': package[0], 'current': package[1]})

        return packages

    def pull_latest_version(self, package_name):
        info = self.pull_package_info(package_name)
        return sorted(list(info['releases'].keys()), reverse=True)[0]

    def write_packages_to_file(self, packages):
        with open(self.get_destination(), 'w') as fh:
            for p in packages:
                fh.write('%s==%s\n' % (p['name'], p['latest']))


class NpmHandler(PackageHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read_packages_from_file(self):
        with open(self.filename) as fh:
            self.contents = json.load(fh)
            contents = self.contents['dependencies']

        # ...
        if self.packages_to_ignore:
            print("Ignoring packages:", self.packages_to_ignore)

            for p in self.packages_to_ignore:
                contents.pop(p)

        return [{'name': k, 'current': v.replace('^', '')} for k,v in contents.items()]


    def pull_latest_version(self, package_name):
        info = self.pull_package_info(package_name)
        return info['collected']['metadata']['version']

    def write_packages_to_file(self, packages):
        # Overwrite the version with the latest
        for p in packages:
            self.contents['dependencies'][p['name']] = p['latest']

        with open(self.get_destination(), 'w') as fh:
            json.dump(self.contents, fh, indent=2)


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
            print("Ignoring packages:", self.packages_to_ignore)
            contents = list(filter(lambda l: l not in self.packages_to_ignore, contents))

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

        with open(self.get_destination(), 'w') as fh:
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
            print("Ignoring packages:", self.packages_to_ignore)

            for p in self.packages_to_ignore:
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

        with open(self.get_destination(), 'w') as fh:
            toml.dump(self.contents, fh)

/*

Get the latest versions for a set of packages.
This only downloads the latest version string; it does not download the package itself.

Usage:

getLatestPackages(
    file: 'requirements.txt'
    type: 'pip',
    [ignore]: ['awscli', 'numpy'],
    [overwrite]: true | [false]     // Overwrite the dependency file with the latest versions,
    [ignoreVersions]: ['minor', 'patch']   // TODO: ignore types of versions (in semver)
)

*/

def call(config) {
    def ignore = config.get('ignore', []).join('|')
    def overwrite = config.get('overwrite', '')

    docker.image('rererecursive/latest-packages').inside('-v $PWD:/app') {
        sh "python3 main.py file=${config.file} type=${config.type} ignore=${ignore} overwrite=${overwrite}"
    }
}

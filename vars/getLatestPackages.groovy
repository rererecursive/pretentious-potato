/*
We need a way to collect and install the latest packages.
Installing is a desired feature so that we can test if the packages actually build.

    getLatestPackages(
        file: 'requirements.txt'
        type: 'pip',
        runtime: 'python3.8',
        [install]: true | [false],
        [installPath]: '/home/jenkins/.local/lib/python3.8/site-packages/', // The local path to install packages to. Default: cwd
        [ignore]: ['awscli', 'numpy']
    )
*/

def call(config) {
    def installPath = config.get('installPath', '/tmp')
    def ignore = config.get('ignore', []).join('|')
    def volumeMounts = "-v $PWD:/app"

    if (config.installPath) {
        volumeMounts += " -v ${installPath}:/host"
    }

    docker.image('rererecursive/latest-packages').inside(volumeMounts) {
        sh "python3 main.py file=${config.file} type=${config.type} ignore=${ignore}"

        if (config.install) {
            sh "./install.sh -f ${config.file} -t ${config.type} -p ${config.installPath}"
        }
    }
}

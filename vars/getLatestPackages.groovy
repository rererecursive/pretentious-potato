/*
    getLatestPackages(
        file: 'requirements.txt'
        type: 'pip',
        runtime: 'python3.8',
        [installPath]: '/home/jenkins/.local/lib/python3.8/site-packages/',
        [debug]: true | [false],
        [ignore]: ['awscli', 'numpy']
    )
*/

def call(config) {
    def installPath = config.get('installPath', '/tmp')
    def ignore = config.get('ignore', []).join('|')

    docker.image('rererecursive/latest-packages').inside("-v ${installPath}:/host -v $PWD:/app") {
        sh "python3 main.py file=${config.file} type=${config.type} ignore=${ignore}"

        if (config.installPath) {
            sh "./install.sh -f ${config.file} -t ${config.type}"
        }
    }
}

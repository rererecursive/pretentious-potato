#!/bin/sh

# ./install.sh -f requirements.txt -t pip -p path

while getopts f:t:p: opts; do
    case ${opts} in
        f) FILE=${OPTARG} ;;
        t) TYPE=${OPTARG} ;;
        p) MOUNTED_PATH=${OPTARG} ;;
    esac
done

LOCATION="/tmp/$FILE"
echo "Installing packages specified in: $LOCATION"
cp $LOCATION .

if [ $TYPE = "pip" ]; then
    pip3 install -r $FILE
    PACKAGE_PATH="/home/myuser/.local/lib/python3.8/site-packages"

elif [ $TYPE = "npm" ]; then
    npm --prefix /tmp install
    PACKAGE_PATH="tmp/node_modules"

elif [ $TYPE = "crate" ]; then
    cargo build

elif [ $TYPE = "gem" ]; then
    bundle config set path '/tmp'
    bundler install
fi

# Copy the packages to the mounted directory
if [ -n $MOUNTED_PATH ]; then
    echo "Copying packages to mounted volume..."
    cp -r $PACKAGE_PATH /host
fi

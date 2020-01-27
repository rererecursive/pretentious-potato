#!/bin/sh

# ./install.sh -f requirements.txt -t pip

while getopts f:t: opts; do
   case ${opts} in
      f) FILE=${OPTARG} ;;
      t) TYPE=${OPTARG} ;;
   esac
done

LOCATION="/tmp/$FILE"
echo "Installing packages specified in: $LOCATION"

if [ $TYPE = "pip" ]; then
    pip3 install -r $LOCATION
    cp -r /home/myuser/.local/lib/python3.8/site-packages/ /host
fi

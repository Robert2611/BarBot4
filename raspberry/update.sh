#!/bin/bash
# find the latest release
url=$(curl -s "https://api.github.com/repos/Robert2611/BarBot4/releases/latest" \
	| grep "/raspberry.tar.gz"\
	| cut -d : -f 2,3 \
	| tr -d \" \
)
# delete all the content of "barbot" including this file
rm -r ~/barbot/*
# download and extract new files
curl -s -L $url | tar xvz -C ~/barbot/
# call the install script 
sh ~/barbot/install.sh
#!/bin/bash
echo "Bitte GitHub token eingeben!"
read token
list=$(curl -s\
	-H "Accept: application/vnd.github+json" \
	-H "Authorization: token $token" \
	"https://api.github.com/repos/Robert2611/BarBot4/releases/latest")
url=$(echo $list | jq -r '.assets[] | select(.name=="raspberry.tar.gz") | .url')
echo "Lade letztes release herunter"
curl -Ls\
	-H "Accept: application/octet-stream" \
  	-H "Authorization: token $token" \
	$url \
	-o raspberry.tar.gz
echo "Entpacke..."
tar xvf raspberry.tar.gz
rm raspberry.tar.gz
echo "Update erfolgreich!"
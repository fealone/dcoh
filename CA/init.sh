#!/bin/bash -e
mkdir exts
mkdir certs
mkdir csreq
mkdir demoCA
mkdir demoCA/certs
mkdir demoCA/private
mkdir demoCA/crl
mkdir demoCA/newcerts
chmod 700 demoCA/private
openssl rand -hex 16 > demoCA/serial
touch demoCA/index.txt

openssl req -new -x509 -newkey rsa:4096 -out demoCA/cacert.pem -keyout demoCA/private/cakey.pem -days 3650 -nodes
chmod 600 demoCA/private/cakey.pem
openssl x509 -in demoCA/cacert.pem -text

openssl x509 -inform PEM -outform DER -in demoCA/cacert.pem -out demoCA/cacert.der

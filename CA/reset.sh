#!/bin/bash -e
rm -rf certs/*
rm -rf csreq/*
rm -rf exts/*
rm demoCA/index.txt
touch demoCA/index.txt
openssl rand -hex 16 > demoCA/serial

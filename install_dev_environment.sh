#!/usr/bin/env bash
#encoding=utf8

echo "mcDuck broker freqtrade dev installation"
echo "Making sure dev environment is clean"

rm -rf dev

echo "cloning freqtrade into dev folder"
git clone https://github.com/freqtrade/freqtrade.git dev

cd dev

git checkout stable


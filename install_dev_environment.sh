#!/usr/bin/env bash
#encoding=utf8

function echo_text(){
    tput bold; tput setaf 3; tput setab 0; echo $1; tput sgr0;
}

tput clear;

echo "====================================="
echo_text "mcDuck broker freqtrade dev installation"
echo "====================================="
echo_text "Strategies and configs and scripts will be inside user_data"
echo "";
echo_text "Making sure dev environment is clean"

rm -rf dev

echo_text "Cloning freqtrade into dev folder"
git clone https://github.com/freqtrade/freqtrade.git dev

echo_text "Creating link for strategies"
rm -rf dev/user_data
ln -sr user_data dev/
ln -sr scripts/debug.sh dev/debug.sh
cd dev

git checkout stable

echo_text "Strating freqtrade install script"
./setup.sh -i

#!/usr/bin/env bash

pacman -Syu
pacman -S --noconfirm wget python python-pip nmap python-django sqlite
mkdir Downloads
cd Downloads
wget https://aur.archlinux.org/packages/li/libspotify/libspotify.tar.gz
tar xf libspotify.tar.gz
cd libspotify
makepkg --asroot
pacman -U --noconfirm libspotify-12.1.51-2-x86_64.pkg.tar.xz
pip install --pre pyspotify
cd /vagrant
pip install -r requirements.txt

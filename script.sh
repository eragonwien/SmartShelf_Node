#!/bin/sh
git fetch
git reset --hard && echo "updated"
sudo reboot now
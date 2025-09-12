#!/bin/bash

git stash
git pull
sudo systemctl restart smokeking.in.service

#!/bin/bash
docker pull lfenergy/arras:latest
docker save -o images/arras_latest.tar lfenergy/arras:latest
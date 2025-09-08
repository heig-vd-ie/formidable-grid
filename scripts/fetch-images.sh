#!/bin/bash
docker pull slacgismo/gridlabd:latest
docker save -o images/gridlabd_latest.tar slacgismo/gridlabd:latest
docker pull lfenergy/arras:latest
docker save -o images/arras_latest.tar lfenergy/arras:latest
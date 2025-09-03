#!/bin/bash
docker pull slacgismo/gridlabd:latest
docker save -o images/gridlabd_latest.tar slacgismo/gridlabd:latest
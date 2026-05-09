#!/usr/bin/env bash

## This tests the motion of one object from an inkscape file with
##   multiple objects

# Testing transforming a group
python renderer.py \
       --scene Assets/robotConcept.svg \
       --output Output/robotConcept.mp4 \
       --duration $((30))

# Testing overlay ed transparencies
python renderer.py \
       --scene Assets/inkscapeTest001.svg \
       --output Output/inkscapeTest.mp4 \
       --duration $((30))

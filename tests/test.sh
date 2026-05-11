#!/usr/bin/env bash

## This tests the motion of one object from an inkscape file with
##   multiple objects

mkdir -p Output

# Testing transforming a group
python src/animation_builder/main.py \
       --scene Assets/robotConcept.svg \
       --output Output/robotConcept.mp4 \
       --duration $((30))

# Testing overlay ed transparencies
python src/animation_builder/main.py \
       --scene Assets/inkscapeTest001.svg \
       --output Output/inkscapeTest.mp4 \
       --duration $((30))

# Add transparency to the robotConcept file
ffmpeg -i Output/robotConcept.mp4 -vf "colorkey=black:0.3:0.1,crop=iw:ih:0:0" -c:v prores_ks -profile:v 4 -pix_fmt yuva444p10le -c:a copy Output/logo.mov

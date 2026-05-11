#!/usr/bin/env bash

## Creates the starting_soon.mp4 from the starting_soon.svg example
## You can use this file as a template for constructing other examples

mkdir -p Output

python src/animation_builder/main.py \
       --scene Examples/starting_soon.svg \
       --output Output/starting_soon.mp4 \
       --duration $((5*60+30))

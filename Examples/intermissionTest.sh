#!/usr/bin/env bash

## Creates the starting_soon.mp4 from the starting_soon.svg example
## You can use this file as a template for constructing other examples

mkdir -p Output

python src/animation_builder/main.py \
       --scene Examples/intermission.svg \
       --output Output/intermission.mp4 \
       --duration $((30))

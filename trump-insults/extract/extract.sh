#!/usr/bin/env bash

source activate blog

python extract_insults.py --path data
python extract_tweets.py --path data


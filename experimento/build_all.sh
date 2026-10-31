#!/usr/bin/env bash
set -e
for rt in go node python java; do
  for wl in minimal deps; do
    sudo docker build --build-arg WORKLOAD=$wl -t exp-$rt-$wl apps/$rt
  done
done
sudo docker images --format 'table {{.Repository}}\t{{.Size}}' | grep exp-
#!/bin/bash
# date 2019-11-22 18:25:05
# author calllivecn <calllivecn@outlook.com>

#docker images |awk '{if($1 == "<none>" && $2 == "<none>") print $3}' |xargs -n 64 docker rmi

podman images |awk '{if($1 == "<none>" && $2 == "<none>") print $3}' |xargs -n 64 podman rmi


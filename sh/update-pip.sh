#!/bin/bash
# date 2018-11-28 11:44:33
# author calllivecn <c-all@qq.com>

set -xe

PIP="pip3"

for pip in $($PIP list --user --not-required --format freeze |awk -F'=' '{print $1}')
do
	$PIP install --user --upgrade "$pip"
done

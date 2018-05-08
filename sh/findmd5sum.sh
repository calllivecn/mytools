#!/bin/sh

find -type f -print0 |xargs -0 md5sum |grep -v md5sum.txt |tee md5sum.txt

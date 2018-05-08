#!/bin/bash


AUTOSH=~/bin/autostart

[ -d $AUTOSH ] || exit 1

for sh in $AUTOSH/*.sh
do
	bash $sh &
done



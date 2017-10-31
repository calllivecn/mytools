#!/bin/bash
# date 2017-10-31 22:08:50
# author calllivecn <c-all@qq.com>

grub-install --target i386-pc \
--recheck \
--boot-directory /tmp/grub/

grub-install --target x86_64-efi \
--efi-directory /tmp/grub/ \
--boot-directory /tmp/grub/ \
--removable

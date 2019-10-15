#!/usr/bin/env python3
# coding=utf-8
# date 2017-11-03 23:27:01
# author calllivecn <c-all@qq.com>


import sys
import termios
import os
import copy
########################
#
# define global variable
#
#######################
base_dir = '/sys/class/backlight/'
current_light_f = '/brightness'
max_light_f = '/max_brightness'
actual_light_f = '/actual_brightness'

video = ''
videos = []

#####################
#
# check root
#
####################
if os.geteuid() != 0:
    print("need the root user.")
    sys.exit(1)

#######################
#
# define functions
#
########################


def usage():
    print("'k' or '↑ ' up adjustment 'j' or '↓ ' down adjustemnt")
    print("'q' or 'ESC' quit")


def video_list():
    return os.listdir(base_dir)


def input_check(lenght):

    while True:
        try:
            n = int(input('select your video [1-{}] :'.format(lenght)))
        except ValueError as e:
            print('please input number [1-{}]'.format(lenght))
            continue
        except KeyboardInterrupt:
            print()
            sys.exit(0)
        if n < 1 or n > lenght:
            print('please input number [1-{}]'.format(lenght))
            continue

        break

    return n


def select_video(videos):
    lenght = len(videos)

    for i in range(lenght):
        print(i+1, ') ', videos[i], sep='')

    n = input_check(lenght)
    return videos[n - 1]


def check_overflow(value, max_v, min_v=0):
    if value < min_v:
        return min_v
    elif value > max_v:
        return max_v
    else:
        return value


def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    new_settings = copy.deepcopy(old_settings)
    new_settings[3] &= ~(termios.ICANON | termios.ECHO)  # | termios.ISIG)
    #new_settings[6][termios.VMIN] = 1
    #new_settings[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)
    try:
        ch = os.read(fd, 8)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return ch


def read_light(video):
    with open(base_dir + video + max_light_f) as fd1, open(base_dir + video + current_light_f) as fd2:
        max_light = int(fd1.read())
        current_light = int(fd2.read())

    step = (max_light-1)//30
    return max_light, current_light, step


def change_light(value, video):
    with open(base_dir + video + current_light_f, 'r+') as fd:
        fd.write(str(value))


def main():
    videos = video_list()

    if len(videos) == 1:
        video = video_list()[0]
    elif len(video) > 1:
        video = select_video(videos)
    elif len(videos) < 1:
        print('not found display device.')
        sys.exit(0)

    max_light, current_light, step = read_light(video)

    usage()
    out_lenght = len(str(max_light))
    while True:
        print('\r', "current brightness: ", ' '*out_lenght, '\b' *
              out_lenght, current_light, sep='', end='', flush=True)
        ch = getch()
        if ch == b'j' or ch == b'\x1b[B':
            current_light = check_overflow(current_light - step, max_light)
            change_light(current_light, video)
        elif ch == b'k' or ch == b'\x1b[A':
            current_light = check_overflow(current_light + step, max_light)
            change_light(current_light, video)
        elif ch == b'\x1b' or ch == b'q':
            print('\nexit...')
            sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# coding=utf-8
# date 2018-01-31 20:59:21
# author calllivecn <calllivecn@outlook.com>

import re
import sys
import wave
import logging
from os import path
from base64 import encodebytes, decodebytes
from selectors import DefaultSelector, EVENT_READ

import libevdev as ev
from libevdev import (
        Device,
        InputEvent,
        evbit,
        )
import pyaudio


def getlogger(level=logging.DEBUG):
    fmt = logging.Formatter(
        "%(asctime)s %(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    logger = logging.getLogger("AES")
    logger.setLevel(level)
    logger.addHandler(stream)
    return logger


logger = getlogger()



class Play:
    def __init__(self, wave_file):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000

        self.pa = pyaudio.PyAudio()
        self.__readWave(wave_file)

        logger.debug(f"self.pa info: {self.pa}")

        self.stream = self.pa.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            output=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self.callback)

    def callback(self, in_data, frames_count, time_info, status):
        self.stream.write(self.WAV_BUFFER)
        return (in_data, pyaudio.paContinue)

    def play(self):
        self.stream.stop_stream()
        data = True
        while data != b'':
            data = self.wf.readframes(self.CHUNK)
            self.stream.write(data)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    def __readWave(self, wave_file):

        with wave.open(wave_file, 'rb') as wf:
            self.FORMAT = self.pa.get_format_from_width(wf.getsampwidth())
            self.CHANNELS = wf.getchannels()
            self.RATE = wf.getframerate()

            wav_fp = wf.getfp()
            self.WAV_BUFFER = wav_fp.read()


class TouchKey:
    '''
    touchkey = TouchKey()
    touchkey.start()
    '''

    def __init__(self, keyboard=None):

        self.keyboards = []

        if keyboard is None:
            self.getKeyboard()
        else:
            self.keyboards.append(keyboard)

        self.selector = DefaultSelector()

        for kb in self.keyboards:
            self.selector.register(kb, EVENT_READ)

    def start(self, playFunc=None):
        while True:
            for key, mask in self.selector.select():
                dev = key.fileobj
                for event in dev.read():
                    # print(event)
                    if event.value == 1 and event.type == 1:
                        if playFunc is None:
                            print(
                                '按下键', evdev.ecodes.KEY[event.code], 'device:', dev.fn)
                        else:
                            # 播放声音
                            playFunc()

    def __re_true(self, string):
        if len(re.findall(r'keyboard', string, re.I)) >= 1:
            return True
        else:
            return False

    def __getKeyboard(self, baseinput="/dev/input"):
        KEYBOARD = [EV_KEY.KEY_ESC, EV_KEY.KEY_SPACE,
                EV_KEY.KEY_BACKSPACE, EV_KEY.KEY_0,
                EV_KEY.KEY_A, EV_KEY.KEY_Z, EV_KEY.KEY_9, EV_KEY.KEY_F2]

        for dev in os.listdir(baseinput):

            devpath = path.join(baseinput, dev)
            if not path.isdir(devpath):
                devfd = open(devpath, 'rb')
            else:
                continue

            try:
                device = Device(devfd)
            except (OSError, Exception) as e :
                logger.debug("打开 {} 异常：{}".format(dev, e))
                continue
        
            if all(map(device.has, KEYBOARD)):
                logger.info("应该是键盘了: {} 路径：{}".format(device.name, device.fd))
                self.keyboards.append(devpath)
            #else:
                #print("其他输入设备：", device.name, "路径：",device.fd)
        
            devfd.close()

    def audio(self, dev):
        for event in dev.read_loop():
            if event.value == 1 and event.type == 1:
                print('按下键', evdev.ecodes.KEY[event.code], 'device:', dev.fn)

    def detectInputKey(self, dev_keyboards):
        while True:
            select([dev], [], [])
            for event in dev.read():
                print("code:{} value:{}".format(event.code, event.value))


def main():

    #logger.setLevel(logging.DEBUG)

    try:
        play = Play('1.wav')
        touchkey = TouchKey()
        touchkey.start(play.play)
        # touchkey.start()
    finally:
        play.close()


def main2():
    play = Play('1.wav')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("exit")

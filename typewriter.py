#!/usr/bin/env python3
# coding=utf-8
# date 2018-01-31 20:59:21
# author calllivecn <c-all@qq.com>

import re
from selectors import DefaultSelector, EVENT_READ
import wave
from base64 import encodebytes, decodebytes

import evdev
from evdev import InputDevice
import pyaudio


class Play:
    def __init__(self, wave_file):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000

        self._readWave(wave_file)

        self.pa = pyaudio.PyAudio()
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

    def _readWave(self, wave_file):
        with wave.open(wave_file, 'rb') as wf:
            self.FORMAT = self.pa.get_format_from_width(
                wf.getsampwidth())
            self.CHANNELS = wf.getchannels()
            self.RATE = wf.getframerate()

            wav_fp = wf.getfp()
            self.WAV_BUFFER = wav_fp.read()


class TouchKey:
    '''
    touchkey = TouchKey()
    touchkey.start()
    '''

    def __init__(self):
        keyboards = self.checkKeyboard()
        self.selector = DefaultSelector()
        for kb in keyboards:
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

    def checkKeyboard(self):
        keyboards = []
        for dev in [evdev.InputDevice(fn) for fn in evdev.list_devices()]:
            if self.__re_true(dev.name):
                keyboards.append(dev)
        return keyboards

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
        main2()
    except KeyboardInterrupt:
        print("exit")

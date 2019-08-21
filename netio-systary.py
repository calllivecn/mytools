#!/usr/bin/env python3
# coding=utf-8
# date 2018-03-12 16:49:03
# author calllivecn <c-all@qq.com>


import os

import gi
# gi.require_version('Gtk','3.0')

from gi.repository import Gtk
from gi.repository import AppIndicator3 as AI3
from gi.repository import Notify

INDICATOR_ID = 'net speed'


def quit(source):
    Notify.uninit()
    Gtk.main_quit()


def notify(_):
    if Notify.init(INDICATOR_ID):
        Notify.Notification.new("网速:", "这是消息", None).show()
    else:
        print('Notify error.')


def menu():
    menu = Gtk.Menu()

    item_notify = Gtk.MenuItem('通知')
    item_notify.connect('activate', notify)
    menu.append(item_notify)

    item_quit = Gtk.MenuItem('退出')
    item_quit.connect('activate', quit)
    menu.append(item_quit)

    menu.show_all()
    return menu


def main():
    #indicator = AI3.Indicator.new(INDICATOR_ID,os.path.abspath('netio-systary.svg'),AI3.IndicatorCategory.SYSTEM_SERVICES)
    indicator = AI3.Indicator.new(
        INDICATOR_ID, 'whatever', AI3.IndicatorCategory.SYSTEM_SERVICES)
    indicator.set_status(AI3.IndicatorStatus.ACTIVE)
    indicator.set_label('label', 'haha')
    # indicator.set_menu(Gtk.Menu())
    indicator.set_menu(menu())
    Gtk.main()


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

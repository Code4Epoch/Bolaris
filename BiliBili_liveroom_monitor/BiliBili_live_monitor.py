# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        BiliBili_liveroom_monitor
# Author:           ydyjya
# Version:          0.3
# Created:          2022/1/16
# Description:      bilibili直播监控存储一体程序入口
# Function List:    read_para(path) --读取参数
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya          0.3             2022/1/16   create
# ------------------------------------------------------------------
from BiliBili_liveroom_monitor import live_monitor
from BiliBili_liveroom_monitor import live_data_stream_decoder
from BiliBili_liveroom_monitor import mysql_for_livestream
from multiprocessing import Process
from multiprocessing import Queue

import json


def read_para(path):
    # 读取本目录下的参数文件
    with open("./%s.json" % path, encoding='utf-8') as config:
        para = json.loads(config.read())

    return para


class BiliBili_liveroom_monitor(object):
    def __init__(self, room_id):

        self.message_queue = Queue()
        self.data_buffer = Queue()
        self.room_id = room_id

        self.my_monitor = live_monitor.BiliBili_live_monitor(room_id=room_id, config=read_para('live_monitor_config'),
                                                             message_queue=self.message_queue)
        self.my_decoder = \
            live_data_stream_decoder.live_data_decoder(buffer=self.data_buffer)
        self.process_list = []

    def process_message(self):
        while True:
            self.my_decoder.decode(self.message_queue.get())

    def mysql_store(self):

        my_mysql = mysql_for_livestream.mysql_for_livestream(config=read_para("mysql_config"),
                                                             room_id=self.room_id)
        while True:
            my_mysql.insert_data(self.data_buffer.get())

    def start(self):
        decoder = Process(target=self.process_message)
        decoder.start()
        monitor = Process(target=self.my_monitor.get_livestream)
        monitor.start()
        mysql_store = Process(target=self.mysql_store)
        mysql_store.start()

        self.process_list.append(monitor)
        self.process_list.append(decoder)
        self.process_list.append(mysql_store)

        for i in self.process_list:
            i.join()
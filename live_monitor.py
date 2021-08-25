# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        live_monitor
# Author:           ydyjya
# Version:          1.0
# Created:          2021/7/9
# Description:      监控b站某直播间（获取部分信息流）并存储到mysql中
# Function List:    bilibili_live_monitor() --监控某直播间的类
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya          1.0             2021/7/9   create
# ------------------------------------------------------------------
from __future__ import unicode_literals

from live import tool_function as tf
from aiowebsocket.converses import AioWebSocket
import asyncio
import json
import pymysql
import time
import zlib


class bilibili_live_monitor(object):
    """
    该类实现了以下几个功能
    1.输入room_id获取该room_id下的直播消息流
    2.将上述消息流存入mysql
    """

    def __init__(self, room_id):
        """
        room_id是string类型
        """
        if type(room_id) == str:
            self.room_id = room_id
        else:
            print("initialize error, please input a string")
            raise ValueError
        self.config = tf.get_config("./config/live_monitor_config/live_monitor_mysql_config.json")
        if len(self.config['medal_room_id']) > 1:
            self.live_monitor_type = 'muti'
            self.medal_list = self.config['medal_room_id']
        elif len(self.config['medal_room_id']) == 1:
            self.live_monitor_type = 'single'
            if self.config['medal_room_id'][0] != room_id:
                print('config error')
                raise ValueError
            else:
                self.medal_list = [room_id]
        else:
            print('medal_list is empty!')
            raise ValueError
        self.data_raw = self.config['bilibili_config']['data_raw'].format(headerLen=hex(27 + len(room_id))[2:],
                                                                          room_id=''.join(
                                                                              map(lambda x: hex(ord(x))[2:],
                                                                                  list(self.room_id))))
        # bilibili的配置
        self.url = self.config['bilibili_config']['remote']
        self.heartbeat = self.config['bilibili_config']['heart_beat']
        self.heartbeat_time = self.config['bilibili_config']['heart_beat_time']
        self.error_time = self.config['bilibili_config']['error_time']
        self.latest_heart_beat_time = time.time()

        # mysql配置
        self.host = self.config['mysql_config']['host']
        self.port = self.config['mysql_config']['port']
        self.user = self.config['mysql_config']['user']
        self.password = self.config['mysql_config']['password']
        self.db = self.config['mysql_config']['db']

        # 弹幕数据库配置
        self.sql_road_dm = self.config['mysql_config']['sql_sentence']['dm_road'] % \
                           (tf.get_time().tm_year, tf.get_time().tm_mon, tf.get_time().tm_mday, self.room_id)
        self.dm_insert_sql_model = "Insert into " + self.sql_road_dm + " " + \
                                   self.config['mysql_config']['sql_sentence']['dm_values']

        self.sql_road_rq = self.config['mysql_config']['sql_sentence']['rq_road'] % \
                           (tf.get_time().tm_year, tf.get_time().tm_mon, tf.get_time().tm_mday, self.room_id)
        self.rq_insert_sql_model = "Insert into " + self.sql_road_rq + " " + \
                                   self.config['mysql_config']['sql_sentence']['rq_values']
        self.mysql_conn = pymysql.connect(host=self.host, port=self.port,
                                          user=self.user, password=self.password, db=self.db)

        # 判断是否开始判断粉丝数据变动
        self.new_fans_flag = 1
        # 开播时的粉丝数据
        self.before_fans = 0
        # 开播时的粉丝团数据
        self.before_medal_fans = 0
        # 上次接收粉丝变动报文时的粉丝数
        self.latest_fans = 0
        # 上次接收粉丝变动报文时的粉丝团数
        self.latest_medal_fans = 0

        # 心跳
        self.latest_heart_beat_time = time.time()

        # 直播间状态判别
        self.live_status = 'preparing'

        # 当前日期值
        self.now_day = tf.get_time().tm_mday

    # 监控直播间
    def live_monitor(self):
        self.__create_dm_sql(table_name=self.sql_road_dm)
        self.__create_rq_sql(table_name=self.sql_road_rq)
        self.mysql_conn.commit()
        try:
            asyncio.get_event_loop().run_until_complete(self.__listen_live_room())
        except KeyboardInterrupt as exc:
            print("Quit.")

    # 根据url进行监听
    async def __listen_live_room(self):
        async with AioWebSocket(self.url) as aws:
            converse = aws.manipulator
            await converse.send(bytes.fromhex(self.data_raw))
            tasks = [self.__rece_data_packet(converse), self.__send_heartbeat(converse, aws)]
            await asyncio.wait(tasks)

    # 发送心跳
    async def __send_heartbeat(self, websocket, aws):
        # 发送一个心跳防止被断开连接
        while True:
            await asyncio.sleep(self.heartbeat_time)
            self.__judge_new_day()
            if time.time() - self.latest_heart_beat_time > self.heartbeat_time + self.error_time:
                tasks = [aws.close_connection(), self.__listen_live_room()]
                self.latest_heart_beat_time = time.time()
                print('[Notice] try reconnect')
                await asyncio.wait(tasks)
                return
            await websocket.send(bytes.fromhex(self.heartbeat))
            print('[Notice] Sent HeartBeat')

    # 接收弹幕
    async def __rece_data_packet(self, websocket):
        while True:
            recv_text = await websocket.receive()
            self.__data2sql(recv_text)

    # 将信息流存入数据库中
    def __data2sql(self, data):
        # 获取包的长度
        packet_len = int(data[:4].hex(), 16)
        # 获取包的ver属性
        ver = int(data[6:8].hex(), 16)
        # 获取包的op属性
        op = int(data[8:12].hex(), 16)
        # 有时存在多个数据包粘连的情况
        while len(data) > packet_len:
            # 调用
            self.__data2sql(data[packet_len:])
            data = data[:packet_len]

        # 如果ver参数为0，op=5说明是普通的通知信息
        """      
        | 表项格式 | uid | user_name | room_id_of_medal | level_of_medal | msg_type | time_stamp | text | ul | sc_price |
        | ------ | --- | --------- | ---------------- | -------------- | -------- | ---------- | ---- | -- | -------- |
        |  type  | var |  varchar  |     varchar      |      int       |  varchar |  timestamp | text | int|    int   |
        |        |char |           |                  |                |          |            |      |    |          |
        | ------ | --- | --------- | ---------------- | -------------- | -------- | ---------- | ---- | -- | -------- |
        | default| key | not null  |     0            |      0         | not null |  not null  |空字符串| -1 |     0    |
        | ------ | --- | --------- | ---------------- | -------------- | -------- | ---------- | ---- | -- | -------- |
                 | gift_ID | fans_type |
                 | ------- | ----------|
                 |  int    |  int      |
                 |         |           |
                 | ------- | --------- |
                 |    0    |     0     |
                 | ------- | --------- |
        数据解释
        uid: b站用户的uid，数据表的主键
        user_name: b站用户的user_name
        room_id_of_medal: b站的纯消息流的medal_id是room的id，舰团消息却是uid，很奇怪
        level_of_medal:当前携带的粉丝牌的等级
        msg_type:消息的类型
            danmu:弹幕消息
            sc:sc消息
            entry:进入消息
            gift:送礼物，连击礼物消息
            guard:舰团消息
            fans_change:粉丝变动
        time_stamp:消息的时间戳，如果该消息是不携带时间戳类型的消息取本地的时间戳
        text:消息的文本内容
        ul:如果消息中携带直播等级，记录，不携带不记录
        sc_price:如果是sc消息记录金额
        gift_ID:如果是礼物消息记录礼物id
        fans_type:如果消息不携带粉丝牌为0
                  如果消息携带粉丝牌且是asoul相关的粉丝牌则为1
                  如果消息携带粉丝牌不是asoul相关粉丝牌，但是可以判断为asoul粉丝则为2（暂未实现）
                  如果消息携带粉丝牌且不是asoul相关的粉丝牌，也不是asoul粉丝则为3
        (注：fans_type这里实现，在未拥有大批量代理时无法做到实时更新，只能依靠本地记录，因此此处暂不考虑实现，后续技术更新会实现)
        """
        if ver == 0:
            try:
                py_data = json.loads(data[16:].decode('utf-8', errors='ignore'))
                uid = ''
                user_name = ''
                room_id_of_medal = ''
                level_of_medal = 0
                msg_type = ''
                time_stamp = ''
                text = ''
                ul = -1
                sc_price = 0
                gift_ID = 0
                fans_type = 0
                sql_flag = 1
                if py_data['cmd'] == "DANMU_MSG:4:0:2:2:2:0" or py_data['cmd'] == "DANMU_MSG":
                    uid = py_data['info'][2][0]
                    user_name = py_data['info'][2][1]
                    if len(py_data['info'][3]) == 0:
                        room_id_of_medal = 0
                        level_of_medal = 0
                    else:
                        room_id_of_medal = py_data['info'][3][3]
                        level_of_medal = py_data['info'][3][0]
                    msg_type = 'danmu'
                    time_stamp = tf.ts2date(py_data['info'][0][4] / 1000)
                    text = py_data['info'][1]
                    ul = py_data['info'][4][0]
                    if room_id_of_medal in self.medal_list:
                        fans_type = 1
                    else:
                        # self.get_fans_status(uid)
                        fans_type = 3
                elif py_data['cmd'] == 'SUPER_CHAT_MESSAGE':
                    uid = py_data['data']['uid']
                    user_name = py_data['data']['user_info']['uname']
                    room_id_of_medal = py_data['data']['medal_info']['target_id']
                    level_of_medal = py_data['data']['medal_info']['medal_level']
                    msg_type = "sc"
                    time_stamp = tf.ts2date(py_data['data']['start_time'])
                    text = py_data['data']['message']
                    ul = py_data['data']['user_info']['user_level']
                    sc_price = py_data['data']['price']
                    gift_ID = py_data['data']['gift']['gift_id']
                    if room_id_of_medal in self.medal_list:
                        fans_type = 1
                    else:
                        # self.get_fans_status(uid)
                        fans_type = 3
                elif py_data['cmd'] == 'SEND_GIFT':
                    uid = py_data['data']['uid']
                    user_name = py_data['data']['uname']
                    room_id_of_medal = py_data['data']['medal_info']['target_id']
                    level_of_medal = py_data['data']['medal_info']['medal_level']
                    msg_type = "gift"
                    time_stamp = tf.ts2date(py_data['data']['timestamp'])
                    text = py_data['data']['giftName']
                    gift_ID = py_data['data']['giftId']
                    if room_id_of_medal in self.medal_list:
                        fans_type = 1
                    else:
                        # self.get_fans_status(uid)
                        fans_type = 3
                elif py_data['cmd'] == 'COMBO_SEND':
                    uid = py_data['data']['uid']
                    user_name = py_data['data']['uname']
                    room_id_of_medal = py_data['data']['medal_info']['target_id']
                    level_of_medal = py_data['data']['medal_info']['medal_level']
                    msg_type = "gift"
                    time_stamp = tf.ts2date(time.time())
                    temp = " * %d" % py_data['data']['batch_combo_num']
                    text = py_data['data']['gift_name'] + temp
                    gift_ID = py_data['data']['gift_id']
                    if room_id_of_medal in self.medal_list:
                        fans_type = 1
                    else:
                        # self.get_fans_status(uid)
                        fans_type = 3
                elif py_data['cmd'] == 'GUARD_BUY' or py_data['cmd'] == 'USER_TOAST_MSG':
                    uid = py_data['data']['uid']
                    user_name = py_data['data']['username']
                    room_id_of_medal = 0
                    level_of_medal = 0
                    msg_type = 'guard'
                    time_stamp = tf.ts2date(py_data['data']['start_time'])
                    if py_data['cmd'] == 'USER_TOAST_MSG':
                        text = py_data['data']['gift_name'] + '138'
                    else:
                        text = py_data['data']['gift_name'] + '198'
                    gift_ID = py_data['data']['gift_id']
                    fans_type = 1
                elif py_data['cmd'] == 'INTERACT_WORD':
                    uid = py_data['data']['uid']
                    user_name = py_data['data']['uname']
                    room_id_of_medal = py_data['data']['fans_medal']['target_id']
                    level_of_medal = py_data['data']['fans_medal']['medal_level']
                    msg_type = 'entry'
                    time_stamp = tf.ts2date(py_data['data']['timestamp'])
                    if room_id_of_medal in self.medal_list:
                        fans_type = 1
                    else:
                        # self.get_fans_status(uid)
                        fans_type = 3
                elif py_data['cmd'] == 'ENTRY_EFFECT':
                    uid = py_data['data']['uid']
                    copy_writing = py_data['data']['copy_writing']
                    user_name = copy_writing[7:-8]
                    room_id_of_medal = py_data['data']['target_id']
                    # 不带，设置为舰长的最低默认值
                    level_of_medal = 21
                    msg_type = 'entry'
                    time_stamp = tf.ts2date(time.time())
                    text = copy_writing
                    fans_type = 1
                elif py_data['cmd'] == 'ROOM_REAL_TIME_MESSAGE_UPDATE':
                    if self.new_fans_flag == 0:
                        new_fans = py_data['data']['fans'] - self.latest_fans
                        new_medal_fans = py_data['data']['fans_club'] - self.latest_medal_fans
                        self.latest_fans = py_data['data']['fans']
                        self.latest_medal_fans = py_data['data']['fans_club']
                    else:
                        self.latest_fans = py_data['data']['fans']
                        self.latest_medal_fans = py_data['data']['fans_club']
                    uid = 0
                    user_name = ''
                    room_id_of_medal = ''
                    level_of_medal = 0
                    msg_type = "fans_change"
                    time_stamp = tf.ts2date(time.time())
                    if self.new_fans_flag == 0:
                        text = "新增加了%s个粉丝，%s个粉丝团" % (new_fans, new_medal_fans)
                    else:
                        self.new_fans_flag = 0
                        text = "程序运行前有%s个粉丝，%s个粉丝团" % (self.before_fans, self.before_medal_fans)
                elif py_data['cmd'] == 'ROOM_CHANGE' or py_data['cmd'] == 'LIVE' or py_data['cmd'] == 'PREPARING':
                    if self.live_status == 'preparing' and py_data['cmd'] == 'LIVE':
                        self.live_status = 'live'
                        uid = 'start'
                        print('[Notice] live start')
                    elif self.live_status == 'live' and py_data['cmd'] == 'PREPARING':
                        self.live_status = 'preparing'
                        uid = 'end'
                        self.new_fans_flag = 1
                        # self.__send_live_analysis()
                        print('[Notice] live end')
                    else:
                        sql_flag = 0
                    time_stamp = tf.ts2date(time.time())
                else:
                    sql_flag = 0
                if sql_flag == 1:
                    sql = self.dm_insert_sql_model % (
                        uid, user_name, room_id_of_medal, level_of_medal, msg_type, time_stamp,
                        text, ul, sc_price, gift_ID, fans_type)
                    try:
                        with self.mysql_conn.cursor() as cursor:
                            cursor.execute(sql)
                        self.mysql_conn.commit()
                    except Exception as e:
                        self.mysql_conn.rollback()
                        print("Commit Failed!\n%s" % sql)

            except Exception as e:
                pass

        # 如果ver参数为2，说明时zlib格式的压缩数据包，需要解压
        elif ver == 2:
            data = zlib.decompress(data[16:])
            self.__data2sql(data)

        # 如果ver参数为1，说明为进入房间后或者心跳包的服务器回应，其中op为3时为房间的人气值
        elif ver == 1:
            if op == 3:
                renqi = int(data[16:].hex(), 16)
                now_heart_beat_time = time.time()
                self.latest_heart_beat_time = now_heart_beat_time
                time_stamp = tf.ts2date(now_heart_beat_time)
                print("[Notice] receive_back ", time_stamp)
                sql = self.rq_insert_sql_model % (time_stamp, renqi)
                # print("renqi", sql)
                self.mysql_conn.cursor().execute(sql)
            return

    # 根据格式自动创造一个弹幕数据表
    def __create_dm_sql(self, table_name):
        create_sql = "CREATE TABLE IF NOT EXISTS `%s` (" \
                     "`uid` varchar(255) not null, " \
                     "`user_name` varchar(255) not null, " \
                     "`room_id_of_medal` varchar(255) not null, " \
                     "`level_of_medal` int not null, " \
                     "`msg_type` varchar(255) not null, " \
                     "`time_stamp` timestamp not null, " \
                     "`text` text not null, " \
                     "`ul` int not null, " \
                     "`sc_price` int not null, " \
                     "`gift_ID` int not null, " \
                     "`fans_type` int not null)" \
                     "CHARSET=utf8" % table_name
        self.mysql_conn.cursor().execute(create_sql)

    # 根据格式自动创造一个人气数据表
    def __create_rq_sql(self, table_name):
        create_sql = "CREATE TABLE IF NOT EXISTS `%s`(" \
                     "`time_stamp` timestamp not null, " \
                     "`popularity` varchar(255) not null)" \
                     "CHARSET=utf8" % table_name
        self.mysql_conn.cursor().execute(create_sql)

    # 判断是否是新的一天
    def __judge_new_day(self):
        now_day = tf.get_time().tm_mday
        if self.now_day != now_day:
            print('new day!')
            self.new_fans_flag = 1
            self.now_day = now_day
            self.sql_road_dm = self.config['mysql_config']['sql_sentence']['dm_road'] % \
                               (tf.get_time().tm_year, tf.get_time().tm_mon, tf.get_time().tm_mday, self.room_id)
            self.dm_insert_sql_model = "Insert into " + self.sql_road_dm + " " + \
                                       self.config['mysql_config']['sql_sentence']['dm_values']

            self.sql_road_rq = self.config['mysql_config']['sql_sentence']['rq_road'] % \
                               (tf.get_time().tm_year, tf.get_time().tm_mon, tf.get_time().tm_mday, self.room_id)
            self.rq_insert_sql_model = "Insert into " + self.sql_road_rq + " " + \
                                       self.config['mysql_config']['sql_sentence']['rq_values']
            self.__create_rq_sql(self.sql_road_rq)
            self.__create_dm_sql(self.sql_road_dm)

    # 向外发送生成直播小结的消息
    def __send_live_analysis(self):
        # TODO(ydyjya): 后面解决表格问题一并处理
        pass
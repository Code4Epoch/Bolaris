# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        live_data_stream_decoder
# Author:           ydyjya
# Version:          0.3
# Created:          2022/1/16
# Description:      将直播信息流解码
# Function List:    ts2date()   --获取字符串格式的时间戳
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya          0.3             2022/1/16   create
# ------------------------------------------------------------------
import json
import zlib
import brotli
import time


# 时间转换
def ts2date(time_stamp):
    time_array = time.localtime(time_stamp)
    other_style_time = time.strftime("%Y%m%d%H%M%S", time_array)
    return other_style_time


class live_data_decoder(object):
    def __init__(self, buffer):
        self.buffer = buffer

    def decode(self, data):
        if data is None:
            return
        # 获取包的长度
        packet_len = int(data[:4].hex(), 16)
        # 获取包的ver属性
        ver = int(data[6:8].hex(), 16)
        # 获取包的op属性
        op = int(data[8:12].hex(), 16)
        # 有时存在多个数据包粘连的情况
        while len(data) > packet_len:
            # 调用
            self.decode(data[packet_len:])
            data = data[:packet_len]
        if ver == 0:
            try:
                py_data = json.loads(data[16:].decode('utf-8', errors='ignore'))
                text = ''
                ul = -1
                sc_price = 0
                gift_ID = 0
                gift_price = 0
                fans_type = 0
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
                    time_stamp = ts2date(py_data['info'][0][4] / 1000)
                    text = py_data['info'][1]
                    ul = py_data['info'][4][0]
                elif py_data['cmd'] == 'SUPER_CHAT_MESSAGE':
                    uid = py_data['data']['uid']
                    user_name = py_data['data']['user_info']['uname']
                    try:
                        room_id_of_medal = py_data['data']['medal_info']['target_id']
                        level_of_medal = py_data['data']['medal_info']['medal_level']
                    except TypeError:
                        room_id_of_medal = -1
                        level_of_medal = 0
                    msg_type = "sc"
                    time_stamp = ts2date(py_data['data']['start_time'])
                    text = py_data['data']['message']
                    ul = py_data['data']['user_info']['user_level']
                    sc_price = py_data['data']['price']
                    gift_ID = py_data['data']['gift']['gift_id']
                    gift_price = sc_price

                elif py_data['cmd'] == 'SEND_GIFT':
                    uid = py_data['data']['uid']
                    user_name = py_data['data']['uname']
                    room_id_of_medal = py_data['data']['medal_info']['target_id']
                    level_of_medal = py_data['data']['medal_info']['medal_level']
                    msg_type = "gift"
                    time_stamp = ts2date(py_data['data']['timestamp'])
                    text = py_data['data']['giftName']
                    gift_ID = py_data['data']['giftId']
                    gift_price = int(py_data['data']['combo_total_coin']) / 1000

                elif py_data['cmd'] == 'COMBO_SEND':
                    uid = py_data['data']['uid']
                    user_name = py_data['data']['uname']
                    room_id_of_medal = py_data['data']['medal_info']['target_id']
                    level_of_medal = py_data['data']['medal_info']['medal_level']
                    msg_type = "gift"
                    time_stamp = ts2date(time.time())
                    temp = " * %d" % py_data['data']['batch_combo_num']
                    text = py_data['data']['gift_name'] + temp
                    gift_ID = py_data['data']['gift_id']
                    gift_price = int(py_data['data']['combo_total_coin']) / 1000

                elif py_data['cmd'] == 'GUARD_BUY' or py_data['cmd'] == 'USER_TOAST_MSG':
                    uid = py_data['data']['uid']
                    user_name = py_data['data']['username']
                    room_id_of_medal = 0
                    level_of_medal = 0
                    msg_type = 'guard'
                    time_stamp = ts2date(py_data['data']['start_time'])
                    if py_data['cmd'] == 'USER_TOAST_MSG':
                        text = py_data['data']['role_name']
                        gift_price = int(py_data['data']['price'] / 1000)
                    else:
                        text = py_data['data']['gift_name'] + "guard_buy的不准确价格信息"
                        gift_price = 0
                    gift_ID = "1000%d" % py_data['data']['guard_level']

                elif py_data['cmd'] == 'INTERACT_WORD':
                    uid = py_data['data']['uid']
                    user_name = py_data['data']['uname']
                    room_id_of_medal = py_data['data']['fans_medal']['target_id']
                    level_of_medal = py_data['data']['fans_medal']['medal_level']
                    msg_type = 'entry'
                    time_stamp = ts2date(py_data['data']['timestamp'])

                elif py_data['cmd'] == 'ENTRY_EFFECT':
                    uid = py_data['data']['uid']
                    copy_writing = py_data['data']['copy_writing']
                    user_name = copy_writing[7:-8]
                    room_id_of_medal = py_data['data']['target_id']
                    # 不带，设置为舰长的最低默认值
                    level_of_medal = 21
                    msg_type = 'entry'
                    time_stamp = ts2date(time.time())
                    text = copy_writing

                elif py_data['cmd'] == 'ROOM_REAL_TIME_MESSAGE_UPDATE':
                    now_fans = py_data['data']['fans']
                    now_medal_fans = py_data['data']['fans_club']
                    uid = "0"
                    user_name = 'fans_change'
                    room_id_of_medal = ''
                    level_of_medal = 0
                    msg_type = "fans_change"
                    time_stamp = ts2date(time.time())
                    text = "粉丝:%s，粉丝团:%s" % (now_fans, now_medal_fans)

                elif py_data['cmd'] == 'ONLINE_RANK_COUNT':
                    uid = '0'
                    user_name = 'watch_num'
                    room_id_of_medal = ''
                    level_of_medal = 0
                    msg_type = "watch_num"
                    time_stamp = ts2date(time.time())
                    text = "观众:%s" % (py_data['data']['count'])

                elif py_data['cmd'] == 'HOT_RANK_CHANGED_V2':
                    uid = '0'
                    user_name = 'rank_num'
                    room_id_of_medal = ''
                    level_of_medal = 0
                    msg_type = "rank_num"
                    time_stamp = ts2date(time.time())
                    text = "分区:%s,名次:%s" % (py_data['data']['area_name'], py_data['data']['rank'])

                elif py_data['cmd'] == 'LIVE':
                    uid = '0'
                    user_name = 'start'
                    room_id_of_medal = ''
                    level_of_medal = 0
                    msg_type = "start"
                    temp = int(py_data['sub_session_key'].split('sub_time:')[1])
                    time_stamp = ts2date(temp)
                    print('[Notice] live start')

                elif py_data['cmd'] == 'PREPARING':
                    uid = '0'
                    user_name = 'end'
                    room_id_of_medal = ''
                    level_of_medal = 0
                    msg_type = "end"
                    time_stamp = ts2date(time.time())
                    print('[Notice] live end')

                elif py_data['cmd'] == 'ROOM_CHANGE':
                    uid = '0'
                    user_name = 'status_change'
                    room_id_of_medal = ''
                    level_of_medal = 0
                    msg_type = "status_change"
                    try:
                        temp = int(py_data['data']['sub_session_key'].split('sub_time:')[1])
                    except IndexError:
                        temp = ts2date(time.time())
                    time_stamp = ts2date(temp)
                    text = "标题:%s 分区:%s 父分区:%s" % \
                           (py_data['data']['title'], py_data['data']['area_name'], py_data['data']['parent_area_name'])
                    print('[Notice] room status change')
                elif py_data['cmd'] == "WATCHED_CHANGE":
                    uid = '0'
                    user_name = 'watched_change'
                    room_id_of_medal = ''
                    level_of_medal = 0
                    msg_type = "watched_change"
                    text = "看过:%d" % py_data["data"]["num"]
                    time_stamp = ts2date(time.time())
                else:
                    return None
                sql_data = (uid, user_name, room_id_of_medal, level_of_medal, msg_type, time_stamp,
                            text, ul, sc_price, gift_ID, gift_price, fans_type)
                self.buffer.put(sql_data)
            except Exception as e:
                py_data = json.loads(data[16:].decode('utf-8', errors='ignore'))
                print("something is wrong!", e)
                print("info is ", py_data)
                pass

        elif ver == 1:
            if op == 3:
                print("[Notice] receive_back ")
                uid = '0'
                user_name = 'renqi'
                room_id_of_medal = ''
                level_of_medal = 0
                msg_type = 'renqi'
                time_stamp = ts2date(time.time())
                text = "人气:" + "%d" % int(data[16:].hex(), 16)
                ul = -1
                sc_price = 0
                gift_ID = 0
                gift_price = 0
                fans_type = 0
                sql_data = (uid, user_name, room_id_of_medal, level_of_medal, msg_type, time_stamp,
                            text, ul, sc_price, gift_ID, fans_type, gift_price)
                self.buffer.put(sql_data)
        # 如果ver参数为2，说明时zlib格式的压缩数据包，需要解压
        elif ver == 2:
            data = zlib.decompress(data[16:])
            print('zlib')
            self.decode(data)
        # 如果ver参数为3，说明时brotli格式的压缩数据包，需要解压
        elif ver == 3:
            data = brotli.decompress(data[16:])
            self.decode(data)
            # print('brotli')
        else:
            print(ver, op, data)

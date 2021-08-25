# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        tool_function
# Author:           ydyjya、lucien
# Version:          1.0
# Created:          2021/7/9
# Description:      live中的辅助函数
# Function List:    read_translate_dict()   --读取营收翻译
#                   read_bilibili_gift_price()  --读取礼物对应价格
#                   ts2date()   --时间转换
#                   get_config()    --获取配置
#                   get_arg()   --获取summary类的参数
#                   get_time()  --获取时间
#                   compute_user_data() --计算对用户的用户级别统计数据
#                   get_user_stats_data()   --根据用户级别统计数据计算正常直播统计
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya、lucien   1.0             2021/7/9    create
# ------------------------------------------------------------------
import time
import json


# 读取营收翻译
def read_translate_dict(path):
    """

    :param path: 文件路径
    :return: 营收饼图对应的翻译
    """
    with open("%s" % path, encoding='utf-8') as revenue_file:
        revenue = revenue_file.read()
        revenue_dict = json.loads(revenue)
    return revenue_dict


# 读取礼物对应价格
def read_bilibili_gift_price(path):
    """

    :param path: 文件路径
    :return: 礼物对应的价格
    """
    with open("%s" % path, encoding='utf-8') as gift_file:
        gift = gift_file.read()
        gift_dict = json.loads(gift)
    return gift_dict


# 时间转换
def ts2date(time_stamp):
    time_array = time.localtime(time_stamp)
    other_style_time = time.strftime("%Y%m%d%H%M%S", time_array)
    return other_style_time


# 获取配置
def get_config(path):
    with open("%s" % path, encoding='utf-8') as config_file:
        config = config_file.read()
        my_config = json.loads(config)
    return my_config


# 获取时间
def get_time():
    local_time = time.time()
    time_array = time.localtime(local_time)
    return time_array


# 获取summary类的参数
def get_arg():
    print("请输入房间号：")
    room_id = input()
    print("请输入日期：\n格式为202x_x_xx")
    live_date = input()
    live_road = "%s_%s" % (live_date, room_id)
    print("请输入直播类型:单人直播/双人直播/小剧场/游戏室/夜谈/活动直播")
    live_type = input()
    return room_id, live_date, live_road, live_type


# 计算对用户的用户级别统计数据
def compute_user_data(my_default_time, my_data, my_medal_list, my_uid_list):
    """
    :param my_uid_list: uid字典
    :param my_medal_list:room_id字典
    :param my_default_time: 默认的起始时间
    :param my_data: 观众的观看记录
    :return: 原字典，但value（a list）的-1处为观看时长
    """

    uid2room = {}
    new_data = {}
    for k in my_medal_list.keys():
        uid2room[my_uid_list[k]] = my_medal_list[k]

    for k, v in my_data.items():
        watch_time = 0
        status = 'start'
        """
        status:
            start:开始状态
            entry:上一次是entry消息
            react:上一次是非entry消息
        """
        user_default_time = my_default_time

        user_msg_times_dic = {'gift': 0, 'danmu': 0, 'sc': 0, 'guard': 0, 'entry': 0, 'react': 0}

        target_medal = {'id': 0, 'level': 0}

        user_data = {}

        for record in v:
            if record[4] == 'entry' and status == 'start':
                user_default_time = record[5]
                status = 'entry'
                user_msg_times_dic['entry'] += 1
            elif record[4] == 'entry' and (status == 'entry' or status == 'react'):
                watch_time += 300
                user_default_time = record[5]
                status = 'entry'
                user_msg_times_dic['entry'] += 1
            elif record[4] != 'entry':
                watch_time += (record[5] - user_default_time).seconds
                user_default_time = record[5]
                status = 'react'
                if record[4] == 'danmu':
                    user_msg_times_dic['danmu'] += 1
                elif record[4] == 'gift':
                    user_msg_times_dic['gift'] += 1
                elif record[4] == 'guard':
                    user_msg_times_dic['guard'] += 1
                elif record[4] == 'sc':
                    user_msg_times_dic['sc'] += 1
                user_msg_times_dic['react'] += 1
            if record[2] in my_medal_list.values() or record[2] in my_uid_list.values():
                if record[3] > target_medal['level']:
                    target_medal['id'] = record[2]
                    target_medal['level'] = record[3]
                    if target_medal['id'] not in my_medal_list.values():
                        target_medal['id'] = uid2room[target_medal['id']]

        user_data['msg_times'] = user_msg_times_dic
        user_data['watch_time'] = watch_time / 60
        user_data['medal'] = target_medal

        new_data[k] = user_data
    return new_data


# 根据用户级别统计数据计算正常直播统计
def get_user_stats_data(my_data):
    """
    :param my_data: user直播统计字典
    :return: no return
    """
    watch_time = {'entry': 0, 'react': 0, 'entry_num': 0, 'react_num': 0}
    medal_sum = {'medal_0': {}, 'medal_1_5': {}, 'medal_6_10': {}, 'medal_11_20': {}, 'medal_21': {}, 'all': {}}
    for k, v in medal_sum.items():
        medal_sum[k] = {'gift': 0, 'danmu': 0, 'sc': 0, 'guard': 0, 'entry': 0, 'react': 0, 'num': 0}
    for k, v in my_data.items():
        watch_time['entry'] += v['watch_time']
        watch_time['entry_num'] += 1
        if v['msg_times']['react'] > 0:
            watch_time['react'] += v['watch_time']
            watch_time['react_num'] += 1
        if v['medal']['level'] == 0:
            for my_type in v['msg_times'].keys():
                medal_sum['medal_0'][my_type] += v['msg_times'][my_type]
            medal_sum['medal_0']['num'] += 1
        elif v['medal']['level'] < 6:
            for my_type in v['msg_times'].keys():
                medal_sum['medal_1_5'][my_type] += v['msg_times'][my_type]
            medal_sum['medal_1_5']['num'] += 1
        elif v['medal']['level'] < 11:
            for my_type in v['msg_times'].keys():
                medal_sum['medal_6_10'][my_type] += v['msg_times'][my_type]
            medal_sum['medal_6_10']['num'] += 1
        elif v['medal']['level'] < 21:
            for my_type in v['msg_times'].keys():
                medal_sum['medal_11_20'][my_type] += v['msg_times'][my_type]
            medal_sum['medal_11_20']['num'] += 1
        else:
            for my_type in v['msg_times'].keys():
                medal_sum['medal_21'][my_type] += v['msg_times'][my_type]
            medal_sum['medal_21']['num'] += 1
        for my_type in v['msg_times'].keys():
            medal_sum['all'][my_type] += v['msg_times'][my_type]
        medal_sum['all']['num'] += 1
    return medal_sum, watch_time


# 获取多场直播的列表和主题
def get_live_id_theme():
    print("请输入直播id 年_月_日_房间号\n以,为分隔符")
    live_id_str = input()
    live_id_list = live_id_str.split(sep=',')
    print('请输入主题')
    theme = input()
    return live_id_list, theme
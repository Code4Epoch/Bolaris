"""
@author:zzh、Lucien
@update_time:2021_7_9
"""
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


# 获取analysis的参数
def get_arg():
    print("请输入房间号：")
    room_id = input()
    print("请输入日期：\n格式为202x_x_xx")
    live_date = input()
    live_road = "%s_%s" % (live_date, room_id)
    print("请输入直播类型:单人直播/双人直播/小剧场/游戏室/夜谈/活动直播")
    live_type = input()
    return room_id, live_date, live_road, live_type

"""
@author:zzh、Lucien
@update_time:2021_7_3
"""
import time
import json


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

    return room_id, live_date, live_road

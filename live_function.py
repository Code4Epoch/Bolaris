"""
@author:zzh
@update_time:2021_7_2
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
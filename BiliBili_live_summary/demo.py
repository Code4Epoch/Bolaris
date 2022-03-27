# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        
# Author:           
# Version:          
# Created:          
# Description:      
# Function List:               
# History:
#       <author>        <version>       <time>      <desc>
# ------------------------------------------------------------------
from BiliBili_live_summary import BiliBili_daily_data_report
import json


def read_para(path):
    # 读取本目录下的参数文件
    with open("./%s.json" % path, encoding='utf-8') as config:
        para = json.loads(config.read())

    return para


if __name__ == '__main__':
    test = BiliBili_daily_data_report.BiliBili_daily_data_generator(read_para("daily_config"))
    test.generate()
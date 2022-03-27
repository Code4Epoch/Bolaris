# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        BiliBili_liveroom_monitor
# Author:           ydyjya
# Version:          0.3
# Created:          2022/1/16
# Description:      bilibili直播监控存储一体程序入口
# Function List:
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya          0.3             2022/1/16   create
# ------------------------------------------------------------------
from BiliBili_liveroom_monitor.BiliBili_live_monitor import BiliBili_liveroom_monitor

if __name__ == '__main__':
    BiliBili = BiliBili_liveroom_monitor("22634198")
    BiliBili.start()

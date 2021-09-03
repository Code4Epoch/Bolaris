# ASOUL直播间弹幕抓取&&数据分析（更新中）

这些文件用于爬取ASOUL直播间的弹幕（其他直播间也可以）和其他信息，以及简单的数据分析生成。

---

我们的B站专栏：[A-SOUL数据组](https://space.bilibili.com/1357475736):kissing_heart:
如果喜欢的话请关注A-SOUL五位可爱的小姐姐：
向晚：https://space.bilibili.com/672346917
贝拉：https://space.bilibili.com/672353429
珈乐：https://space.bilibili.com/351609538
嘉然：https://space.bilibili.com/672328094
乃琳：https://space.bilibili.com/672342685


---

## 目录

- [运行环境要求](#运行环境要求)
- [直播信息抓取](#直播信息抓取)
- [直播数据生成](直播数据生成)



## 运行环境要求

需要python3、requirements.txt中的库以及mysql数据库。

## 直播信息抓取

### 简介

这部分文件主要用于抓取直播间的所有信息，例如弹幕、SC、进场等，并且保存到mysql数据库中。

### 相关文件

- live_data_collection.py     ——    直播间监控爬取主程序
- live_function.py                 ——    一些要用到的小函数    

### 使用方法

1. 安装pip库，在目录下命令行

   ```
   pip install -r requirement.txt
   ```

2. 修改live/config.txt中room_id（你所关心的直播间号）、target_id（你所关心的主播的UID）、medal
   _room_id（你认为所有的和你所关心的主播相关的直播间号）。默认是asoul相关。

3. 修改live/config.txt中mysql_config中的host、port、user、password和db。

4. 同目录下新建一个python文件，在新文件添加语句如下：

   ```python
   from live_monitor import live_monitor

   room_id = '22625025' #这里是你要爬取的房间id
   test = live_monitor.bilibili_live_monitor(room_id=room_id)
   test.live_monitor()
   ```

5. 运行新文件，成功的话，程序会自动生成mysql中的表，并且程序终端会有心跳包等信息输出，可以连接数据库查看新的信息。

### 其他

关于数据库表结构和字段含义，请在live_data_collection.py等相关文件里面寻找注释。

因为是拿pycharm开发的，后面改了一下文件结构，可能有的地方文件import有点问题需要自己改一改。以后再更新一下（摆大烂了QAQ）

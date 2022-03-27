# BiliBili_live_monitor

> 本目录下包括以下程序，实现了获取某b站直播间的直播数据流，并将数据流存储到mysql数据库中

| **文件名**                      | **功能**                                                   | **备注**                                                     |
| ------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------ |
| **BiliBili_live_monitor.py**    | 本目录下所有程序的入口<br />直接执行main()函数即可         | 该文件中类内函数为对该目录下其他类的包装，start函数为BiliBili_live_room_monitor的入口函数 |
| room_id.json                    | 配置BiliBili_live_monitor.py的房间信息                     | 无                                                           |
| **live_monitor**                | 获取bilibili某直播间的原始直播信息流                       | 该类中，get_livestream为类内入口                             |
| live_monitor_config.json        | 配置live_monitor.py的参数信息，主要为心跳时间              | 该文件中的error_time为重连时间配置，该部分暂时废弃           |
| **live_data_stream_decoder.py** | 将live_monitor.py获取的原始直播信息流解码为mysql需要的形式 | 报文粗略解析见下文                                           |
| **mysql_for_livestream.py**     | 将live_data_stream_decoder.py解码的信息存储到数据库中      | 最新版协议接收到心跳回复后，b站会回复一个空对象（[object Object]）,他并不符合解码定义，会被直接打印出来 |
| mysql_config.json               | 配置mysql_for_livestream.py的参数信息，主要是数据库的配置  | 如使用需更改为自己的数据库信息配置，而insert_pt1,insert_pt2,insert_road如有需求根据自身需求更改，否则不需要做改动 |



### **live_monitor**

> **获取bilibili直播间的直播数据流**



### **live_data_stream_decoder**

> **将live_monitor中获取的原始直播流解码为适合mysql存储的形式**

**报文参数解释：**

0-3位为数据包长度信息；

6-7位为数据包的版本信息指示数据包的内容或者压缩格式；

8-11为op（~~我超，op！https://www.bilibili.com/video/BV1tb4y187Lw~~）参数，在传递控制信息时，会指示控制信息类型；

| **version** | **作用**             |
| ----------- | -------------------- |
| **0**       | **数据通信消息**     |
| **1**       | **控制通信消息**     |
| **2**       | **zlib格式压缩包**   |
| **3**       | **brotli格式压缩包** |

###### **ver=0**

> **数据通信消息：b站发给用户端的各种数据信息**

| **cmd**                                  | **数据信息**                                                 |
| ---------------------------------------- | ------------------------------------------------------------ |
| **STOP_LIVE_ROOM_LIST**                  | **一个list:距离上次发送该信息之间，停播的room_id**           |
| **WIDGET_BANNER**                        | **条幅类消息（例如：某某成为榜一）**                         |
| **PREPARING**                            | **直播间直播流停止推送**                                     |
| **LIVE**                                 | **直播开启**                                                 |
| **ROOM_CHANGE**                          | **直播间状态改变（分区、标题等发生变化）**                   |
| **LIVE_INTERACTIVE_GAME**                | **送银瓜子礼物触发的某种消息，不明确是否还有其他作用**       |
| **DANMU_MSG:4:0:2:2:2:0<br />DANMU_MSG** | **DANMU_MSG:4:0:2:2:2:0是特殊时段不可见的弹幕<br />DANMU_MSG是普通弹幕消息** |
| **SUPER_CHAT_MESSAGE**                   | **SC消息**                                                   |
| **SEND_GIFT**                            | **单次礼物**                                                 |
| **COMBO_SEND**                           | **连击礼物**                                                 |
| **GUARD_BUY<br />USER_TOAST_MSG**        | **舰长购买**                                                 |
| **INTERACT_WORD**                        | **普通入场消息**                                             |
| **ENTRY_EFFECT**                         | **舰长入场消息**                                             |
| **ROOM_REAL_TIME_MESSAGE_UPDATE**        | **粉丝/粉丝团变更消息**                                      |
| **ONLINE_RANK_COUNT**                    | **当前高能榜上有多少观众（可视作在线观看人数的一个最低值）** |
| **ONLINE_RANK_TOP3**                     | **高能榜前三变化信息**                                       |
| **ONLINE_RANK_V2**                       | **高能榜前7个人的一些信息**                                  |
| **NOTICE_MSG**                           | **嗯哥们投放的全站礼物广播信息**                             |
| **HOT_RANK_CHANGED_V2**                  | **全直播分区排名，排名高的会被官方挪到热门分区，该热门榜半个小时为一场** |

###### **ver=1**

**op为其他值时不会对直播流产生影响，也不影响数据记录**

**op=3时为心跳包的返回数据，并附加人气值**

###### **ver=2**

**zlib格式的数据压缩包（疑似已经被废弃）**

###### **ver=3**

**brotli格式的数据压缩包，当前b站直播协议所使用的压缩协议**

### mysql_for_livestream.py

> 数据表解释

| 列名             | 作用                                           | 数据类型  | 备注                                                         |
| ---------------- | ---------------------------------------------- | --------- | ------------------------------------------------------------ |
| uid              | 记录发送本信息的uid                            | varchar   | uid为0时，为直播间部分非用户发送的官方控制信息               |
| username         | 记录发送本信息的username                       | varchar   | uid为0时为控制信息类型                                       |
| room_id_of_medal | 记录发送本信息的用户的粉丝团房间号             | varchar   | b站部分消息给出的不是room_id，而是uid（举例：有几种报文给出的是22632424👈贝拉kira的房间号，有几种报文给出的是672353429👈贝拉kira的uid） |
| level_of_medal   | 记录发送本信息的用户所携带的粉丝牌的粉丝团等级 | int       | 即使给出的是uid，也会正确携带等级数据                        |
| msg_type         | 记录本信息的消息类型                           | varchar   | danmu:弹幕消息；<br />sc:sc消息；<br />entry:进入消息；<br /> gift:送礼物，连击礼物消息；<br />guard:舰团消息<br />watch_num:高能榜人数<br />fans_change:粉丝数变更<br />rank_num:分区排行<br />start:直播开始<br />end：直播结束 |
| time_stamp       | 记录本消息的时间戳                             | timestamp | 部分直播消息不会给出时间戳，取了本地时间                     |
| text             | 记录本消息的内容                               | text      | 无                                                           |
| ul               | 记录发送本消息用户的ul等级                     | int       | 无                                                           |
| sc_price         | 记录sc消息的价格                               | int       | 无                                                           |
| gift_ID          | 记录礼物消息的礼物id                           | int       | 无                                                           |
| gift_price       | 记录礼物消息的总价值                           | float     | b站官方在单独礼物中给小心心记作0.001元，连击里不算，无语😓    |
| fans_type        | 记录本消息发送者的关注情况                     | int       | 在未拥有大批量代理时无法做到实时更新，只能依靠本地记录，因此此处暂不考虑实现，后续技术更新会实现<br />果咩纳塞 |

本文件中，暂时还在使用单次插入，i/o开销还比较大，但考虑到使用情况不尽相同，无法用一个简单的Timer或者Counter来进行时间/条数记数来进行多条同时插入减少i/o。需要一个流量控制程序来控制多少条/多长时间进行一次插入操作，后续有时间会更新一个流量控制机制，来完成多条插入，节约i/o开销，提高程序运行速度。

该部分中已经实现了自动根据每日时间变化建表并更改插入路径的功能，但是0点前后数据可能会出现不正确时间插入（例如由于延迟，部分0点前数据在0点后到达，但其中包含不含时间戳——需要获取本地时间的消息）但并不会造成很大影响，因此无需关注

## 使用方法

首先修改mysql_config.json文件中的数据库配置，主要是user，password，dbname三项属性，改为你自己的参数。

BiliBili_liveroom_monitor类实例化的一个对象可以用来获取一个b站房间号的数据并持久化到mysql中，见demo.py

```Python
BiliBili = BiliBili_liveroom_monitor("22625025") # bilibili向晚大魔王的直播间
BiliBili.start()
```


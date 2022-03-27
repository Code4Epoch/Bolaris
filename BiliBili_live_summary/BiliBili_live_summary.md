# BiliBili_live_summary

### 配置文件

##### daily_config.json

| 文件名       | 用途                                                         |
| ------------ | ------------------------------------------------------------ |
| live_mark    | 用于为直播自定义备注名称，参数为on/off，为on时可以为直播增加备注 |
| live_compare | 用于开启对比功能（暂未实现）                                 |
| read_type    | 用于确定数据读取方式，参数为default/customization;为default时默认为读取某天直播的数据（必须包含开播或以及结束信息作为边界）<br />为customization时可以自行输入一段时间作为读取范围 |
| merge_days   | 为read_type中default方式获取时的参数，用来进行多天合并读取（例如某直播23点开播，如果不开启合并功能，默认只读取到改天24点。开启合并功能后（例如为2时），可以读取到第二天的24点） |

##### mysql_config.json

使用时要将host，user，password，dbname，port参数修改为使用者存储数据库的配置。

##### medal_config.json

用于标注团体内其他成员的房间号、uid数据为观众统计做支持

### 资源配置

在本目录的src文件下，需要以主播的房间号作为资源配置的文件夹名称，并包含以下文件

| 文件名                         | 用途                                                         |
| ------------------------------ | ------------------------------------------------------------ |
| background.png                 | 作为折线图以及柱状图的底图，运行后会产生background_opacity.png这一文件实际作为底图<br />注意一定要是png格式，jpg格式不含alpha通道，无法进行透明化 |
| config.json                    | 用于配置环图颜色以及其他图片的主题色<br />user_name:暂时并未使用<br />theme_color:用于配置文字颜色<br />series_color:用于配置环图渐变颜色 |
| wordcloud.jpg                  | 用于配置词云底色                                             |
| pie_background.png             | 用于配置环图背景图                                           |
| （非必须）pictorial_symbol.png | 象形柱状图symbol，如果使用需要配置该文件                     |

### 词典配置

本目录下包含4个词典，用于进行切词处理

| 文件名           | 用途                                                         |
| ---------------- | ------------------------------------------------------------ |
| cust_word.txt    | 用于使用者为切词程序配置自定义词典，该词典格式使用”\n“作为分隔符 |
| hard_word.txt    | 部分词在jieba中无法依靠load_userdict函数读取，因此只能通过suggest_freq实现增加词汇，如果发现添加到cust_word中仍无法切出的词可以丢到该词典中”,“为分隔符 |
| stop_word.txt    | 停词词典                                                     |
| synonym_word.txt | 同义词词典，使用方法如下<br />要保留的词汇\t要被替换的词汇1\t要被替换的词汇2\t…… |

**如果你没有词典，可以在BiliBili_daily_data_generator类generate函数中第43行处**

```python
word_freq = wordcloud_maker.word_reader(data["danmu"], "jieba", cust_dict=True).get_word_freq()
```

"jieba"参数更改为”hanlp“，使用hanlp作为切词库，不过时间会为jieba的10倍左右，但在无词典的情况下精度明显增加，不过由于实在太慢，所以没有当作参数作为可选项。以A-SOUL50分钟单播为例，50分钟场均会有6-7万条弹幕预料，字数约为50w左右，在我的本地上运行，jieba需要1分钟左右，hanlp大概为10分钟-15分钟，大部分情况下还是推荐直接用默认的jieba，如果电脑配置特别高的话，hanlp也是不错的选择。

## 使用方法

①修改mysql_config.json文件，修改host，user，password，dbname为自己的数据库数据

②修改medal_config.json文件，修改org_room_id_list， org_uid_list中的参数为监控直播间的团体或个人的房间号和uid用来判断是否是团体\个人的粉丝牌

③配置src文件夹中的底图文件，见上文

④配置word_dict中的四个词典，见上文

参照demo

```python
test = BiliBili_daily_data_generator(read_para("daily_config"))
test.generate()
# 运行后会进入get_args函数，根据格式输入直播参数即可
```
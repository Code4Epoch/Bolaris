# ASOUL直播间弹幕抓取&&数据分析（更新中）

这些文件用于爬取ASOUL直播间的弹幕（其他直播间也可以）和其他信息，以及简单的数据分析生成。

---

我们的B站专栏：[A-SOUL数据组](https://space.bilibili.com/1357475736):kissing_heart:
如果喜欢的话请关注A-SOUL五位可爱的小姐姐：

- 向晚：https://space.bilibili.com/672346917
- 贝拉：https://space.bilibili.com/672353429
- 珈乐：https://space.bilibili.com/351609538
- 嘉然：https://space.bilibili.com/672328094
- 乃琳：https://space.bilibili.com/672342685


---

## 目录

- [运行环境要求](#运行环境要求)
- [直播信息抓取](#直播信息抓取)
- [直播数据生成](#直播数据生成)
- [其他](#其他)



## 运行环境要求

需要python3、requirements.txt中的库以及mysql数据库。

安装pip，在根目录下命令行

```
pip install -r requirements.txt
```

## 直播信息抓取 BiliBili_liveroom_monitor

### 简介

这部分文件主要用于抓取直播间的所有信息，例如弹幕、SC、进场等，并且保存到mysql数据库中。

### 使用方法

[BiliBili_liveroom_monitor](./BiliBili_liveroom_monitor/BiliBili_live_monitor.md)

## 直播数据生成

### 简介

这部分文件主要用于生成上文中抓取的信息的数据，并以图片、表格、数据库的形式输出。

### 使用方法

[BiliBili_live_summary](./BiliBili_live_summary/BiliBili_live_summary.md)

## 其他

因为是拿pycharm开发的，后面改了一下文件结构，可能有的地方文件import或者文件路径有点问题需要自己改一改。以后再更新一下（摆大烂了QAQ）


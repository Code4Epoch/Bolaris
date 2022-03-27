# -*- coding: utf-8 -*- #
# ------------------------------------------------------------------
# File Name:        wordcloud_maker
# Author:           ydyjya,lucien
# Version:          0.3
# Created:          2022/2/1
# Description:      通过句子列表获取词云
# Function List:               
# History:
#       <author>        <version>       <time>      <desc>
#       ydyjya,lucien   0.1             2021/7/9    create
#       ydyjya          0.2             2021/8/18   修改了部分函数的风格
#       ydyjya          0.3             2022/2/1    重构
# ------------------------------------------------------------------
import jieba
import hanlp
import wordcloud
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import ImageColorGenerator
from imageio import imread
from hanlp.components.mtl.multi_task_learning import MultiTaskLearning
from hanlp.components.mtl.tasks.tok.tag_tok import TaggingTokenization
from Bolaris_Exception import wordcloud_para_error
from BiliBili_live_summary import global_var
import os

# 用来正常显示中文标签设置字体为黑体
plt.rcParams['font.sans-serif'] = ['SimHei']
# 用来正常显示负号
plt.rcParams['axes.unicode_minus'] = False

# 词典路径配置
cust_word_road = "./word_dict/cust_word.txt"
stop_word_road = "./word_dict/stop_word.txt"
synonym_word_road = "./word_dict/synonym_word.txt"
hard_word_road = "./word_dict/hard_word.txt"

# 词云底图以及存储方式配置
wordcloud_bgimage = "./src/%s/wordcloud.jpg"
wordcloud_save_dir = "./output/%s/"
wordcloud_save_file = "4-%s词云.png"


def load_dict(path):
    with open("%s" % path, encoding='utf-8') as word_file:
        word = word_file.read()
        word_list = word.split(',')
    return word_list


def hanlp_load_dict(path):
    with open("%s" % path, encoding='utf-8') as word_file:
        word = word_file.read()
        word_list = word.split('\n')
    return word_list


def combine_single_and_lower_char(sentence):
    sentence = sentence.lower()
    max_repeat = 3

    if len(sentence) <= max_repeat:
        return sentence

    now = ''
    repeat = 0
    new_sentence = ''
    for i in range(0, len(sentence)):

        if sentence[i] == now:
            repeat += 1
            if repeat < max_repeat:
                new_sentence += sentence[i]
        else:
            repeat = 0
            new_sentence += sentence[i]
            now = sentence[i]
    return new_sentence


def combine_single_word(word_list):
    combine_list = []
    for word in word_list:
        if word not in combine_list:
            combine_list.append(word)
    return combine_list


def compute_word_freq(word_list):
    word_count = {}
    for word in word_list:
        if word not in word_count:
            word_count[word] = 1
        else:
            word_count[word] += 1
    return word_count


def make_wordcloud(my_word_freq_dict, room_id, store_road):
    """

    :param my_word_freq_dict: 词频字典
    :param room_id: room_id用于
    :param store_road: 存图路径 为日期和房间号
    :return:
    """
    img = imread(wordcloud_bgimage % room_id)
    image_colors = ImageColorGenerator(img)
    mask_img = np.array(img)
    wc = wordcloud.WordCloud(font_path=r"C:\Windows\Fonts\msyh.ttc",
                             mask=mask_img,
                             width=1000,
                             height=700,
                             background_color=None,
                             mode="RGBA",
                             max_words=500)
    wc.generate_from_frequencies(my_word_freq_dict)
    plt.imshow(wc.recolor(color_func=image_colors))
    plt.clf()
    save_path = wordcloud_save_dir % store_road
    if os.path.exists(save_path) is False:
        os.makedirs(save_path)
    wc.to_file(save_path + wordcloud_save_file % store_road)


HanLP: MultiTaskLearning = hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_SMALL_ZH)
tok: TaggingTokenization = HanLP['tok/fine']


class word_reader(object):
    def __init__(self, sentence_list, mode, cust_dict):
        """

        :param sentence_list: 要切分的句子的列表
        :param mode: 切分模式，目前写了jieba和hanlp的切词方式
                            jieba：更快，但是切分精度和能力较差，需要词典辅助
                            hanlp：很慢，但在无词典的情况下切分能力较强，精度比较好
        :param cust_dict: 布尔变量，是否有词典，无词典默认用文章的jieba切分（hanlp实在是太慢了）
        """
        self.data = sentence_list
        self.mode = mode
        self.dict = cust_dict

    def get_word_freq(self):
        self.__load_word_dict()
        if self.dict is True:
            word_list = self.__processing_word()
        elif self.dict is False:
            word_list = self.__no_dict_processing_word()
        else:
            raise wordcloud_para_error("cust_dict is a Boolean var")
        word_count_dict = compute_word_freq(word_list)
        return word_count_dict

    def __load_word_dict(self):

        if self.mode == "jieba":
            jieba.load_userdict(cust_word_road)
        elif self.mode == "hanlp":
            tok.dict_force = set(hanlp_load_dict(cust_word_road))
        else:
            raise wordcloud_para_error("mode is jieba or hanlp")
        self.stop_word_dict = load_dict(stop_word_road)

        self.hard_word_dict = load_dict(hard_word_road)
        for word in self.hard_word_dict:
            jieba.suggest_freq(word, tune=True)

        self.combine_dict = {}
        for line in open("%s" % synonym_word_road, 'r', encoding='utf-8'):
            separate_word = line.strip().split("\t")
            num = len(separate_word)
            for i in range(1, num):
                self.combine_dict[separate_word[i]] = separate_word[0]

    def __processing_word(self):
        real_word_list = []
        for sentence in self.data:
            # 下面这行是针对voice_dm特制的，但似乎b站又不打算加上这个功能了，观望
            my_sentence = combine_single_and_lower_char(sentence[global_var.TEXT].split(';data_group;')[0])
            real_result = []
            if self.mode == "hanlp":
                result = HanLP(my_sentence, tasks="tok")
                for word in result["tok/fine"]:
                    if word in self.stop_word_dict:
                        pass
                    elif word in self.combine_dict:
                        real_result.append(self.combine_dict[word])
                    else:
                        real_result.append(word)
            elif self.mode == "jieba":
                result = jieba.cut(my_sentence)
                for word in result:
                    if word in self.stop_word_dict:
                        pass
                    elif word in self.combine_dict:
                        real_result.append(self.combine_dict[word])
                    else:
                        real_result.append(word)
            else:
                raise wordcloud_para_error("mode is jieba or hanlp")
            real_word_list.extend(combine_single_word(real_result))
        return real_word_list

    def __no_dict_processing_word(self):
        """
        无自建词典时，用这个切词
        :return:
        """
        article = ""
        for word in self.data:
            temp = word.split(';data_group;')[0]
            article += temp
        return jieba.lcut(article)

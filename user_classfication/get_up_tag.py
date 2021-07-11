import pymysql
import my_sql_sentence
import re
from gensim import corpora
from gensim import models
import numpy as np
from gensim.models import Word2Vec
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split




aup__list = [2400846, 329489875, 1508624800
    , 7028090
    , 95697439
    , 9189109
    , 1185499676
    , 10933736
    , 546192219
    , 37228699
    , 73000956
    , 482218159
    , 2075842775
    , 1243572082
    , 22031812
    , 5674737
    , 1695638
    , 59811897
    , 587992
    , 60457
    , 13188020
    , 1983455
    , 5358448
    , 7841930
    , 1146290035
    , 956775
    , 8138817
    , 956706
    , 13347778
    , 1587231
    , 428891
    , 394998430
    , 5411123
    , 122608
    , 17495434
    , 2117046216
    , 1047156421
    , 613727274
    , 183834
    , 12782522
    , 3512064
    , 15107002400846
    , 329489875
    , 1508624800
    , 7028090
    , 95697439
    , 9189109
    , 1185499676
    , 10933736
    , 546192219
    , 37228699
    , 73000956
    , 482218159
    , 2075842775
    , 1243572082
    , 22031812
    , 5674737
    , 1695638
    , 59811897
    , 587992
    , 60457
    , 13188020
    , 1983455
    , 5358448
    , 7841930
    , 1146290035
    , 956775
    , 8138817
    , 956706
    , 13347778
    , 1587231
    , 428891
    , 394998430
    , 5411123
    , 122608
    , 17495434
    , 2117046216
    , 1047156421
    , 613727274
    , 183834
    , 12782522
    , 3512064
    , 1510700]

other_list = [100022032,1002039059,10032675,10037251,10040906,10094840,10119428,10160261,10160324,102043515,10206987,10215511,10217431,102176172,102359102,10245319,10278125,102984190,102999485,10303206,1032082242,10330740,10334523,103416759,10345615,10350985,10360627,10413744,104207471,10421720,10431355,10462362,1047156421,10500463,105432922,105502937,10558098,1057929346,10592068,106017013,106320250,10664325,106685726,10696502,107130503,107138178,10715694,107278647,107873360,108532523,108635990,10874201,1087482281,1089059487,10897973,10909041,10915924,10933736,1093614539,10955537,10957838,1096223397,1096228210,109629667,1098417804,1098589911,109891,11012023,110352985,11057377,11061327,11062819,110631,11073,110969,11100920,111095065,11133002,11139681,11153765,11164088,11167,111927934,1120258151,11203281,11233223,112428,11252239,11253297,11255948,11264229,11270116,11278782,11299160,1131457022,11329000,113362335,11336264,11348715,11357018,113711,1140672573,11415011,11421405,11443550,1146290035,11498155,1152130637,1156637837,1160110127,11605312,1160621006,11616487,1164975438,116683,11684516,11684621,11685197,11688464,11739937,11742550,11783021,11783152,11799651,11805472,11814408,11831050,1185499676,118754720,1188981217,11938498,119801456,11997177,120187282,1202504814,1202762767,1205886701,12076317,1212641828,1213087766,121487111,12246,122608,122879,12295034,1230202404,12330804,123330934,123372,12337738,12344893,123484,12362451,123938419,124025181,1243266187,12434430,1243572082,12444306,124522366,124679421,124735327,12474467,124799,12497617,125086406,125526,125776535,12587095,12618791,12633655,12638031,1265680561,12761764,1276787,12771348,1277504905,1278218205,12782522,12807175,12816241,12820125,12846577,12874701,128912828,12894303,12894311,129259501,12945093,1296113267,13017755,130209,13043933,13046,1306049,13084687,1308967115,13101988,1310478759,1313602338,13164144,13188020,1318997,13195721,13199099,1320523,1320581,13209383,1322881625,13248198,132704,13279707,1328260,13297724,13315327,13347778,13354765,13357338,1338362,133901828,133934,13397992,1343403,1344579539,1351379,13555375,1357115005,135751,13575288,135980509,1359996,136107,13677047,13689353,13705279,13716885,1372433,1373037,13730996,13736113,137543719,137910465,1379178206,1379333376,137952,13814919,13817466,13826185,1384383789,13854759,138624168,1386661850,138827797,1388774,138894648,13904634,13908542,139219049,13925422,1393437,1398957,14013521,1403138,14068111,14082,14110780,14141146,1417,14203588,1420982,142371069,1424972,14254182,142841,14293391,1431512,14328316,143322,14333871,1435578906,1437582453,14387072,14392124,14402657,14413475,14444722,14454663,144709395,14478936,14487572,144923982,145149047,14553873,145544,145716,14583962,1461498,14626386,14636150,1467772,14681,1468726245,147166910,1472906636,1473247194,1473522,1473528,1473830,14751040,1475759,1476077,1476786225,14781644,14784628,14804670,1480503142,1481675,1482610,1483706297,1485065,14871346,14897804,149113,1492,14946689,149592,1501380958,1508624800,1510700,15134124,151482404,15161351,1516482,15168109,1519379568,15202837,1523132,15232589,1523475,152389373,1526101,15262818,15312,1531707,1532165,15324420,15377173,15385187,154021609,154058118,1543732,1546534138,1547601133,15503317,15641218,1565155,156619610,1567446009,156968917,15717030,1574624,1576121,1576741752,15773384,15774841,157761,1577804,15782465,15810,158119101,15817819,1587231,1589613,15897890,159,1590219891,1590370,159122,159163668,15953291,15960317,1596341281,1599822,1600113,1605721,1612112,161419374,161750562,1617739681,161775300,1619097,162265056,16235896,1630089,1634420959,16351122,163637592,1637,16379092,163917943,16419172,1643718,1646036311,164627,1647299264,16539048,165906284,165918,1661076923,1666868191,16671656,1667334057,16693558,1676940341,1677445,16794231,16822962,16836724,16853896,168598,168687092,1689182622,1691347,1692217,1693810421,1695638,1701495895,1701570,1706933058,171368594,17138783,17171565,17174243,171818544,1720738,17223352,1722768962,17239951,17244618,1724598,172917055,1734978373,173947574,17404564,1740827542,17409016,17437888,174501086,17474339,174902557,17495434,1750561,1753944506,17546432,1754707,17561219,17561885,1758308541,17588331,176037767,176063604,1762293,17646811,1764912,17678573,1770706,17712476,177291194,1773346,1774758,177613639]


def repair_list(tag_list):
    # 对tag_list进行修复
    my_tag_list = []
    for j in tag_list:
        tag_str = j.split(sep=':')
        if len(tag_str) < 5:
            continue
        elif len(tag_str) > 5:
            real_tag = tag_str[1] + ":" + tag_str[2]
            real_0 = tag_str[0]
            real_2 = tag_str[3]
            real_3 = tag_str[4]
            real_4 = tag_str[5]
            tag_str = [real_0, real_tag, real_2, real_3, real_4]
            # print(tag_str)
        else:
            real_tag = tag_str[1]

        # temp_list = [tag_str[0], tag_str[2], tag_str[3], tag_str[4], 1]

        my_tag_list.append(real_tag)

    return my_tag_list


def get_up(table_name):
    mysql_conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='292513', db='test')

    sql = "select uid, name, tag_click from %s" % table_name
    data = my_sql_sentence.my_sql(mysql_conn, sql)
    my_up_tag_dict = {}
    for up in data.__iter__():
        if up[2] is None or len(up[2]) == 0:
            continue
        click_tag_list = up[2].split(sep=';')
        key = up[0]
        real_tag_list = repair_list(click_tag_list)
        my_up_tag_dict[key] = real_tag_list

    return my_up_tag_dict


def get_word2vec(texts):

    model = Word2Vec.load("./test1")

    new_up_dict = {}

    for uid, tag_list in texts.items():
        for word in tag_list:
            try:
                word2vec = np.array(model.wv.__getitem__(word))
                if uid not in new_up_dict:
                    new_up_dict[uid] = word2vec
                elif uid in new_up_dict:
                    new_up_dict[uid] += word2vec
            except Exception:
                continue
    return model, new_up_dict


def get_tfidf(texts):
    my_texts = texts.values()
    dictionary = corpora.Dictionary(my_texts)
    corpus = [dictionary.doc2bow(text) for text in my_texts]
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = [tfidf[doc] for doc in corpus]

    my_tfidf = {}
    up_key = list(texts.keys())
    idx = 0
    for item in corpus_tfidf:
        temp_list = []
        for pair in item:
            temp_pair = (dictionary[pair[0]], pair[1])
            temp_list.append(temp_pair)
        my_tfidf[up_key[idx]] = temp_list
        idx += 1
    return my_tfidf


texts = get_up('up_video')
my_data = []
label = []
for k, v in texts.items():
    key = int(k)
    if key in aup__list:
        my_data.append(v)
        label.append(1)
    elif key in other_list:
        my_data.append(v)
        label.append(0)


"""tfidf = TfidfVectorizer()
traindata = tfidf.fit_transform(X_train)
testdata = tfidf.transform(X_test)



# 多项式朴素贝叶斯


"""




import pandas as pd
import numpy as np
import keras
from keras.layers.merge import concatenate
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.layers.embeddings import Embedding
from keras.layers import Conv1D, MaxPooling1D, Flatten, Dropout, Dense, Input
from keras.models import Model
from sklearn.model_selection import train_test_split
from sklearn import metrics
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt
from sklearn.metrics import f1_score,recall_score

my_data = np.array(my_data)
label = np.array(label)
df_data = pd.DataFrame(my_data, columns=['words'])
df_label = pd.DataFrame(label, columns=['words'])


def data_process(max_len=50):           #path为句子的存储路径，max_len为句子的固定长度

    dataset = pd.concat([df_data, pd.DataFrame(label, columns=['label'])], axis=1)
    # print(dataset)
    tokenizer = Tokenizer()                   # 创建一个Tokenizer对象，将一个词转换为正整数
    tokenizer.fit_on_texts(dataset['words'])  #将词编号，词频越大，编号越小
    vocab = tokenizer.word_index              # 得到每个词的编号
    x_train, x_test, y_train, y_test = train_test_split(dataset['words'], dataset['label'], test_size=0.3)  #划分数据集
    x_train_word_ids = tokenizer.texts_to_sequences(x_train)     #将测试集列表中每个词转换为数字
    x_test_word_ids = tokenizer.texts_to_sequences(x_test)       #将训练集列表中每个词转换为数字
    x_train_padded_seqs = pad_sequences(x_train_word_ids, maxlen=max_len)  # 将每个句子设置为等长，每句默认为50
    x_test_padded_seqs = pad_sequences(x_test_word_ids, maxlen=max_len)    #将超过固定值的部分截掉，不足的在最前面用0填充
    return x_train_padded_seqs,y_train,x_test_padded_seqs,y_test,vocab


def TextCNN_model_1(x_train, y_train, x_test, y_test):
    main_input = Input(shape=(50,), dtype='float64')
    # 嵌入层（使用预训练的词向量）
    embedder = Embedding(len(vocab) + 1, 300, input_length=50, trainable=False)
    embed = embedder(main_input)
    # 卷积层和池化层，设置卷积核大小分别为3,4,5
    cnn1 = Conv1D(256, 3, padding='same', strides=1, activation='relu')(embed)
    cnn1 = MaxPooling1D(pool_size=48)(cnn1)
    cnn2 = Conv1D(256, 4, padding='same', strides=1, activation='relu')(embed)
    cnn2 = MaxPooling1D(pool_size=47)(cnn2)
    cnn3 = Conv1D(256, 5, padding='same', strides=1, activation='relu')(embed)
    cnn3 = MaxPooling1D(pool_size=46)(cnn3)
    # 合并三个模型的输出向量
    cnn = concatenate([cnn1, cnn2, cnn3], axis=-1)
    flat = Flatten()(cnn)
    drop = Dropout(0.2)(flat) #在池化层到全连接层之前可以加上dropout防止过拟合
    main_output = Dense(3, activation='softmax')(drop)
    model = Model(inputs=main_input, outputs=main_output)
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    one_hot_labels = keras.utils.to_categorical(y_train, num_classes=3)  # 将标签转换为one-hot编码
    model.fit(x_train, one_hot_labels, batch_size=64, epochs=20)
    result = model.predict(x_test)  # 预测样本属于每个类别的概率
    result_labels = np.argmax(result, axis=1)  # 获得最大概率对应的标签
    y_predict = list(map(int, result_labels))

    print('准确率', metrics.accuracy_score(y_test, y_predict))
    print(f1_score(y_test, y_predict))
    print(recall_score(y_test, y_predict))


x_train, y_train, x_test, y_test, vocab = data_process()
# TextCNN_model_1(x_train, y_train, x_test, y_test)

nb_model = MultinomialNB(alpha=0.001)
nb_model.fit(x_train, y_train)
predict_test = nb_model.predict(x_test)
print("多项式朴素贝叶斯up主分类的准确率为：",metrics.accuracy_score(predict_test, y_test))
print(f1_score(y_test, predict_test))
print(recall_score(y_test, predict_test))




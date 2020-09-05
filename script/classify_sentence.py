#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
-----------------------------------------
@Author: XSS
@Email: 18212010042@fudan.edu.cn
@Created: 2020/09/05
------------------------------------------
@Modify: 2020/09/05
------------------------------------------
@Description:
"""
import json
import os
import random
from pathlib import Path

from fasttext import FastText
from nltk import WordPunctTokenizer
from nltk.corpus import stopwords

from definitions import DATA_DIR, OUTPUT_DIR


class PreprocessData:
    def __init__(self, data_path=None):
        self.__init__path()
        self.data_path = data_path
        if not data_path:
            self.data_path = str(self.data_dir / 'annotation_sentence_vote_valid.json')

    def __init__path(self):
        self.data_dir = Path(DATA_DIR) / 'dataset_for_sentence_classifier'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.train_data_path = str(self.data_dir / 'fast_text_train_data.txt')
        self.test_data_path = str(self.data_dir / 'fast_text_test_data.txt')
        self.predict_data_path = str(self.data_dir / 'fast_text_predict_data.txt')

    def get_data_from_json(self, ):
        """
        :param path: path of a json file
        :return: json_list data
        """
        try:
            with open(self.data_path, 'r', encoding="utf-8") as json_file:
                load_dict = json.load(json_file)
                json_file.close()
            return load_dict
        except Exception as e:
            print("exception:" + str(e))

    def remove_sign(self, str):
        """
        remove sign code of sentence
        input;str
        :return: str
        """
        # print("start remove sign code")
        remove_list = ["\n", "\t", "\r", "/", "*", ".", ";", "@", "{", "}", "<p>", "(", ")", "#", "=", ":", "+", "-",
                       "!", "[", "]", ",", ":", "<", ">", "|", "\\", "&", "'", "?", "\""]
        new_str = str
        for item in remove_list:
            new_str = new_str.replace(item, " ")
        return new_str

    def remove_stop_words(self, sentence):
        """
        remove stop_words of sentence
        :param sentence:
        :return:
        """
        # print("start remove stop words")
        words = WordPunctTokenizer().tokenize(sentence)
        st = stopwords.words('english')
        str_list = []
        for token in words:
            if token not in st:
                str_list.append(token)
        return " ".join(str_list)

    def fast_text_data(self, sentence_list):
        """
        change sentence_list into fast_text format
        :param sentence_list: the origin sentence from the json dataset
        :return: Preprocessed data
        """
        data_list = []
        for item in sentence_list:
            str_rm_sign = self.remove_sign(item["text"])
            str_rm_stop = self.remove_stop_words(str_rm_sign)
            data_list.append("__label__" + str(item["vote_type"]) + " , " + str_rm_stop)
        random.shuffle(data_list)
        return data_list

    def write_data(self, sentences, fileName):
        print("writing data to fasttext format")
        try:
            out = open(fileName, 'w', encoding="utf-8")
            for sentence in sentences:
                out.write(sentence + "\n")
            print("done!")
        except Exception as e:
            print("exception:" + str(e))

    def save_train_and_test_data(self, fast_text_data_list):
        seg_num = int(len(fast_text_data_list) * 0.8)
        self.write_data(fast_text_data_list[:seg_num], self.train_data_path)
        self.write_data(fast_text_data_list[seg_num + 1:], self.test_data_path)

    def preprocess(self, ):
        sentence_data = self.get_data_from_json()
        fast_text_data = self.fast_text_data(sentence_data)
        self.save_train_and_test_data(fast_text_data)


class FastTextClassifier:
    def __init__(self):
        self.classifier = None
        self.__init__path()
        self.preprocessor = PreprocessData()
        self.load_model()

    def __init__path(self):
        self.data_dir = Path(DATA_DIR) / 'dataset_for_sentence_classifier'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.train_data_path = str(self.data_dir / 'fast_text_train_data.txt')
        self.test_data_path = str(self.data_dir / 'fast_text_test_data.txt')
        self.ori_json_path = str(self.data_dir / 'annotation_sentence_vote_valid.json')
        self.model_dir = Path(OUTPUT_DIR) / 'fast_text model'
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = str(self.model_dir / 'classifier.model')

    def load_model(self, ):
        if os.path.exists(self.model_path):
            self.classifier = FastText.load_model(self.model_path)
        else:
            self.train_model()
            print("no such model, train now")

    def set_model_path(self, new_path):
        self.model_path = new_path

    def train_model(self):
        if not Path(self.train_data_path).exists():
            self.preprocessor.preprocess()
        classifier = FastText.train_supervised(input=self.train_data_path, lr=0.25, ws=4)
        classifier.save_model(self.model_path)
        self.classifier = classifier
        print("test result in training data:")
        result = classifier.test(self.train_data_path)
        print(result)
        print("test result in testing data:")
        result = classifier.test(self.test_data_path)
        print(result)
        # texts = ['The h component floating point number', 'Deprecated']
        # labels, probability = classifier.predict(texts)
        # print(labels)
        # print(probability)

    def predict(self, text):
        """
        :param text: a str query
        :return: predicted label of the input sentence
        """
        rmsign_text = self.preprocessor.remove_sign(text)
        pre_data = self.preprocessor.remove_stop_words(rmsign_text)
        # label = self.classifier.predict_single(pre_data)
        label, probability = self.classifier.predict(pre_data)
        # 打印预测标签
        return int(label[0][-1])


if __name__ == "__main__":
    classifier = FastTextClassifier()
    label = classifier.predict(" The color light gray")
    print(label)

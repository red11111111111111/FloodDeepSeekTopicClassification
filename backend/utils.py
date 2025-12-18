# coding: UTF-8
import os
import torch
import numpy as np
import pickle as pkl
from tqdm import tqdm
import time
from datetime import timedelta
from transformers import BertTokenizer
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MAX_VOCAB_SIZE = 10000  # 词表长度限制
UNK, PAD = '<UNK>', '<PAD>'  # 未知字，padding符号
CLS = '[CLS]'  # BERT的CLS符号

def build_vocab(file_path, tokenizer, max_size, min_freq):
    vocab_dic = {}
    with open(file_path, 'r', encoding='UTF-8') as f:
        for line in tqdm(f):
            lin = line.strip()
            if not lin:
                continue
            content = lin.split('\t')[0]
            for word in tokenizer(content):
                vocab_dic[word] = vocab_dic.get(word, 0) + 1
        vocab_list = sorted([_ for _ in vocab_dic.items() if _[1] >= min_freq], key=lambda x: x[1], reverse=True)[:max_size]
        vocab_dic = {word_count[0]: idx for idx, word_count in enumerate(vocab_list)}
        vocab_dic.update({UNK: len(vocab_dic), PAD: len(vocab_dic) + 1})
    return vocab_dic

def build_dataset(config, use_bert=False):
    if use_bert:
        logger.debug("Using BERT tokenizer")
        tokenizer = config.tokenizer  # 使用 BertTokenizer
        pad_size = config.pad_size
        def load_dataset(path, pad_size=pad_size):
            contents = []
            with open(path, 'r', encoding='UTF-8') as f:
                for line in tqdm(f):
                    lin = line.strip()
                    if not lin:
                        continue
                    try:
                        content, label = lin.split('\t')
                        token = tokenizer.tokenize(content)
                        token = ['[CLS]'] + token
                        seq_len = len(token)
                        mask = []
                        token_ids = tokenizer.convert_tokens_to_ids(token)
                        if pad_size:
                            if len(token) < pad_size:
                                mask = [1] * len(token_ids) + [0] * (pad_size - len(token))
                                token_ids += ([0] * (pad_size - len(token)))
                            else:
                                mask = [1] * pad_size
                                token_ids = token_ids[:pad_size]
                                seq_len = pad_size
                        contents.append((token_ids, int(label), seq_len, mask))
                    except ValueError as e:
                        logger.error(f"Invalid data format in {path}: {line.strip()}")
                        continue
            return contents
        train = load_dataset(config.train_path, config.pad_size)
        dev = load_dataset(config.dev_path, config.pad_size)
        test = load_dataset(config.test_path, config.pad_size)
        logger.debug(f"BERT data loaded: train={len(train)}, dev={len(dev)}, test={len(test)}")
        return train, dev, test
    else:
        logger.debug("Using character-level tokenizer")
        tokenizer = lambda x: [y for y in x]  # char-level
        if os.path.exists(config.vocab_path):
            vocab = pkl.load(open(config.vocab_path, 'rb'))
            logger.debug(f"Loaded vocab from {config.vocab_path}, size={len(vocab)}")
        else:
            logger.debug(f"Building vocab from {config.train_path}")
            vocab = build_vocab(config.train_path, tokenizer=tokenizer, max_size=MAX_VOCAB_SIZE, min_freq=1)
            pkl.dump(vocab, open(config.vocab_path, 'wb'))
            logger.debug(f"Saved vocab to {config.vocab_path}, size={len(vocab)}")
        print(f"Vocab size: {len(vocab)}")

        def load_dataset(path, pad_size=32):
            contents = []
            with open(path, 'r', encoding='UTF-8') as f:
                for line in tqdm(f):
                    lin = line.strip()
                    if not lin:
                        continue
                    try:
                        content, label = lin.split('\t')
                        words_line = []
                        token = tokenizer(content)
                        seq_len = len(token)
                        if pad_size:
                            if len(token) < pad_size:
                                token.extend([PAD] * (pad_size - len(token)))
                            else:
                                token = token[:pad_size]
                                seq_len = pad_size
                        # word to id
                        for word in token:
                            words_line.append(vocab.get(word, vocab.get(UNK)))
                        contents.append((words_line, int(label), seq_len))
                    except ValueError as e:
                        logger.error(f"Invalid data format in {path}: {line.strip()}")
                        continue
            return contents
        train = load_dataset(config.train_path, config.pad_size)
        dev = load_dataset(config.dev_path, config.pad_size)
        test = load_dataset(config.test_path, config.pad_size)
        logger.debug(f"Non-BERT data loaded: vocab_size={len(vocab)}, train={len(train)}, dev={len(dev)}, test={len(test)}")
        return vocab, train, dev, test

class DatasetIterater(object):
    def __init__(self, batches, batch_size, device):
        self.batch_size = batch_size
        self.batches = batches
        self.n_batches = len(batches) // batch_size
        self.residue = False  # 记录batch数量是否为整数
        if len(batches) % self.n_batches != 0:
            self.residue = True
        self.index = 0
        self.device = device

    def _to_tensor(self, datas):
        x = torch.LongTensor([_[0] for _ in datas]).to(self.device)
        y = torch.LongTensor([_[1] for _ in datas]).to(self.device)
        seq_len = torch.LongTensor([_[2] for _ in datas]).to(self.device)
        if len(datas[0]) > 3:  # 如果数据包含mask（BERT模型）
            mask = torch.LongTensor([_[3] for _ in datas]).to(self.device)
            return (x, seq_len, mask), y
        return (x, seq_len), y

    def __next__(self):
        if self.residue and self.index == self.n_batches:
            batches = self.batches[self.index * self.batch_size: len(self.batches)]
            self.index += 1
            batches = self._to_tensor(batches)
            return batches
        elif self.index >= self.n_batches:
            self.index = 0
            raise StopIteration
        else:
            batches = self.batches[self.index * self.batch_size: (self.index + 1) * self.batch_size]
            self.index += 1
            batches = self._to_tensor(batches)
            return batches

    def __iter__(self):
        return self

    def __len__(self):
        if self.residue:
            return self.n_batches + 1
        else:
            return self.n_batches

def build_iterator(dataset, config):
    iter = DatasetIterater(dataset, config.batch_size, config.device)
    return iter

def get_time_dif(start_time):
    """获取已使用时间"""
    end_time = time.time()
    time_dif = end_time - start_time
    return timedelta(seconds=int(round(time_dif)))
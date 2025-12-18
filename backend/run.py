# coding: UTF-8
import time
import torch
import numpy as np
from train_eval import train, init_network
from importlib import import_module
from utils import build_iterator, build_dataset, get_time_dif
import os
import json
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main(file_path, model_params):
    dataset = 'THUCNews'  # 数据集路径
    embedding = 'embedding_SougouNews.npz'  # 预训练词向量文件
    # 使用从前端传来的模型参数
    dropout = model_params['dropout']
    num_epochs = model_params['num_epochs']
    batch_size = model_params['batch_size']
    learning_rate = model_params['learning_rate']
    model_name = model_params['model']
    embedding_option = 'embedding_SougouNews.npz'
    # 动态导入模型和相关配置
    try:
        x = import_module('models.' + model_name)
        config = x.Config(dataset, embedding_option)
    except ImportError as e:
        logger.error(f"Failed to import model {model_name}: {str(e)}")
        raise
    config.dropout = dropout
    config.num_epochs = num_epochs
    config.batch_size = batch_size
    config.learning_rate = learning_rate
    # 设置随机种子
    np.random.seed(1)
    torch.manual_seed(1)
    torch.cuda.manual_seed_all(1)
    torch.backends.cudnn.deterministic = True
    # 加载数据
    logger.info("Loading data...")
    try:
        # 根据模型类型选择数据加载方式
        if model_name in ['bert', 'bert_CNN']:
            train_data, dev_data, test_data = build_dataset(config, use_bert=True)
        else:
            vocab, train_data, dev_data, test_data = build_dataset(config)
            config.n_vocab = len(vocab)
        train_iter = build_iterator(train_data, config)
        dev_iter = build_iterator(dev_data, config)
        test_iter = build_iterator(test_data, config)
    except Exception as e:
        logger.error(f"Data loading error: {str(e)}")
        raise
    # 初始化模型
    try:
        model = x.Model(config).to(config.device)
        init_network(model)
    except Exception as e:
        logger.error(f"Model initialization error: {str(e)}")
        raise
    # 清空 CUDA 缓存
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    # 开始训练
    logger.info(f"Training the {model_name} model...")
    try:
        metrics_dict = train(config, model, train_iter, dev_iter, test_iter)
    except Exception as e:
        logger.error(f"Training error: {str(e)}")
        raise
    # 保存训练结果到 JSON
    result_dir = 'results'
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    result_path = os.path.join(result_dir, f"{model_name}_results.json")
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(metrics_dict, f, ensure_ascii=False, indent=4)
    return metrics_dict
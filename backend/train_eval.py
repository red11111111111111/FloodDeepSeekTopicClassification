# coding: UTF-8
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn import metrics
import time
from utils import get_time_dif
from tensorboardX import SummaryWriter
import matplotlib

matplotlib.use('Agg')  # 设置非交互式后端
import matplotlib.pyplot as plt
import os
import logging
from torch.optim import AdamW
from transformers.optimization import get_linear_schedule_with_warmup

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 权重初始化，默认xavier
def init_network(model, method='xavier', exclude='embedding', seed=123):
    torch.manual_seed(seed)
    for name, w in model.named_parameters():
        if exclude not in name:
            if 'weight' in name:
                if w.dim() >= 2:  # 仅对二维及以上张量应用初始化
                    if method == 'xavier':
                        nn.init.xavier_normal_(w)
                    elif method == 'kaiming':
                        nn.init.kaiming_normal_(w)
                    else:
                        nn.init.normal_(w)
                else:
                    logger.debug(f"Skipping initialization for {name} (dim={w.dim()})")
            elif 'bias' in name:
                nn.init.constant_(w, 0)
            else:
                pass


def train(config, model, train_iter, dev_iter, test_iter):
    start_time = time.time()
    model.train()
    # 根据模型类型选择优化器
    if config.model_name in ['bert', 'bert_CNN']:
        optimizer = AdamW(model.parameters(), lr=config.learning_rate)
        warm_up_ratio = 0.05  # 定义预热比例
        total_steps = len(train_iter) * config.num_epochs
        scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warm_up_ratio * total_steps,
                                                    num_training_steps=total_steps)
    else:
        optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)

    total_batch = 0  # 记录进行到多少batch
    dev_best_loss = float('inf')
    last_improve = 0  # 记录上次验证集loss下降的batch数
    flag = False  # 记录是否很久没有效果提升
    writer = SummaryWriter(log_dir=config.log_path + '/' + time.strftime('%m-%d_%H.%M', time.localtime()))
    # 初始化训练过程中的指标记录
    train_losses = []
    train_accuracies = []
    dev_losses = []
    dev_accuracies = []
    # 添加保存指标的变量
    precision = None
    recall = None
    f1_score = None
    for epoch in range(config.num_epochs):
        logger.info('Epoch [{}/{}]'.format(epoch + 1, config.num_epochs))
        epoch_train_loss = 0
        epoch_train_acc = 0
        for i, (trains, labels) in enumerate(train_iter):
            try:
                model.train()  # 确保每次迭代开始时模型处于训练模式
                outputs = model(trains)
                model.zero_grad()
                loss = F.cross_entropy(outputs, labels)
                loss.backward()
                optimizer.step()
                if config.model_name in ['bert', 'bert_CNN']:
                    scheduler.step()  # 更新学习率
                epoch_train_loss += loss.item()
                true = labels.data.cpu().numpy()
                predic = torch.max(outputs.data, 1)[1].cpu().numpy()
                epoch_train_acc += metrics.accuracy_score(true, predic)
                if total_batch % 100 == 0:
                    # 每100轮评估一次
                    dev_acc, dev_loss = evaluate(config, model, dev_iter)
                    if dev_loss < dev_best_loss:
                        dev_best_loss = dev_loss
                        torch.save(model.state_dict(), config.save_path)
                        improve = '*'
                        last_improve = total_batch
                    else:
                        improve = ''
                    time_dif = get_time_dif(start_time)
                    msg = 'Iter: {0:>6},  Train Loss: {1:>5.2},  Train Acc: {2:>6.2%},  Val Loss: {3:>5.2},  Val Acc: {4:>6.2%},  Time: {5} {6}'
                    logger.info(
                        msg.format(total_batch, loss.item(), epoch_train_acc / (i + 1), dev_loss, dev_acc, time_dif,
                                   improve))
                    writer.add_scalar("loss/train", loss.item(), total_batch)
                    writer.add_scalar("loss/dev", dev_loss, total_batch)
                total_batch += 1
            except Exception as e:
                logger.error(f"Training error in batch {total_batch}: {str(e)}")
                raise e
        # 记录每个epoch的损失和准确率
        epoch_train_loss /= len(train_iter)
        epoch_train_acc /= len(train_iter)
        dev_acc, dev_loss = evaluate(config, model, dev_iter)
        train_losses.append(epoch_train_loss)
        train_accuracies.append(epoch_train_acc)
        dev_losses.append(dev_loss)
        dev_accuracies.append(dev_acc)
        if total_batch - last_improve > config.require_improvement:
            logger.info("No optimization for a long time, auto-stopping...")
            flag = True
            break
    writer.close()
    # 绘制训练曲线
    plot_training_curve(train_losses, train_accuracies, dev_losses, dev_accuracies)
    # 测试集指标
    test_acc, test_loss, test_report, test_confusion = test(config, model, test_iter)
    # 提取 precision、recall、f1-score
    precision = test_report["weighted avg"]["precision"]
    recall = test_report["weighted avg"]["recall"]
    f1_score = test_report["weighted avg"]["f1-score"]
    return {"precision": precision, "recall": recall, "f1_score": f1_score, "accuracy": test_acc}


def plot_training_curve(train_losses, train_accuracies, dev_losses, dev_accuracies, save_dir='static/images'):
    plt.figure(figsize=(12, 6))
    # 损失曲线
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(dev_losses, label='Dev Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss Curve')
    plt.legend()
    # 准确率曲线
    plt.subplot(1, 2, 2)
    plt.plot(train_accuracies, label='Train Accuracy')
    plt.plot(dev_accuracies, label='Dev Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.title('Training and Validation Accuracy Curve')
    plt.legend()
    # 确保保存目录存在
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = os.path.join(save_dir, "training_curve.png")
    plt.savefig(save_path)
    plt.close('all')


def test(config, model, test_iter):
    model.eval()
    loss_total = 0
    predict_all = np.array([], dtype=int)
    labels_all = np.array([], dtype=int)
    with torch.no_grad():
        for texts, labels in test_iter:
            outputs = model(texts)
            loss = F.cross_entropy(outputs, labels)
            loss_total += loss.item()
            labels = labels.detach().cpu().numpy()
            predic = torch.max(outputs.data, 1)[1].detach().cpu().numpy()
            labels_all = np.append(labels_all, labels)
            predict_all = np.append(predict_all, predic)
    acc = metrics.accuracy_score(labels_all, predict_all)
    report = metrics.classification_report(labels_all, predict_all, output_dict=True)
    confusion = metrics.confusion_matrix(labels_all, predict_all)
    logger.info("\nConfusion Matrix:\n%s", confusion)
    return acc, loss_total / len(test_iter), report, confusion


def evaluate(config, model, data_iter, test=False):
    model.eval()
    loss_total = 0
    predict_all = np.array([], dtype=int)
    labels_all = np.array([], dtype=int)
    with torch.no_grad():
        for texts, labels in data_iter:
            outputs = model(texts)
            loss = F.cross_entropy(outputs, labels)
            loss_total += loss.item()
            labels = labels.data.cpu().numpy()
            predic = torch.max(outputs.data, 1)[1].cpu().numpy()
            labels_all = np.append(labels_all, labels)
            predict_all = np.append(predict_all, predic)
    acc = metrics.accuracy_score(labels_all, predict_all)
    if test:
        report = metrics.classification_report(labels_all, predict_all, target_names=config.class_list, digits=4)
        confusion = metrics.confusion_matrix(labels_all, predict_all)
        return acc, loss_total / len(data_iter), report, confusion
    return acc, loss_total / len(data_iter)
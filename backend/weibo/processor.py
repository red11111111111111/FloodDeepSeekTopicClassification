# -*- coding: utf-8 -*-
import sys
import os
import logging
import time
import signal
import threading
from weibo.redis_queue import RedisQueue
from weibo.clean import TextCleaner  # 使用现有的文本清洗功能
from weibo.qwen_classifier import QwenClassifier  # 使用现有的分类功能
from weibo.items import WeiboCleanedItem, WeiboClassifiedItem
from weibo.pipelines import WeiboCleanedPipeline, WeiboClassifiedPipeline
from scrapy.utils.project import get_project_settings
from datetime import datetime

# 添加项目根目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
settings = get_project_settings()
logger = logging.getLogger(__name__)

# 全局控制变量
should_stop = False
processing_lock = threading.Lock()


def signal_handler(signum, frame):
    """信号处理函数"""
    global should_stop
    logger.info(f"收到信号 {signum}，准备优雅停止...")
    should_stop = True


def process_single_item(item, cleaner, classifier):
    """处理单个数据项"""
    try:
        if not isinstance(item, dict) or 'weibo' not in item:
            logger.error(f"从 Redis 队列获取的 item 格式错误: {item}")
            return False

        weibo = item['weibo']
        keyword = item.get('keyword', '')
        logger.debug(f"处理 item: {weibo['id']}, keyword: {keyword}")

        # 清洗文本
        cleaned_text = cleaner.clean_text(weibo['text'])

        # 创建 WeiboCleanedItem
        cleaned_item = WeiboCleanedItem()
        cleaned_item['id'] = weibo['id']
        cleaned_item['screen_name'] = weibo['screen_name']
        cleaned_item['cleaned_text'] = cleaned_text
        cleaned_item['created_at'] = weibo['created_at']
        cleaned_item['location'] = weibo.get('location', '')  # 新增：从原始 weibo 传递 location
        cleaned_item['insert_time'] = datetime.now()  # 新增：设置插入时间

        # 存储清洗后的数据
        try:
            pipeline = WeiboCleanedPipeline()
            pipeline.open_spider(None)
            pipeline.process_item(cleaned_item, None)
            pipeline.close_spider(None)
            logger.info(f"成功存储清洗数据: {weibo['id']}")
        except Exception as e:
            logger.error(f"存储清洗数据失败: {e}")
            return False

        # 分类
        category = classifier.classify(cleaned_text)  # ✅ 改成 classify

        # 创建 WeiboClassifiedItem
        classified_item = WeiboClassifiedItem()
        classified_item['id'] = weibo['id']
        classified_item['screen_name'] = weibo['screen_name']
        classified_item['cleaned_text'] = cleaned_text
        classified_item['created_at'] = weibo['created_at']
        classified_item['category'] = category if category else '未知'
        classified_item['location'] = weibo.get('location', '')  # 新增
        classified_item['insert_time'] = datetime.now()  # 新增

        try:
            pipeline = WeiboClassifiedPipeline()
            pipeline.open_spider(None)
            pipeline.process_item(classified_item, None)
            pipeline.close_spider(None)
            logger.info(f"成功存储分类数据: {weibo['id']}, 类别: {category}")

        except Exception as e:
            logger.error(f"存储分类数据失败: {e}")
            return False

        return True

    except Exception as e:
        logger.error(f"处理数据项失败: {e}")
        return False


def check_queue_empty(queue, check_times=3, interval=2):
    """检查队列是否为空（连续检查多次确认）"""
    for i in range(check_times):
        if queue.redis_client.llen(queue.queue_name) == 0:
            if i < check_times - 1:
                time.sleep(interval)
            else:
                return True
        else:
            return False
    return True


def process_queue():
    """处理队列中的数据"""
    global should_stop

    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    queue = RedisQueue()
    cleaner = TextCleaner()
    classifier = QwenClassifier(base_url="http://127.0.0.1:8000")

    logger.info("数据处理器启动，开始监听Redis队列...")

    processed_count = 0
    idle_count = 0
    max_idle_count = 10  # 最大空闲次数

    try:
        while not should_stop:
            with processing_lock:
                item = queue.pop()

                if not item:
                    idle_count += 1
                    if idle_count >= max_idle_count:
                        # 连续多次没有数据，检查队列是否真的为空
                        if check_queue_empty(queue):
                            logger.debug("队列为空，等待新数据...")
                            idle_count = 0
                    time.sleep(2)  # 减少空转时的资源消耗
                    continue

                idle_count = 0
                success = process_single_item(item, cleaner, classifier)

                if success:
                    processed_count += 1
                    if processed_count % 10 == 0:
                        logger.info(f"已处理 {processed_count} 条数据")

    except Exception as e:
        logger.error(f"处理队列时发生错误: {e}")

    finally:
        # 处理剩余数据
        if should_stop:
            logger.info("正在进行剩余数据操作...")
            remaining_count = process_remaining_data(queue, cleaner, classifier)
            logger.info(f"数据处理器停止，总共处理了 {processed_count + remaining_count} 条数据")
        else:
            logger.info(f"数据处理器正常结束，总共处理了 {processed_count} 条数据")


def process_remaining_data(queue, cleaner, classifier):
    """处理剩余数据"""
    remaining_count = 0
    logger.info("开始处理剩余数据...")

    try:
        while True:
            item = queue.pop()
            if not item:
                # 再次确认队列为空
                if check_queue_empty(queue, check_times=2, interval=1):
                    break
                continue

            success = process_single_item(item, cleaner, classifier)
            if success:
                remaining_count += 1
                logger.info(f"处理剩余数据: {remaining_count}")

    except Exception as e:
        logger.error(f"处理剩余数据时出错: {e}")

    if remaining_count > 0:
        logger.info(f"剩余数据处理完成，共处理 {remaining_count} 条")
    else:
        logger.info("无剩余数据需要处理")

    return remaining_count


def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler('processor.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logger.info("启动微博数据处理器...")
    process_queue()


if __name__ == "__main__":
    main() 
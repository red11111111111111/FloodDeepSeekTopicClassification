#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时数据处理器
使用Redis队列进行数据处理
"""
import logging
from weibo.processor import process_queue

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def start_redis_processor():
    """启动Redis队列处理器"""
    logger.info("启动基于Redis队列的数据处理器...")
    process_queue()

if __name__ == "__main__":
    start_redis_processor()
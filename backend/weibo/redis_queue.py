# -*- coding: utf-8 -*-
import redis
import json
import logging
from scrapy.utils.project import get_project_settings

settings = get_project_settings()
logger = logging.getLogger(__name__)

class RedisQueue:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.get('REDIS_HOST', 'localhost'),
            port=settings.get('REDIS_PORT', 6379),
            db=settings.get('REDIS_DB', 0),
            password=settings.get('REDIS_PASSWORD', None),
            decode_responses=True
        )
        self.queue_name = 'weibo:items'

    def push(self, item):
        """将 item 推送到 Redis 队列"""
        try:
            item_dict = dict(item)
            item_json = json.dumps(item_dict, ensure_ascii=False)
            self.redis_client.lpush(self.queue_name, item_json)
            logger.info(f"成功推送 item 到 Redis 队列: {item['weibo']['id']}")
        except Exception as e:
            logger.error(f"推送 item 到 Redis 队列失败: {e}")

    def pop(self):
        """从 Redis 队列获取 item"""
        try:
            item_json = self.redis_client.rpop(self.queue_name)
            if item_json:
                item_dict = json.loads(item_json)
                logger.info(f"成功从 Redis 队列获取 item: {item_dict['weibo']['id']}")
                return item_dict
            return None
        except Exception as e:
            logger.error(f"从 Redis 队列获取 item 失败: {e}")
            return None

    def get_queue_length(self):
        """获取队列长度"""
        try:
            return self.redis_client.llen(self.queue_name)
        except Exception as e:
            logger.error(f"获取队列长度失败: {e}")
            return 0

    def clear_queue(self):
        """清空队列"""
        try:
            self.redis_client.delete(self.queue_name)
            logger.info(f"已清空队列: {self.queue_name}")
        except Exception as e:
            logger.error(f"清空队列失败: {e}")

    def get_stats(self):
        """获取队列统计信息"""
        return {
            'queue_length': self.get_queue_length(),
            'queue_name': self.queue_name
        }
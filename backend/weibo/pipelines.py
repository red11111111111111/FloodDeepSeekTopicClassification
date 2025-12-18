# -*- coding: utf-8 -*-
import copy
import csv
import os
import logging
import pymysql
import scrapy
from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings
from weibo.items import WeiboItem, WeiboCleanedItem, WeiboClassifiedItem
from weibo.redis_queue import RedisQueue

settings = get_project_settings()
logger = logging.getLogger(__name__)

class CsvPipeline(object):
    def process_item(self, item, spider):
        base_dir = '结果文件' + os.sep + item['keyword']
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)
        file_path = base_dir + os.sep + item['keyword'] + '.csv'
        if not os.path.isfile(file_path):
            is_first_write = 1
        else:
            is_first_write = 0

        if item:
            with open(file_path, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                if is_first_write:
                    header = [
                        'id', 'bid', 'user_id', '用户昵称', '微博正文', '头条文章url',
                        '发布位置', '艾特用户', '话题', '转发数', '评论数', '点赞数', '发布时间',
                        '发布工具', '微博图片url', '微博视频url', 'retweet_id', 'ip', 'user_authentication'
                    ]
                    writer.writerow(header)

                writer.writerow([
                    item['weibo'].get('id', ''),
                    item['weibo'].get('bid', ''),
                    item['weibo'].get('user_id', ''),
                    item['weibo'].get('screen_name', ''),
                    item['weibo'].get('text', ''),
                    item['weibo'].get('article_url', ''),
                    item['weibo'].get('location', ''),
                    item['weibo'].get('at_users', ''),
                    item['weibo'].get('topics', ''),
                    item['weibo'].get('reposts_count', ''),
                    item['weibo'].get('comments_count', ''),
                    item['weibo'].get('attitudes_count', ''),
                    item['weibo'].get('created_at', ''),
                    item['weibo'].get('source', ''),
                    ','.join(item['weibo'].get('pics', [])),
                    item['weibo'].get('video_url', ''),
                    item['weibo'].get('retweet_id', ''),
                    item['weibo'].get('ip', ''),
                    item['weibo'].get('user_authentication', '')
                ])
        return item

class MysqlPipeline(object):
    def create_database(self, mysql_config):
        import pymysql
        sql = """CREATE DATABASE IF NOT EXISTS %s DEFAULT
                 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci""" % settings.get(
            'MYSQL_DATABASE', 'weibo')
        db = pymysql.connect(**mysql_config)
        cursor = db.cursor()
        cursor.execute(sql)
        db.close()

    def create_table(self):
        sql = """
                CREATE TABLE IF NOT EXISTS weibo (
                id varchar(20) NOT NULL,
                bid varchar(12) NOT NULL,
                user_id varchar(20),
                screen_name varchar(30),
                text varchar(2000),
                article_url varchar(100),
                topics varchar(200),
                at_users varchar(1000),
                pics varchar(3000),
                video_url varchar(1000),
                location varchar(100),
                created_at DATETIME,
                source varchar(30),
                attitudes_count INT,
                comments_count INT,
                reposts_count INT,
                retweet_id varchar(20),
                ip varchar(100),
                user_authentication varchar(100),
                insert_time DATETIME,  # 新增字段
                PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        self.cursor.execute(sql)

    def open_spider(self, spider):
        try:
            import pymysql
            mysql_config = {
                'host': settings.get('MYSQL_HOST', 'localhost'),
                'port': settings.get('MYSQL_PORT', 3306),
                'user': settings.get('MYSQL_USER', 'root'),
                'password': settings.get('MYSQL_PASSWORD', 'chen55322697'),
                'charset': 'utf8mb4'
            }
            self.create_database(mysql_config)
            mysql_config['db'] = settings.get('MYSQL_DATABASE', 'weibo')
            self.db = pymysql.connect(**mysql_config)
            self.cursor = self.db.cursor()
            self.create_table()
        except ImportError:
            spider.pymysql_error = True
        except pymysql.OperationalError:
            spider.mysql_error = True

    def process_item(self, item, spider):
        data = dict(item['weibo'])
        data['pics'] = ','.join(data['pics'])
        keys = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        sql = """INSERT INTO {table}({keys}) VALUES ({values}) ON
                 DUPLICATE KEY UPDATE""".format(table='weibo', keys=keys, values=values)
        update = ','.join([" {key} = {key}".format(key=key) for key in data])
        sql += update
        try:
            self.cursor.execute(sql, tuple(data.values()))
            self.db.commit()
        except Exception:
            self.db.rollback()
        return item

    def close_spider(self, spider):
        try:
            self.db.close()
        except Exception:
            pass

class WeiboCleanedPipeline(object):
    def create_table(self):
        sql = """
                CREATE TABLE IF NOT EXISTS weibo_cleaned (
                id VARCHAR(50) NOT NULL,
                screen_name VARCHAR(30),
                cleaned_text TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                created_at DATETIME,
                PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        self.cursor.execute(sql)

    def open_spider(self, spider):
        try:
            import pymysql
            mysql_config = {
                'host': settings.get('MYSQL_HOST', 'localhost'),
                'port': settings.get('MYSQL_PORT', 3306),
                'user': settings.get('MYSQL_USER', 'root'),
                'password': settings.get('MYSQL_PASSWORD', 'chen55322697'),
                'charset': 'utf8mb4',
                'db': settings.get('MYSQL_DATABASE', 'weibo')
            }
            self.db = pymysql.connect(**mysql_config)
            self.cursor = self.db.cursor()
            self.create_table()
        except ImportError:
            spider.pymysql_error = True
        except pymysql.OperationalError:
            spider.mysql_error = True

    def process_item(self, item, spider):
        if isinstance(item, WeiboCleanedItem):
            data = dict(item)
            keys = ', '.join(data.keys())
            values = ', '.join(['%s'] * len(data))
            sql = """INSERT INTO weibo_cleaned ({keys}) VALUES ({values}) ON
                     DUPLICATE KEY UPDATE""".format(keys=keys, values=values)
            update = ','.join([" {key} = %s".format(key=key) for key in data])
            sql += update
            try:
                self.cursor.execute(sql, tuple(data.values()) + tuple(data.values()))
                self.db.commit()
            except Exception as e:
                logger.error(f"存储清洗数据失败: {e}")
                self.db.rollback()
        return item

    def close_spider(self, spider):
        try:
            self.db.close()
        except Exception:
            pass

class WeiboClassifiedPipeline(object):
    def create_table(self):
        sql = """
                CREATE TABLE IF NOT EXISTS weibo_classified (
                id VARCHAR(50) NOT NULL,
                screen_name VARCHAR(30),
                cleaned_text TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                created_at DATETIME,
                category VARCHAR(50),
                location VARCHAR(100),
                PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        self.cursor.execute(sql)

    def open_spider(self, spider):
        try:
            import pymysql
            mysql_config = {
                'host': settings.get('MYSQL_HOST', 'localhost'),
                'port': settings.get('MYSQL_PORT', 3306),
                'user': settings.get('MYSQL_USER', 'root'),
                'password': settings.get('MYSQL_PASSWORD', 'chen55322697'),
                'charset': 'utf8mb4',
                'db': settings.get('MYSQL_DATABASE', 'weibo')
            }
            self.db = pymysql.connect(**mysql_config)
            self.cursor = self.db.cursor()
            self.create_table()
        except ImportError:
            spider.pymysql_error = True
        except pymysql.OperationalError:
            spider.mysql_error = True

    def process_item(self, item, spider):
        if isinstance(item, WeiboClassifiedItem):
            data = dict(item)
            keys = ', '.join(data.keys())
            values = ', '.join(['%s'] * len(data))
            sql = """INSERT INTO weibo_classified ({keys}) VALUES ({values}) ON
                     DUPLICATE KEY UPDATE""".format(keys=keys, values=values)
            update = ','.join([" {key} = %s".format(key=key) for key in data])
            sql += update
            try:
                self.cursor.execute(sql, tuple(data.values()) + tuple(data.values()))
                self.db.commit()
            except Exception as e:
                logger.error(f"存储分类数据失败: {e}")
                self.db.rollback()
        return item

    def close_spider(self, spider):
        try:
            self.db.close()
        except Exception:
            pass

class DuplicatesPipeline(object):
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if isinstance(item, dict) and 'weibo' in item and item['weibo']['id'] in self.ids_seen:
            raise DropItem("过滤重复微博: %s" % item)
        elif isinstance(item, dict) and 'weibo' in item:
            self.ids_seen.add(item['weibo']['id'])
        return item

class RedisPipeline(object):
    def __init__(self):
        self.queue = RedisQueue()
        logger.debug("RedisPipeline 初始化完成")

    def process_item(self, item, spider):
        logger.debug(f"RedisPipeline 开始处理 item: {item.get('weibo', {}).get('id', '未知')}")
        if isinstance(item, dict) and 'weibo' in item:
            # 将 WeiboItem 转换为参考项目的格式: {'weibo': {}, 'keyword': ''}
            item_dict = {
                'weibo': dict(item['weibo']),
                'keyword': item['keyword']
            }
            logger.debug(f"准备推送 dict 类型 item 到 Redis: {item_dict['weibo']['id']}")
            self.queue.push(item_dict)
            logger.debug(f"RedisPipeline 完成推送 item: {item_dict['weibo']['id']}")
        else:
            logger.debug(f"跳过非 dict 类型 item: {type(item)}")
        return item
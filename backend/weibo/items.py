# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WeiboItem(scrapy.Item):
    id = scrapy.Field()
    bid = scrapy.Field()
    user_id = scrapy.Field()
    screen_name = scrapy.Field()
    text = scrapy.Field()
    article_url = scrapy.Field()
    location = scrapy.Field()
    at_users = scrapy.Field()
    topics = scrapy.Field()
    reposts_count = scrapy.Field()
    comments_count = scrapy.Field()
    attitudes_count = scrapy.Field()
    created_at = scrapy.Field()
    source = scrapy.Field()
    pics = scrapy.Field()
    video_url = scrapy.Field()
    retweet_id = scrapy.Field()
    ip = scrapy.Field()
    user_authentication = scrapy.Field()
    keyword = scrapy.Field()


# 文件: items.py

class WeiboCleanedItem(scrapy.Item):
    id = scrapy.Field()
    screen_name = scrapy.Field()
    cleaned_text = scrapy.Field()
    created_at = scrapy.Field()
    location = scrapy.Field()  # 新增
    insert_time = scrapy.Field()  # 新增

class WeiboClassifiedItem(scrapy.Item):
    id = scrapy.Field()
    screen_name = scrapy.Field()
    cleaned_text = scrapy.Field()
    created_at = scrapy.Field()
    category = scrapy.Field()
    location = scrapy.Field()  # 新增
    insert_time = scrapy.Field()  # 新增
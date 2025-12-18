# -*- coding: utf-8 -*-
# qwen_classifier.py （实际是 Deepseek 分类器，但接口兼容）
import requests
import logging

class QwenClassifier:
    def __init__(self, api_key=None, proxy_url=None, base_url="http://127.0.0.1:8000"):
        """
        为了兼容原有调用方式，保留 api_key 和 proxy_url 参数（但不再使用）
        新增 base_url 指向 AutoDL 上的 Deepseek 分类服务
        """
        # 如果你愿意，也可以从环境变量读取 base_url
        self.base_url = base_url.rstrip("/")
        self.categories = ['救援', '祈福祝愿', '求助', '无关', '预警', '灾情', '指南']
        self.timeout = 15

    def classify(self, text):
        """
        调用 AutoDL 上的 Deepseek 分类服务
        """
        try:
            response = requests.post(
                f"{self.base_url}/classify",
                json={"text": text},
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            category = result.get("category")

            if category in self.categories:
                return category
            else:
                logging.warning(f"Deepseek 返回未知类别: {category}，原文: {text[:30]}...")
                return None

        except requests.exceptions.Timeout:
            logging.error("Deepseek 分类服务请求超时")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Deepseek 分类服务连接失败: {e}")
            return None
        except Exception as e:
            logging.error(f"Deepseek 分类异常: {e}")
            return None
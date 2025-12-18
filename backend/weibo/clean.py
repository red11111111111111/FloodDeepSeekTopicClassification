import re
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextCleaner:
    def __init__(self):
        # 简化正则表达式
        self.url_pattern = re.compile(r'https?://\S+')
        self.emoji_pattern = re.compile(r'[\U0001F000-\U0001FFFF]')
        self.special_pattern = re.compile(r'[@＠#<>\|\\/\[\]\{\}\(\)][_\-\.\+\*=:;]*')
        self.char_pattern = re.compile(r'[^\w\s，。！？、]')

    def clean_text(self, text, *args, **kwargs):
        """清洗单条文本"""
        if not text or not isinstance(text, str):
            logger.warning("输入文本为空或无效")
            return ''
        try:
            start_time = time.time()
            text = self.url_pattern.sub('', text)
            text = self.emoji_pattern.sub('', text)
            text = self.special_pattern.sub('', text)
            text = self.char_pattern.sub('', text)
            text = ' '.join(text.split())
            if len(text) > 500:
                text = text[:500]
            logger.debug(f"清洗单条文本耗时: {time.time() - start_time:.4f} 秒, 结果: {text[:50]}...")
            return text
        except Exception as e:
            logger.error(f"清洗文本失败: {e}, 原始文本: {text[:50]}...")
            return ''

    def clean_text_batch(self, texts):
        """批量清洗文本"""
        if not texts:
            logger.warning("批量清洗输入为空")
            return []
        try:
            start_time = time.time()
            cleaned_texts = [self.clean_text(text) for text in texts]
            logger.info(f"批量清洗 {len(texts)} 条文本耗时: {time.time() - start_time:.4f} 秒")
            return cleaned_texts
        except Exception as e:
            logger.error(f"批量清洗失败: {e}")
            return [''] * len(texts)
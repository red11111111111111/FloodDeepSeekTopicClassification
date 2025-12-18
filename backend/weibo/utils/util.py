import sys
import re
from datetime import datetime, timedelta
from weibo.utils.region import region_dict

def standardize_date(created_at):
    """标准化微博发布时间"""
    if not created_at or not isinstance(created_at, str):
        raise ValueError(f"无效的 created_at 值: {created_at}")

    created_at = created_at.strip()
    try:
        if "刚刚" in created_at:
            return datetime.now().strftime("%Y-%m-%d %H:%M")
        elif "秒" in created_at:
            second = created_at[:created_at.find("秒")]
            second = timedelta(seconds=int(second))
            return (datetime.now() - second).strftime("%Y-%m-%d %H:%M")
        elif "分钟" in created_at:
            minute = created_at[:created_at.find("分钟")]
            minute = timedelta(minutes=int(minute))
            return (datetime.now() - minute).strftime("%Y-%m-%d %H:%M")
        elif "小时" in created_at:
            hour = created_at[:created_at.find("小时")]
            hour = timedelta(hours=int(hour))
            return (datetime.now() - hour).strftime("%Y-%m-%d %H:%M")
        elif "今天" in created_at:
            today = datetime.now().strftime('%Y-%m-%d')
            time_part = created_at.split("今天")[1].strip()
            return f"{today} {time_part}"
        elif "昨天" in created_at:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            time_part = created_at.split("昨天")[1].strip()
            return f"{yesterday} {time_part}"
        elif re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', created_at):
            return created_at  # 已经是标准格式
        elif re.match(r'\d{2}-\d{2} \d{2}:\d{2}', created_at):
            year = datetime.now().strftime("%Y")
            month = created_at[:2]
            day = created_at[3:5]
            time = created_at[6:]
            return f"{year}-{month}-{day} {time}"
        elif re.match(r'\d{4}年\d{1,2}月\d{1,2}日\d{2}:\d{2}', created_at):
            # 处理 2024年11月03日20:00 格式
            return datetime.strptime(created_at, '%Y年%m月%d日%H:%M').strftime("%Y-%m-%d %H:%M")
        elif re.match(r'\d{1,2}月\d{1,2}日\d{2}:\d{2}', created_at):
            # 处理 03月25日23:59 格式
            year = datetime.now().strftime("%Y")
            month = re.search(r'(\d{1,2})月', created_at).group(1)
            day = re.search(r'(\d{1,2})日', created_at).group(1)
            time = re.search(r'(\d{2}:\d{2})', created_at).group(1)
            return f"{year}-{month.zfill(2)}-{day.zfill(2)} {time}"
        else:
            raise ValueError(f"未知的 created_at 格式: {created_at}")
    except Exception as e:
        raise ValueError(f"无法解析 created_at: {created_at}, 错误: {str(e)}")

def convert_weibo_type(weibo_type):
    """将微博类型转换成字符串"""
    if weibo_type == 0:
        return '&typeall=1'
    elif weibo_type == 1:
        return '&scope=ori'
    elif weibo_type == 2:
        return '&xsort=hot'
    elif weibo_type == 3:
        return '&atten=1'
    elif weibo_type == 4:
        return '&vip=1'
    elif weibo_type == 5:
        return '&category=4'
    elif weibo_type == 6:
        return '&viewpoint=1'
    return '&scope=ori'

def convert_contain_type(contain_type):
    """将包含类型转换成字符串"""
    if contain_type == 0:
        return '&suball=1'
    elif contain_type == 1:
        return '&haspic=1'
    elif contain_type == 2:
        return '&hasvideo=1'
    elif contain_type == 3:
        return '&hasmusic=1'
    elif contain_type == 4:
        return '&haslink=1'
    return '&suball=1'

def get_keyword_list(file_name):
    """获取文件中的关键词列表"""
    with open(file_name, 'rb') as f:
        try:
            lines = f.read().splitlines()
            lines = [line.decode('utf-8-sig') for line in lines]
        except UnicodeDecodeError:
            print(u'%s文件应为utf-8编码，请先将文件编码转为utf-8再运行程序', file_name)
            sys.exit()
        keyword_list = []
        for line in lines:
            if line:
                keyword_list.append(line)
    return keyword_list

def get_regions(region):
    """根据区域筛选条件返回符合要求的region"""
    new_region = {}
    if region:
        for key in region:
            if region_dict.get(key):
                new_region[key] = region_dict[key]
    if not new_region:
        new_region = region_dict
    return new_region

def str_to_time(text):
    """将字符串转换成时间类型"""
    result = datetime.strptime(text, '%Y-%m-%d')
    return result
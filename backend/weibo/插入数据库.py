import pandas as pd
import pymysql
import logging
import time
import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_excel_to_mysql(excel_file, sheet_name='清洗_分类结果', db_table='weibo_classified'):
    """
    将Excel数据导入MySQL数据库。
    Excel列名: id, 用户昵称, 发布位置, 发布时间, 正文, 类别, X, Y
    对应数据库字段: id, screen_name, location, created_at, cleaned_text, category, lng, lat

    :param excel_file: Excel文件路径
    :param sheet_name: Excel工作表名称
    :param db_table: 数据库表名
    """
    # 数据库连接配置
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'chen55322697', # 请确保密码正确且安全
        'database': 'weibo',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }

    # Excel列名到数据库字段名的映射
    column_mapping = {
        'id': 'id',
        '用户昵称': 'screen_name',
        '发布位置': 'location',
        '发布时间': 'created_at',
        '正文': 'cleaned_text',
        '类别': 'category', # 如果Excel中是'类别'，数据库是'category'
        'X': 'lng',
        'Y': 'lat'
    }

    try:
        # 读取Excel文件
        logger.info(f"开始读取Excel文件: {excel_file}, 工作表: {sheet_name}")
        start_time = time.time()
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        logger.info(f"成功读取Excel文件, 共 {len(df)} 条记录, 耗时: {time.time() - start_time:.2f}秒")

        # 检查数据是否为空
        if df.empty:
            logger.warning("Excel文件中没有数据")
            return False

        # 检查必要的Excel列是否存在
        missing_excel_cols = [col for col in column_mapping.keys() if col not in df.columns]
        if missing_excel_cols:
            logger.error(f"错误: Excel中缺少以下必要列: {', '.join(missing_excel_cols)}")
            return False

        # 重命名DataFrame的列以匹配数据库字段
        df.rename(columns=column_mapping, inplace=True)
        logger.info(f"列名已根据映射关系重命名: {column_mapping}")

        # 可选：处理日期时间格式（如果需要确保是datetime类型）
        # df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce') # errors='coerce' 将无效解析设置为NaT

        # 建立数据库连接
        logger.info("正在连接MySQL数据库...")
        connection = pymysql.connect(**db_config)
        logger.info("数据库连接成功")

        # 检查表是否存在
        with connection.cursor() as cursor:
            cursor.execute(f"SHOW TABLES LIKE %s", (db_table,))
            if not cursor.fetchone():
                logger.error(f"数据库表 {db_table} 不存在")
                return False

            # 获取目标表的字段信息
            cursor.execute(f"DESCRIBE {db_table}")
            table_columns_info = cursor.fetchall()
            table_columns = [column['Field'] for column in table_columns_info]

        # 检查重命名后的DataFrame列是否都存在于数据库表中
        # (因为我们是按数据库字段来重命名的，这一步主要是确认没有多余的列被映射到不存在的字段)
        df_columns = df.columns.tolist()
        extra_df_cols = [col for col in df_columns if col not in table_columns]
        if extra_df_cols:
             logger.warning(f"警告: DataFrame中存在数据库表 {db_table} 中没有的字段: {', '.join(extra_df_cols)}。这些列将被忽略。")

        # 准备插入语句 - 使用 INSERT IGNORE 跳过重复记录 (基于主键或唯一索引)
        # 过滤掉DataFrame中不存在于数据库表的列
        columns_to_insert = [col for col in df_columns if col in table_columns]
        columns_str = ', '.join(columns_to_insert)
        placeholders_str = ', '.join(['%s'] * len(columns_to_insert))
        insert_query = f"INSERT IGNORE INTO {db_table} ({columns_str}) VALUES ({placeholders_str})"
        logger.info(f"准备使用的插入语句: {insert_query}")

        # 准备批量插入数据
        data_to_insert = []
        for _, row in df.iterrows():
            # 为每一行创建一个元组，只包含要插入的列的值
            row_data = tuple(row[col] if pd.notna(row[col]) else None for col in columns_to_insert)
            data_to_insert.append(row_data)

        # 执行批量插入
        logger.info(f"开始插入数据到数据库表 {db_table}...")
        batch_start_time = time.time()

        inserted_count = 0
        total_rows = len(data_to_insert)
        batch_size = 1000 # 可根据需要调整

        with connection.cursor() as cursor:
            for i in range(0, total_rows, batch_size):
                batch = data_to_insert[i:i + batch_size]
                cursor.executemany(insert_query, batch)
                connection.commit()
                inserted_count += cursor.rowcount
                logger.info(f"已处理 {min(i + batch_size, total_rows)}/{total_rows} 条记录 (本次插入 {cursor.rowcount} 条)")

        skipped_count = total_rows - inserted_count
        logger.info(
            f"数据导入完成。成功插入 {inserted_count} 条记录, 跳过 {skipped_count} 条重复或无效记录, 总耗时: {time.time() - batch_start_time:.2f}秒")

        return True

    except pymysql.Error as e:
        logger.error(f"数据库操作错误: {e}")
        return False

    except Exception as e:
        logger.error(f"处理过程中发生错误: {e}", exc_info=True) # 添加 exc_info=True 以获取更详细的错误堆栈
        return False

    finally:
        # 确保关闭数据库连接
        if 'connection' in locals() and connection.open:
            connection.close()
            logger.info("数据库连接已关闭")


# 使用示例
if __name__ == "__main__":
    excel_file = r"E:\Experiment\淹没过程可视化\数据处理\7.17-7.24\清洗_分类结果.xlsx"  # 替换为你的Excel文件路径
    sheet_name = "清洗_分类结果"  # 替换为你的工作表名称

    success = import_excel_to_mysql(excel_file, sheet_name)

    if success:
        print("数据导入成功！")
    else:
        print("数据导入过程中出现错误，请检查日志")





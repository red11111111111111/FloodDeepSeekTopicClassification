import pymysql
from pymysql.constants import CLIENT
from datetime import datetime

class Database:
    def __init__(self, config=None):
        self.config = config or {
            'host': 'localhost',
            'user': 'root',
            'password': 'chen55322697',
            'database': 'weibo',
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            'client_flag': CLIENT.MULTI_STATEMENTS,
            'connect_timeout': 10,
            'read_timeout': 30,
            'write_timeout': 30
        }
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = pymysql.connect(**self.config)
            print('使用pymysql连接到MySQL数据库')
            self._initialize_tables()
        except pymysql.Error as e:
            print(f"连接MySQL错误: {e}")
            raise

    def _initialize_tables(self):
        """初始化必要的表"""
        self._ensure_table_exists("weibo_cleaned", """
            CREATE TABLE weibo_cleaned (
                id VARCHAR(50) PRIMARY KEY,
                screen_name VARCHAR(30),
                cleaned_text TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                location VARCHAR(100),
                created_at DATETIME,
                insert_time DATETIME
            )
        """)
        self._ensure_table_exists("weibo_classified", """
            CREATE TABLE weibo_classified (
                id VARCHAR(50) PRIMARY KEY,
                screen_name VARCHAR(30),
                cleaned_text TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                location VARCHAR(100),
                category VARCHAR(20),
                created_at DATETIME,
                insert_time DATETIME
            )
        """)

    def save_cleaned_text_single(self, record_id, cleaned_text, screen_name, location, created_at, insert_time):
        """保存单个清洗结果"""
        try:
            with self.connection.cursor() as cursor:
                cleaned_text = cleaned_text.encode('utf-8', errors='ignore').decode('utf-8')
                cursor.execute("""
                    INSERT INTO weibo_cleaned (id, cleaned_text, screen_name, location, created_at, insert_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE cleaned_text = %s, screen_name = %s, location = %s, created_at = %s
                """, (record_id, cleaned_text, screen_name, location, created_at, insert_time, 
                      cleaned_text, screen_name, location, created_at))
                self.connection.commit()
                print(f"成功保存清洗记录: {record_id}")
        except pymysql.Error as e:
            print(f"保存清洗结果错误: {e}")
            self.connection.rollback()
            raise

    def save_classified_result_single(self, text_id, text, screen_name, location, created_at, category, insert_time):
        """保存单个分类结果"""
        try:
            with self.connection.cursor() as cursor:
                text = text.encode('utf-8', errors='ignore').decode('utf-8')
                cursor.execute("""
                    INSERT INTO weibo_classified (id, cleaned_text, screen_name, location, created_at, category, insert_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE cleaned_text = %s, screen_name = %s, location = %s, created_at = %s, category = %s, insert_time = %s
                """, (text_id, text, screen_name, location, created_at, category, insert_time, 
                      text, screen_name, location, created_at, category, insert_time))
                self.connection.commit()
                print(f"成功保存分类记录: {text_id} -> {category}")
        except pymysql.Error as e:
            print(f"保存分类结果错误: {e}")
            self.connection.rollback()
            raise

    def close(self):
        if self.connection and self.connection.open:
            self.connection.close()
            print('数据库连接已关闭')

    def _ensure_table_exists(self, table_name, create_table_sql):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                if not cursor.fetchone():
                    cursor.execute(create_table_sql)
                    self.connection.commit()
                    print(f"创建表 {table_name}")
                else:
                    # 检查并添加location字段
                    cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE 'location'")
                    if not cursor.fetchone() and table_name in ['weibo_cleaned', 'weibo_classified']:
                        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN location VARCHAR(100) AFTER screen_name")
                        self.connection.commit()
                        print(f"向 {table_name} 表添加 location 字段")
        except pymysql.Error as e:
            print(f"创建或更新表 {table_name} 错误: {e}")
            self.connection.rollback()

    def refresh_connection(self):
        """刷新数据库连接"""
        if self.connection and self.connection.open:
            self.connection.close()
        self.connect()
        print("数据库连接已刷新")
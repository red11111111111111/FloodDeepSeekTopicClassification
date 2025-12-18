import os
import time
import json
import shutil
import logging
import subprocess
import urllib.parse
from datetime import datetime, timedelta
from multiprocessing import Process
from flask_socketio import SocketIO

import requests
import pymysql
import bcrypt
import torch
import pickle as pkl
import matplotlib
from flask import Flask, request, jsonify, render_template, send_file, session
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_socketio import emit
from werkzeug.utils import secure_filename

# project imports (keep these as in original)
from run import main
from config import Config
from model.TextCNN import Model
from compare_models import compare_models
from weibo.processor import process_queue
from weibo.redis_queue import RedisQueue
from weibo.clean import TextCleaner
from weibo.qwen_classifier import QwenClassifier
from weibo.items import WeiboCleanedItem, WeiboClassifiedItem
from weibo.pipelines import WeiboCleanedPipeline, WeiboClassifiedPipeline

# -------------------------
# Configuration
# -------------------------
matplotlib.set_loglevel("warning")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger.setLevel(logging.INFO)

# App & CORS
app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}, r"/predict": {"origins": "*"}})

app.secret_key = 'ce8a89a04dd2508b93f9d3b12d7045e90de8c2ddf1534796a6319ce8cd612ed7'
# SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# JWT
app.config['JWT_SECRET_KEY'] = ''
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)

# MySQL: note there are TWO MySQL configs in the original file. Keep both so behaviour is preserved.
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'chen55322697'
app.config['MYSQL_DB'] = 'myapp'  # used by register/login in original

MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'chen55322697',
    'database': 'weibo',
    'charset': 'utf8mb4',
}

# Uploads
UPLOAD_FOLDER = os.path.join(r'E:\Gezhengti_2 - 副本\backend\THUCNews', 'data')
ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024

# AMap (高德) Key
AMAP_KEY = "6f5894aff371b20019c78c2789dd5323"

# Globals for processes (preserve original behaviour)
crawl_process = None
processor_process = None

# -------------------------
# Utility functions
# -------------------------

def get_db_connection(database=None):
    config = {
        'host': app.config['MYSQL_HOST'],
        'user': app.config['MYSQL_USER'],
        'password': app.config['MYSQL_PASSWORD'],
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
    }
    if database:
        config['database'] = database
    else:
        config['database'] = app.config['MYSQL_DB']

    try:
        return pymysql.connect(**config)
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        raise


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def fmt_row_dates(row: dict, fields=('created_at', 'insert_time')):
    for f in fields:
        if f in row and row[f]:
            try:
                row[f] = row[f].strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                # already formatted or not a datetime
                pass


def geocode_location(address: str, timeout: float = 5.0):
    """Use AMap geocode API to convert address -> (lng, lat) or (None, None) on failure.
    Basic rate limiting (sleep) is handled by the caller.
    """
    if not address:
        return None, None
    try:
        encoded = urllib.parse.quote(address)
        url = f"https://restapi.amap.com/v3/geocode/geo?address={encoded}&key={AMAP_KEY}"
        r = requests.get(url, timeout=timeout)
        data = r.json()
        if data.get('status') == '1' and data.get('geocodes'):
            loc = data['geocodes'][0].get('location')
            if loc and ',' in loc:
                lng, lat = loc.split(',')
                return float(lng), float(lat)
        logger.debug("Geocode failed for %s, response: %s", address, data)
    except Exception as e:
        logger.error("Geocode API error for %s: %s", address, e)
    return None, None


# -------------------------
# Model / vocab loading
# -------------------------
config = Config()
try:
    vocab = pkl.load(open(config.vocab_path, 'rb'))
except Exception as e:
    logger.error("Failed to load vocab: %s", e)
    vocab = {}

model = Model(config).to(config.device)
try:
    # try a robust loading process compatible with different torch versions
    state = torch.load(config.save_path, map_location=config.device)
    if isinstance(state, dict):
        model.load_state_dict(state)
    else:
        model.load_state_dict(state.state_dict())
    model.eval()
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error("Failed to load model state: %s", e)


def preprocess(sentence: str):
    tokenizer = lambda x: [y for y in x]
    tokens = tokenizer(sentence)
    if len(tokens) < config.pad_size:
        tokens.extend(['<PAD>'] * (config.pad_size - len(tokens)))
    else:
        tokens = tokens[:config.pad_size]
    word_ids = [vocab.get(word, vocab.get('<UNK>')) for word in tokens]
    return torch.LongTensor([word_ids]).to(config.device)


# -------------------------
# Settings updater
# -------------------------

def update_settings(params: dict):
    """Update weibo/settings.py with provided parameters.
    This preserves the original behaviour but simplifies parsing.
    """
    settings_path = os.path.join(os.getcwd(), 'weibo', 'settings.py')
    if not os.path.exists(settings_path):
        raise FileNotFoundError(settings_path)

    cookie_value = params.get('cookie', '').replace('\n', '').replace('\r', '').strip()
    keyword_list = params.get('keyword_list', '')
    region = params.get('region', '')
    start_date = params.get('start_date', '')
    end_date = params.get('end_date', '')

    with open(settings_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Replace DEFAULT_REQUEST_HEADERS (simple approach: find start index)
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('DEFAULT_REQUEST_HEADERS'):
            start_idx = i
            break
    if start_idx is not None:
        # find end of dict
        end_idx = None
        for j in range(start_idx, min(start_idx + 50, len(lines))):
            if lines[j].strip().endswith('}'):
                end_idx = j
                break
        if end_idx is not None:
            new_headers = [
                "DEFAULT_REQUEST_HEADERS = {\n",
                "    'Accept': 'application/json, text/plain, */*',\n",
                "    'Accept-Encoding': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',\n",
                "    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',\n",
                f"    'cookie': '{cookie_value}'\n",
                "}\n",
            ]
            lines[start_idx:end_idx + 1] = new_headers
        else:
            lines.append('\n')
            lines.extend([
                "DEFAULT_REQUEST_HEADERS = {\n",
                "    'Accept': 'application/json, text/plain, */*',\n",
                "    'Accept-Encoding': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',\n",
                "    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',\n",
                f"    'cookie': '{cookie_value}'\n",
                "}\n",
            ])

    # Replace simple variable lines KEYWORD_LIST, REGION, START_DATE, END_DATE
    for i, line in enumerate(lines):
        if line.strip().startswith('KEYWORD_LIST'):
            keywords = [k.strip() for k in keyword_list.replace('，', ',').split(',') if k.strip()]
            lines[i] = f"KEYWORD_LIST = {keywords}\n"
        elif line.strip().startswith('REGION'):
            regions = [r.strip() for r in region.replace('，', ',').split(',') if r.strip()]
            lines[i] = f"REGION = {regions}\n"
        elif line.strip().startswith('START_DATE'):
            lines[i] = f"START_DATE = '{start_date}'\n"
        elif line.strip().startswith('END_DATE'):
            lines[i] = f"END_DATE = '{end_date}'\n"

    with open(settings_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    logger.info("settings.py updated")


# -------------------------
# Redis queue & processing helpers
# -------------------------

def start_processor():
    """Run the queue processor (intended to be launched in a separate process)."""
    try:
        logger.info("Starting data processor")
        process_queue()
    except Exception as e:
        logger.exception("Processor failed: %s", e)


def process_remaining_data():
    """Pop remaining items from Redis queue and process them through pipelines/classifier.
    This function is called when the crawler stops to ensure remaining items get persisted.
    """
    try:
        queue = RedisQueue()
        cleaner = TextCleaner()
        classifier = QwenClassifier(api_key="sk-c775e72afdb145ddbe8abdfa235b53af")

        remaining, processed = 0, 0
        while True:
            item = queue.pop()
            if not item:
                break
            remaining += 1
            try:
                if not isinstance(item, dict) or 'weibo' not in item:
                    logger.error("Invalid data in queue: %s", item)
                    continue
                weibo = item['weibo']
                cleaned_text = cleaner.clean_text(weibo.get('text', ''))

                cleaned_item = WeiboCleanedItem()
                cleaned_item['id'] = weibo.get('id')
                cleaned_item['screen_name'] = weibo.get('screen_name')
                cleaned_item['cleaned_text'] = cleaned_text
                cleaned_item['created_at'] = weibo.get('created_at')
                cleaned_item['location'] = weibo.get('location', '')
                cleaned_item['insert_time'] = datetime.now()

                pipeline = WeiboCleanedPipeline()
                pipeline.open_spider(None)
                pipeline.process_item(cleaned_item, None)
                pipeline.close_spider(None)

                category = classifier.classify(cleaned_text)

                classified_item = WeiboClassifiedItem()
                classified_item['id'] = weibo.get('id')
                classified_item['screen_name'] = weibo.get('screen_name')
                classified_item['cleaned_text'] = cleaned_text
                classified_item['created_at'] = weibo.get('created_at')
                classified_item['category'] = category or '未知'
                classified_item['location'] = weibo.get('location', '')
                classified_item['insert_time'] = datetime.now()

                pipeline = WeiboClassifiedPipeline()
                pipeline.open_spider(None)
                pipeline.process_item(classified_item, None)
                pipeline.close_spider(None)

                processed += 1
                logger.info("Processed remaining item %s (%d/%d)", weibo.get('id'), processed, remaining)
            except Exception as e:
                logger.exception("Failed to process queued item: %s", e)

        if processed:
            logger.info("Completed processing %d remaining item(s)", processed)
        else:
            logger.info("No remaining queue items to process")
    except Exception as e:
        logger.exception("Error while processing remaining data: %s", e)

# --- 把查询逻辑封装成函数，供 websocket 调用 ---
def fetch_help_messages(page=1, size=10, sort_prop='created_at', sort_order='DESC'):
    """
    获取分页的求助消息，并根据指定字段排序。

    Args:
        page (int): 页码 (从 1 开始)。
        size (int): 每页大小。
        sort_prop (str): 排序字段名。
        sort_order (str): 排序顺序 ('ASC' 或 'DESC')。

    Returns:
        list: 查询到的消息列表。
    """
    # 2. 定义允许排序的安全字段列表，防止 SQL 注入
    allowed_sort_fields = ['screen_name', 'cleaned_text', 'location', 'category', 'created_at', 'insert_time']

    # 3. 验证 sort_prop 是否在允许列表中，不在则使用默认值
    if sort_prop not in allowed_sort_fields:
        sort_prop = 'created_at'  # 默认排序字段

    # 4. 验证并规范化 sort_order
    sort_order = sort_order.upper()
    if sort_order not in ['ASC', 'DESC']:
        sort_order = 'DESC'  # 默认排序顺序

    conn = pymysql.connect(**MYSQL_CONFIG)
    try:  # 使用 try...finally 确保连接关闭
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # 5. 使用参数化查询和白名单验证构建安全的 SQL
            #    注意：表名和列名不能直接参数化，所以使用白名单验证
            query = f"""
                SELECT screen_name, cleaned_text, location, category, created_at, insert_time 
                FROM weibo_classified 
                WHERE category = '求助' 
                ORDER BY {sort_prop} {sort_order} 
                LIMIT %s OFFSET %s
            """
            offset = (page - 1) * size
            cur.execute(query, (size, offset))
            rows = cur.fetchall()
            for r in rows:
                fmt_row_dates(r)  # 格式化日期
        return rows
    except Exception as e:
        print(f"Error fetching help messages: {e}")  # 记录错误
        return []  # 返回空列表或其他错误指示
    finally:
        conn.close()  # 确保连接关闭

def fetch_help_locations():
    conn = pymysql.connect(**MYSQL_CONFIG)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SHOW TABLES LIKE 'weibo_classified'")
        if not cur.fetchone():
            conn.close()
            return []
        cur.execute("SHOW COLUMNS FROM weibo_classified LIKE 'lng'")
        if not cur.fetchone():
            cur.execute("ALTER TABLE weibo_classified ADD COLUMN lng FLOAT")
            conn.commit()
        cur.execute("SHOW COLUMNS FROM weibo_classified LIKE 'lat'")
        if not cur.fetchone():
            cur.execute("ALTER TABLE weibo_classified ADD COLUMN lat FLOAT")
            conn.commit()
        query = ("SELECT id, screen_name, cleaned_text, location, created_at, insert_time, lng, lat "
                 "FROM weibo_classified WHERE category = '求助' AND location IS NOT NULL AND location != '' ORDER BY insert_time DESC")
        cur.execute(query)
        rows = cur.fetchall()
        for row in rows:
            fmt_row_dates(row)
            if not row.get('lng') or not row.get('lat'):
                location = (row.get('location') or '').replace('·', '')
                lng, lat = geocode_location(location)
                time.sleep(0.4)
                if lng and lat:
                    row['lng'] = lng
                    row['lat'] = lat
                    try:
                        cur.execute("UPDATE weibo_classified SET lng = %s, lat = %s WHERE id = %s", (lng, lat, row['id']))
                        conn.commit()
                    except Exception:
                        logger.exception("Failed to update lng/lat for id=%s", row.get('id'))
                else:
                    row['lng'] = None
                    row['lat'] = None
    conn.close()
    return [r for r in rows if r.get('lng') and r.get('lat')]
def fetch_classified_data(category=None, start_date=None, end_date=None):
    conn = pymysql.connect(**MYSQL_CONFIG)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SHOW TABLES LIKE 'weibo_classified'")
        if not cur.fetchone():
            conn.close()
            return []
        query = "SELECT id, cleaned_text, screen_name, category, created_at, insert_time FROM weibo_classified WHERE 1=1"
        params = []
        if category:
            query += " AND category = %s"
            params.append(category)
        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)
        if end_date:
            query += " AND created_at <= %s"
            params.append(f"{end_date} 23:59:59")
        query += " ORDER BY insert_time DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        for r in rows:
            fmt_row_dates(r)
    conn.close()
    return rows

def fetch_categories():
    conn = pymysql.connect(**MYSQL_CONFIG)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SHOW TABLES LIKE 'weibo_classified'")
        if not cur.fetchone():
            conn.close()
            return []
        cur.execute("SELECT DISTINCT category FROM weibo_classified WHERE category IS NOT NULL")
        cats = [r['category'] for r in cur.fetchall() if r['category']]
    conn.close()
    return cats

def fetch_weibo_data(start_date=None, end_date=None):
    conn = pymysql.connect(**MYSQL_CONFIG)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        query = "SELECT * FROM weibo WHERE 1=1"
        params = []
        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)
        if end_date:
            query += " AND created_at <= %s"
            params.append(f"{end_date} 23:59:59")
        query += " ORDER BY insert_time DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        for r in rows:
            fmt_row_dates(r)
    conn.close()
    return rows

def fetch_cleaned_data(start_date=None, end_date=None):
    conn = pymysql.connect(**MYSQL_CONFIG)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        query = "SELECT screen_name, cleaned_text, created_at, insert_time FROM weibo_cleaned WHERE 1=1"
        params = []
        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)
        if end_date:
            query += " AND created_at <= %s"
            params.append(f"{end_date} 23:59:59")
        query += " ORDER BY created_at DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        for r in rows:
            fmt_row_dates(r)
    conn.close()
    return rows

# -------------------------
# Routes
# -------------------------

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"message": "Token has expired"}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"message": "Invalid token"}), 401


@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({"message": "Missing or invalid Authorization header"}), 401


@app.route('/')
def inadex():
    return render_template('index.html')


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"message": "用户名和密码不能为空"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return jsonify({"message": "用户名已存在"}), 400
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
        conn.commit()
        return jsonify({"message": "注册成功"}), 200
    except Exception as e:
        logger.exception("Register failed: %s", e)
        return jsonify({"message": "注册失败", "error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"message": "用户名和密码不能为空"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                return jsonify({"message": "用户名或密码错误"}), 401
        token = create_access_token(identity=username)
        return jsonify({"token": token, "username": username}), 200
    except Exception as e:
        logger.exception("Login error: %s", e)
        return jsonify({"message": "登录失败", "error": str(e)}), 500
    finally:
        conn.close()


@app.route('/extract_crawler_data', methods=['POST'])
@jwt_required()
def extract_crawler_data():
    data = request.get_json() or {}
    count = data.get('count')
    if not isinstance(count, int) or count <= 0:
        return jsonify({"message": "请输入有效的提取数据条数"}), 400

    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("SHOW TABLES LIKE 'weibo_cleaned'")
            if not cur.fetchone():
                return jsonify({"message": "weibo_cleaned表不存在"}), 400
            cur.execute("SELECT COUNT(*) as total FROM weibo_cleaned")
            total_count = cur.fetchone()['total']
            if count > total_count:
                return jsonify({"message": f"输入的数量超出数据库数据总量，数据库中共有 {total_count} 条数据，请输入更小的值"}), 400
            cur.execute("SELECT text FROM weibo ORDER BY insert_time DESC LIMIT %s", (count,))
            rows = cur.fetchall()

        if not rows:
            return jsonify({"message": "weibo_cleaned表中没有数据"}), 400

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            for r in rows:
                t = (r.get('text') or '').strip()
                if t:
                    f.write(t + '\n')
        return jsonify({"message": "数据提取成功", "file_path": "test.txt"}), 200
    except pymysql.Error as e:
        logger.exception("Database error: %s", e)
        return jsonify({"message": f"数据库错误: {e}"}), 500
    except Exception as e:
        logger.exception("Extract crawler data error: %s", e)
        return jsonify({"message": f"数据提取失败: {e}"}), 500
    finally:
        if 'conn' in locals():
            conn.close()


@app.route('/download/test.txt', methods=['GET'])
@jwt_required()
def download_test_file():
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test.txt')
    if not os.path.exists(file_path):
        return jsonify({"message": "test.txt 文件不存在"}), 404
    return send_file(file_path, as_attachment=True, download_name='test.txt')


@app.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify({"message": "No selected file"}), 400
    if not allowed_file(f.filename):
        return jsonify({"message": "Invalid file format. Please upload a .txt file."}), 400

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filename = secure_filename(f.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(file_path)

    required_fields = ['dropout', 'num_epochs', 'batch_size', 'learning_rate', 'model']
    for field in required_fields:
        if field not in request.form:
            return jsonify({"message": f"Missing field: {field}"}), 400

    try:
        model_params = {
            'dropout': float(request.form['dropout']),
            'num_epochs': int(request.form['num_epochs']),
            'batch_size': int(request.form['batch_size']),
            'learning_rate': float(request.form['learning_rate']),
            'model': request.form['model']
        }
    except Exception:
        return jsonify({"message": "Invalid parameter format"}), 400

    try:
        metrics = main(file_path, model_params)
        metrics = {k: round(v, 3) for k, v in metrics.items()}
        resp = {
            "image_url": 'static/images/training_curve.png',
            "accuracy": metrics.get("accuracy"),
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall"),
            "f1_score": metrics.get("f1_score")
        }
        return jsonify(resp)
    except Exception as e:
        logger.exception("Training failed: %s", e)
        return jsonify({"message": "Training failed", "error": str(e)}), 500


@app.route('/api/compare_models', methods=['POST'])
@jwt_required()
def compare_models_endpoint():
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify({"message": "No selected file"}), 400
    if not allowed_file(f.filename):
        return jsonify({"message": "Invalid file format. Please upload a .txt file."}), 400

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filename = secure_filename(f.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(file_path)

    try:
        model1_params = json.loads(request.form['model1_params'])
        model2_params = json.loads(request.form['model2_params'])
    except Exception as e:
        logger.exception("Invalid model params: %s", e)
        return jsonify({"message": "Invalid model parameters format"}), 400

    required_fields = ['dropout', 'num_epochs', 'batch_size', 'learning_rate', 'model']
    for pset in (model1_params, model2_params):
        for field in required_fields:
            if field not in pset:
                return jsonify({"message": f"Missing field in model parameters: {field}"}), 400

    try:
        m1 = main(file_path, model1_params)
        m2 = main(file_path, model2_params)
        comp = compare_models(model1_params['model'], m1, model2_params['model'], m2)
        resp = {
            "bar_chart": comp['bar_chart'],
            "metrics": comp['metrics'],
            "model1_name": model1_params['model'],
            "model1_data": [m1['accuracy'], m1['precision'], m1['recall'], m1['f1_score']],
            "model2_name": model2_params['model'],
            "model2_data": [m2['accuracy'], m2['precision'], m2['recall'], m2['f1_score']],
        }
        return jsonify(resp)
    except Exception as e:
        logger.exception("Model comparison failed: %s", e)
        return jsonify({"message": "Model comparison failed", "error": str(e)}), 500


@app.route('/api/start_crawl', methods=['POST'])
@jwt_required()
def start_crawl():
    global crawl_process, processor_process
    try:
        params = request.get_json() or {}
        for k in ('cookie', 'keyword_list', 'region', 'start_date', 'end_date'):
            if k not in params:
                return jsonify({'error': '缺少必要参数'}), 400

        # 新增：记录初始求助信息条数
        conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=pymysql.cursors.DictCursor)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM weibo_classified WHERE category = '求助'")
            result = cur.fetchone()
            initial_count = result['count'] if result else 0
        conn.close()
        session['initial_help_count'] = initial_count
        logger.info(f"记录初始求助条数: {initial_count}")

        update_settings(params)

        scrapy_project_path = os.getcwd()
        scrapy_cfg_path = os.path.join(scrapy_project_path, 'scrapy.cfg')
        if not os.path.exists(scrapy_cfg_path):
            return jsonify({'error': f'Scrapy 项目配置文件不存在: {scrapy_cfg_path}'}), 500

        settings_path = os.path.join(scrapy_project_path, 'weibo', 'settings.py')
        if not os.path.exists(settings_path):
            return jsonify({'error': f'Settings 文件不存在: {settings_path}'}), 500

        crawls_path = os.path.join(scrapy_project_path, 'crawls')
        if os.path.exists(crawls_path):
            shutil.rmtree(crawls_path)

        # Start data processor
        if processor_process is None or not processor_process.is_alive():
            processor_process = Process(target=start_processor)
            processor_process.start()
            logger.info("Data processor started (pid=%s)", processor_process.pid)

        # make sure weibo module is importable
        env = os.environ.copy()
        env['PYTHONPATH'] = f"{scrapy_project_path}{os.pathsep}{env.get('PYTHONPATH', '')}"

        # start crawler
        try:
            crawl_process = subprocess.Popen(
                ['scrapy', 'crawl', 'search', '-s', 'JOBDIR=crawls/search'],
                cwd=scrapy_project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            logger.info("Crawler started (pid=%s)", crawl_process.pid)
        except Exception as e:
            logger.exception("Failed to start crawler: %s", e)
            return jsonify({'error': f'启动爬虫失败: {e}'}), 500

        time.sleep(2)
        if crawl_process.poll() is not None:
            stdout, stderr = crawl_process.communicate(timeout=10)
            logger.error("Crawler failed to start, stdout=%s, stderr=%s", stdout, stderr)
            return jsonify({'error': f'爬虫启动失败: {stderr}'}), 500

        return jsonify({'message': '爬虫和数据处理器已启动'}), 200
    except Exception as e:
        logger.exception("Crawler start error: %s", e)
        return jsonify({'error': f'爬虫启动异常: {e}'}), 500

@app.route('/api/stop_crawl', methods=['POST'])
@jwt_required()
def stop_crawl():
    global crawl_process, processor_process
    try:
        if crawl_process is not None and crawl_process.poll() is None:
            crawl_process.terminate()
            try:
                crawl_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                crawl_process.kill()
            logger.info("Crawler process terminated")
            crawl_process = None

            # 处理剩余数据
            logger.info("Processing remaining data after stop")
            process_remaining_data()

            # 计算新增求助信息条数
            conn = get_db_connection(database='weibo')
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM weibo_classified WHERE category = '求助'")
                result = cur.fetchone()
                current_count = result['count'] if result else 0
            conn.close()
            initial_count = session.get('initial_help_count', 0)
            new_help_count = max(0, current_count - initial_count)
            logger.info(f"新增求助信息条数: {new_help_count}")

            # 清空session记录
            session.pop('initial_help_count', None)

            return jsonify({
                'message': '爬虫已停止，数据处理完成',
                'new_help_count': new_help_count
            }), 200
        else:
            # 如果没有运行的爬虫，也返回当前求助数（以防意外）
            conn = pymysql.connect(**MYSQL_CONFIG)
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM weibo_classified WHERE category = '求助'")
                current_count = cur.fetchone()['count']
            conn.close()
            session.pop('initial_help_count', None)
            return jsonify({
                'message': '没有正在运行的爬虫',
                'new_help_count': 0
            }), 200
    except Exception as e:
        logger.exception("Failed to stop crawler: %s", e)
        return jsonify({'error': f'停止爬虫失败: {e}'}), 500

# --- Socket events for queries ---
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected: %s', request.sid)
    emit('connected', {'message': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected: %s', request.sid)


# 6. 更新 SocketIO 事件处理函数，使用新的默认值
@socketio.on('get_all_help_messages')  # 假设 socketio 是已初始化的实例
def ws_get_all_help_messages(payload):
    """
    WebSocket 事件处理函数，响应前端获取所有求助消息的请求。
    """
    try:
        # 7. 从 payload 获取参数，使用新的默认值
        page = int(payload.get('page', 1))
        size = int(payload.get('size', 10))
        # 注意：前端传递的 sort_prop 和 sort_order 可能为空或无效，
        # fetch_help_messages 内部会处理默认值和验证
        sort_prop = payload.get('sort_prop', 'created_at')  # 默认改为 created_at
        sort_order = payload.get('sort_order', 'DESC')  # 默认改为 DESC

        # 8. 调用获取数据的函数
        data = fetch_help_messages(page=page, size=size, sort_prop=sort_prop, sort_order=sort_order)

        # 9. 获取总记录数
        total = 0
        conn = pymysql.connect(**MYSQL_CONFIG)
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute("SELECT COUNT(*) as total FROM weibo_classified WHERE category = '求助'")
                result = cur.fetchone()
                total = result.get('total', 0) if result else 0
        finally:
            conn.close()

        # 10. 发送结果回前端
        emit('all_help_messages', {'data': data, 'total': total})

    except (ValueError, TypeError) as e:
        # 处理 payload 中 page 或 size 不是有效整数的情况
        print(f"Invalid payload data: {e}")
        emit('all_help_messages', {'data': [], 'total': 0, 'error': 'Invalid request data'})
    except Exception as e:
        # 处理其他意外错误
        print(f"Unexpected error in ws_get_all_help_messages: {e}")
        emit('all_help_messages', {'data': [], 'total': 0, 'error': 'Internal server error'})

@socketio.on('get_help_locations')
def ws_get_help_locations(_payload):
    data = fetch_help_locations()
    emit('help_locations', {'data': data})


@socketio.on('get_classified_data')
def ws_get_classified_data(payload):
    category = payload.get('category')
    start_date = payload.get('start_date')
    end_date = payload.get('end_date')

    data = fetch_classified_data(category=category, start_date=start_date, end_date=end_date)

    # ✅ 重要：返回 query.category，让前端能识别是哪个类别的响应
    emit('classified_data', {
        'data': data,
        'query': {
            'category': category,
            'start_date': start_date,
            'end_date': end_date
        }
    })

@socketio.on('get_categories')
def ws_get_categories(_payload):
    cats = fetch_categories()
    emit('categories', {'data': cats})

@socketio.on('get_weibo_data')
def ws_get_weibo_data(payload):
    start_date = payload.get('start_date')
    end_date = payload.get('end_date')
    data = fetch_weibo_data(start_date=start_date, end_date=end_date)
    emit('weibo_data', {'data': data})

@socketio.on('get_cleaned_data')
def ws_get_cleaned_data(payload):
    start_date = payload.get('start_date')
    end_date = payload.get('end_date')
    data = fetch_cleaned_data(start_date=start_date, end_date=end_date)
    emit('cleaned_data', {'data': data})

@socketio.on('stop_crawl')
def ws_stop_crawl(_payload):
    global crawl_process, processor_process
    try:
        if crawl_process is not None and crawl_process.poll() is None:
            crawl_process.terminate()
            try:
                crawl_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                crawl_process.kill()
            logger.info("Crawler process terminated")
            crawl_process = None

            # process leftover queue
            logger.info("Processing remaining data after stop")
            process_remaining_data()

            emit('stop_crawl', {'success': True, 'message': '爬虫已停止，正在处理剩余数据'})
        else:
            emit('stop_crawl', {'success': True, 'message': '没有正在运行的爬虫'})
    except Exception as e:
        logger.exception("Failed to stop crawler: %s", e)
        emit('stop_crawl', {'success': False, 'error': f'停止爬虫失败: {e}'})


@app.route('/api/get_queue_status', methods=['GET'])
def get_queue_status():
    try:
        redis_queue = RedisQueue()
        stats = redis_queue.get_stats()
        return jsonify({'queue_length': stats['queue_length'], 'queue_name': stats['queue_name'], 'message': '队列状态获取成功'}), 200
    except Exception as e:
        logger.exception("get_queue_status failed: %s", e)
        return jsonify({'error': f'获取队列状态失败: {e}'}), 500

@app.route('/api/clear_queues', methods=['POST'])
def clear_queues():
    try:
        redis_queue = RedisQueue()
        redis_queue.clear_queue()
        return jsonify({'message': '队列已清空'}), 200
    except Exception as e:
        logger.exception("clear_queues failed: %s", e)
        return jsonify({'error': f'清空队列失败: {e}'}), 500

def notify_new_classified_row(row_id):
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("""
                SELECT id, screen_name, cleaned_text, location, category, created_at, insert_time
                FROM weibo_classified WHERE id = %s
            """, (row_id,))
            row = cur.fetchone()
            if row:
                fmt_row_dates(row)
                # 使用 broadcast=False + to=None 方式广播给所有客户端
                # socketio.emit('new-message', row, namespace='/', to=None)
    except Exception as e:
        logger.exception("notify_new_classified_row failed: %s", e)
    finally:
        try:
            conn.close()
        except Exception:
            pass



if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5004)
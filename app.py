
from flask import Flask, render_template, jsonify, request
import os
import json
import datetime
from glob import glob
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import re
from PIL import Image

# 读取名称映射文件
def load_name_mapping():
    mapping_file = 'name_mapping.json'
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取名称映射文件失败: {e}")
    # 返回默认映射
    return {
        "items": {},
        "currencies": {}
    }

# 加载名称映射
NAME_MAPPING = load_name_mapping()

# 获取物品的中文名称
def get_item_display_name(item_name):
    return NAME_MAPPING['items'].get(item_name, item_name)

# 获取货币的中文名称
def get_currency_display_name(currency_name):
    return NAME_MAPPING['currencies'].get(currency_name, currency_name)

# 设置matplotlib支持中文
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用黑体显示中文
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

app = Flask(__name__)

# 将datetime添加到Jinja2环境
app.jinja_env.globals.update(datetime=datetime)
 
# 添加时间过滤器，将时间戳格式化为可读格式
@app.template_filter('format_datetime')
def format_datetime(value):
    try:
        # 假设时间戳格式为：2023-10-01_12-30
        dt = datetime.datetime.strptime(value, '%Y-%m-%d_%H-%M')
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return value

# 添加枚举过滤器，用于在模板中获取索引
@app.template_filter('enumerate')
def filter_enumerate(iterable):
    return enumerate(iterable)
# 数据基础目录
BASE_DIR = 'Market price statistics'

# 支持的货币类型映射
CURRENCY_TYPES = {
    'buy_c': '购买-混沌石',
    'sell_c': '出售-混沌石',
    'buy_d': '购买-神圣石',
    'sell_d': '出售-神圣石'
}

# 解析比例值为浮点数
def parse_ratio(ratio_str):
    try:
        if ':' in ratio_str:
            parts = ratio_str.split(':')
            return float(parts[1]) / float(parts[0])
        return float(ratio_str)
    except:
        return None

# 获取所有物品列表（返回英文名称和中文名称的映射）
def get_all_items():
    if not os.path.exists(BASE_DIR):
        return []
    items = []
    for item in os.listdir(BASE_DIR):
        item_path = os.path.join(BASE_DIR, item)
        if os.path.isdir(item_path):
            display_name = get_item_display_name(item)
            items.append({
                'name': item,  # 英文名称，用于URL和文件操作
                'display_name': display_name  # 中文名称，用于显示
            })
    # 按中文名称排序
    return sorted(items, key=lambda x: x['display_name'])

# 获取物品的所有数据文件
def get_item_data_files(item_name):
    item_dir = os.path.join(BASE_DIR, item_name)
    if not os.path.exists(item_dir):
        return []
    
    data_files = []
    for file_name in os.listdir(item_dir):
        if file_name.endswith('_results.json'):
            data_files.append(file_name)
    return data_files

# 读取JSON数据文件
def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取文件 {file_path} 失败: {e}")
        return []

# 获取物品价格数据
def get_item_price_data(item_name, data_type):
    file_path = os.path.join(BASE_DIR, item_name, f'{data_type}_results.json')
    if not os.path.exists(file_path):
        return [], []
    
    data = read_json_file(file_path)
    results = []
    empty_timestamps = []
    
    for entry in data:
        timestamp = entry.get('timestamp', '')
        # 收集所有非空的比例值
        price_items = []
        has_non_empty = False
        
        for item in entry.get('data', []):
            ratio = item.get('ratio', '')
            count = item.get('count', '')
            if ratio and count:
                try:
                    ratio_value = parse_ratio(ratio)
                    count_value = int(count)
                    price_items.append({
                        'ratio': ratio_value,
                        'count': count_value,
                        'raw_ratio': ratio  # 保留原始比例字符串
                    })
                    has_non_empty = True
                except:
                    continue
        
        if has_non_empty:
            results.append({
                'timestamp': timestamp,
                'price_items': price_items,  # 存储所有非空数据项
                # 保留原始字段以便向后兼容
                'ratio': price_items[0]['ratio'],  # 第一个比例值
                'count': price_items[0]['count']  # 第一个订单数量
            })
        elif timestamp:  # 如果时间戳存在但数据全为空
            empty_timestamps.append(timestamp)
    
    return sorted(results, key=lambda x: x['timestamp']), sorted(empty_timestamps)

# 获取所有截图信息
def get_all_screenshots(item_name, data_type):
    item_dir = os.path.join(BASE_DIR, item_name)
    if not os.path.exists(item_dir):
        return []
    
    # 查找对应的截图文件，尝试多种可能的文件名格式
    possible_formats = [
        f'{data_type}.png',
        f'{data_type.replace("buy_", "buy-").replace("sell_", "sell-")}.png'
    ]
    
    screenshots = []
    # 获取所有时间戳目录
    for dir_name in os.listdir(item_dir):
        dir_path = os.path.join(item_dir, dir_name)
        if os.path.isdir(dir_path):
            for format_str in possible_formats:
                screenshot_file = os.path.join(dir_path, format_str)
                if os.path.exists(screenshot_file):
                    screenshots.append({
                        'timestamp': dir_name,
                        'file_path': screenshot_file
                    })
    
    # 按时间戳排序，最新的在前
    screenshots.sort(key=lambda x: x['timestamp'], reverse=True)
    return screenshots

# 获取最新的截图
def get_latest_screenshot(item_name, data_type):
    screenshots = get_all_screenshots(item_name, data_type)
    if screenshots:
        print(f"找到最新截图文件: {screenshots[0]['file_path']}")
        return screenshots[0]['file_path']
    
    print(f"未找到{item_name}的{data_type}截图")
    return None

# 生成价格趋势图
def generate_price_chart(data, title):
    if not data:
        return None
    
    try:
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d_%H-%M')
        
        plt.figure(figsize=(10, 5))
        plt.plot(df['datetime'], df['ratio'], marker='o', linestyle='-', color='#1f77b4')
        plt.title(title)
        plt.xlabel('时间')
        plt.ylabel('价格比例')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 将图表转换为base64编码的字符串
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode('utf-8')
    except Exception as e:
        print(f"生成图表失败: {e}")
        return None

# 转换图片为base64
def image_to_base64(image_path):
    try:
        with open(image_path, 'rb') as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        print(f"转换图片失败: {e}")
        return None

@app.route('/')
def index():
    items = get_all_items()
    return render_template('index.html', items=items)

@app.route('/item/<item_name>')
def item_detail(item_name):
    # 获取物品的中文显示名称
    item_display_name = get_item_display_name(item_name)
    
    data_files = get_item_data_files(item_name)
    
    # 提取所有数据类型
    data_types = []
    for file in data_files:
        data_type = file.split('_results.json')[0]
        if data_type in CURRENCY_TYPES:
            data_types.append(data_type)
    
    # 获取所有数据
    all_data = {}
    latest_data = {}
    charts = {}
    screenshots = {}
    empty_timestamps = {}
    
    for data_type in data_types:
        # 获取价格数据和空数据时间戳
        price_data, empty_ts = get_item_price_data(item_name, data_type)
        all_data[data_type] = price_data
        empty_timestamps[data_type] = empty_ts
        
        # 获取最新数据
        if price_data:
            latest_data[data_type] = price_data[-1]
        else:
            latest_data[data_type] = None
        
        # 生成趋势图（使用中文名称）
        chart_title = f"{item_display_name} - {CURRENCY_TYPES[data_type]} 价格趋势"
        charts[data_type] = generate_price_chart(price_data, chart_title)
        
        # 获取所有截图信息
        all_screenshots = get_all_screenshots(item_name, data_type)
        if all_screenshots:
            # 保存所有截图的时间戳信息
            screenshots[data_type] = {
                'timestamps': [s['timestamp'] for s in all_screenshots],
                'latest_image': image_to_base64(all_screenshots[0]['file_path'])
            }
        else:
            screenshots[data_type] = {'timestamps': [], 'latest_image': None}
    
    return render_template(
        'item_detail.html',
        item_name=item_name,
        item_display_name=item_display_name,
        data_types=data_types,
        currency_types=CURRENCY_TYPES,
        all_data=all_data,
        latest_data=latest_data,
        charts=charts,
        screenshots=screenshots,
        empty_timestamps=empty_timestamps
    )

@app.route('/api/items')
def api_items():
    items = get_all_items()
    # 返回包含显示名称的物品列表
    return jsonify([{'name': item['name'], 'display_name': item['display_name']} for item in items])

@app.route('/api/item/<item_name>/<data_type>')
def api_item_data(item_name, data_type):
    price_data = get_item_price_data(item_name, data_type)
    return jsonify(price_data)

@app.route('/api/screenshot/<item_name>/<data_type>/<timestamp>')
def api_screenshot(item_name, data_type, timestamp):
    all_screenshots = get_all_screenshots(item_name, data_type)
    # 查找指定时间戳的截图
    for screenshot in all_screenshots:
        if screenshot['timestamp'] == timestamp:
            image_data = image_to_base64(screenshot['file_path'])
            return jsonify({'image': image_data})
    return jsonify({'error': '截图未找到'}), 404

if __name__ == '__main__':
    # 确保templates目录存在
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    app.run(host='0.0.0.0', port=5000, debug=True)
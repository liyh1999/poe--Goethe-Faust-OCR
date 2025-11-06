import json
import os
import datetime
import time
import pyautogui
import pyperclip
pyautogui.PAUSE = 0.5
from PIL import Image
import cv2
import numpy as np
import pytesseract
# 配置 Tesseract 路径（根据你的安装路径调整）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
def preprocess_image(image):
    """
    对图像进行二值化、腐蚀、膨胀等预处理，提高 OCR 提取效率。
    参数:
        image (numpy.ndarray): 输入的灰度图像。
    返回:
        numpy.ndarray: 预处理后的图像。
    """
    # 转为二值化图像
    _, binary = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY_INV)
    # 应用腐蚀和膨胀
    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.dilate(cv2.erode(binary, kernel, iterations=1), kernel, iterations=1)
    return processed
def extract_text_from_row(image, row_height):
    """
    对图像的每一行进行 OCR 提取，将每行分为左右两部分，分别提取比例和订单数目。
    参数:
        image (numpy.ndarray): 输入的灰度图像。
        row_height (int): 每一行的高度。
    返回:
        list: 每行提取的文本结果，格式为[{"ratio": 比例, "count": 订单数目}]
    """
    height, width = image.shape
    results = []
    # 将每行分为左右两部分，左边是比例，右边是订单数目
    mid_point = width // 2
    
    for i in range(6):  # 假设分成六行
        # 计算每行的起始和结束位置
        y_start = i * row_height
        y_end = (i + 1) * row_height
        
        # 截取左边部分（比例）
        left_row = image[y_start:y_end, :mid_point]
        processed_left = preprocess_image(left_row)
        # 使用 Tesseract OCR 提取比例，允许数字和冒号
        ratio_config = r'--psm 7 -c tessedit_char_whitelist=:0123456789.'
        ratio_text = pytesseract.image_to_string(processed_left, config=ratio_config).strip()
        
        # 截取右边部分（订单数目）
        right_row = image[y_start:y_end, mid_point:]
        processed_right = preprocess_image(right_row)
        # 使用 Tesseract OCR 提取订单数目，只允许数字
        count_config = r'--psm 7 -c tessedit_char_whitelist=0123456789'
        count_text = pytesseract.image_to_string(processed_right, config=count_config).strip()
        
        # 将结果保存为字典格式
        results.append({
            "ratio": ratio_text,
            "count": count_text
        })
    return results
def split_and_recognize(image_path):
    """
    读取本地图片，将其平均分为六行，并提取每行的数字。
    参数:
        image_path (str): 图片文件路径。
    返回:
        list: 每行提取的数字文本。
    """
    # 加载图像并转换为灰度
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # 获取图像高度，并计算每行高度
    height, width = image.shape
    row_height = height // 6
    # 提取每行文本
    results = extract_text_from_row(image, row_height)
    return results
def move_and_click(x, y):
    """
    将鼠标移动到指定坐标并左键单击。
    参数:
        x (int): 鼠标目标位置的X坐标。
        y (int): 鼠标目标位置的Y坐标。
        duration (float): 鼠标移动到目标位置的时间（默认0.05秒）。
    """
    pyautogui.moveTo(x, y,duration=0.05)  # 移动到指定坐标
    pyautogui.click()  # 左键单击
def search_keyword(keyword):
    """
    按下 Ctrl+F，然后粘贴指定的关键词。

    参数:
        keyword (str): 要搜索的关键词。
    """
    # 按下 Ctrl+F
    pyautogui.hotkey('ctrl', 'f')
    # 将关键词复制到剪贴板并粘贴
    pyperclip.copy(keyword)  # 使用 pyperclip 复制到剪贴板
    pyautogui.hotkey('ctrl', 'v')  # 粘贴关键词
def clean_old_screenshots(product_dir, keep_count=10):
    """
    清理旧的截图目录，只保留最近的指定数量的目录。
    
    参数:
        product_dir (str): 商品目录路径
        keep_count (int): 要保留的目录数量
    """
    # 获取所有子目录
    subdirs = []
    for item in os.listdir(product_dir):
        item_path = os.path.join(product_dir, item)
        if os.path.isdir(item_path):
            # 获取目录的修改时间
            mtime = os.path.getmtime(item_path)
            subdirs.append((item_path, mtime))
    
    # 按修改时间排序，最新的在前
    subdirs.sort(key=lambda x: x[1], reverse=True)
    
    # 删除超出保留数量的旧目录
    for dir_path, _ in subdirs[keep_count:]:
        try:
            # 删除目录及其所有内容
            import shutil
            shutil.rmtree(dir_path)
            print(f"已删除旧截图目录: {dir_path}")
        except Exception as e:
            print(f"删除目录 {dir_path} 时出错: {e}")

def move_and_screenshot(x, y, region1, region2, name, currency):
    """
    移动到指定位置，按住 Alt 键，截取屏幕某个区域的图像并释放按键。

    参数:
        x (int): 鼠标目标位置的 X 坐标。
        y (int): 鼠标目标位置的 Y 坐标。
        region1 (tuple): 截图区域，格式为 (左上角X, 左上角Y, 宽度, 高度)。
        region2 (tuple): 第二个截图区域，格式为 (左上角X, 左上角Y, 宽度, 高度)。
        name (str): 用户或市场名称。
        currency (str): 货币类型，'d' 或 'e'。
    """
    # 移动鼠标到指定位置
    pyautogui.moveTo(x, y, duration=0.05)
    # 按下 Alt 键
    pyautogui.keyDown('alt')
    try:
        # 获取当前时间并生成目录，精确到分钟
        now = datetime.datetime.now()
        adjusted_minute = (now.minute // 10) * 10  # 取当前分钟的整10分钟值
        current_time = now.replace(minute=adjusted_minute, second=0, microsecond=0).strftime("%Y-%m-%d_%H-%M")
        product_dir = rf".\Market price statistics\{name}"
        directory = rf"{product_dir}\{current_time}"
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # 根据货币类型进行不同处理
        if currency == 'd':
            # 截取 buy-d 区域
            screenshot = pyautogui.screenshot(region=region1)
            screenshot.save(rf"{directory}\buy-d.png")
            # 执行分割和识别
            results_buy = split_and_recognize(rf"{directory}\buy-d.png")
            # 输出识别结果
            for idx, item in enumerate(results_buy, 1):
                print(rf"{name}的d出售比例为: {item['ratio']}, 订单数目: {item['count']}")
            # JSON文件保存到商品目录
            results_file = rf"{product_dir}\buy_d_results.json"
            # 追加写入 JSON 文件
            append_to_json(results_file, results_buy)
            
            # 截取 sell-d 区域
            screenshot = pyautogui.screenshot(region=region2)
            screenshot.save(rf"{directory}\sell-d.png")
            # 执行分割和识别
            results_sell = split_and_recognize(rf"{directory}\sell-d.png")
            # 输出识别结果
            for idx, item in enumerate(results_sell, 1):
                print(rf"{name}的d购买比例为: {item['ratio']}, 订单数目: {item['count']}")
            # JSON文件保存到商品目录
            results_file = rf"{product_dir}\sell_d_results.json"
            # 追加写入 JSON 文件
            append_to_json(results_file, results_sell)
        
        if currency == 'c':
            # 截取 buy-c 区域
            screenshot = pyautogui.screenshot(region=region1)
            screenshot.save(rf"{directory}\buy-c.png")
            # 执行分割和识别
            results_buy = split_and_recognize(rf"{directory}\buy-c.png")
            # 输出识别结果
            for idx, item in enumerate(results_buy, 1):
                print(rf"{name}的c出售比例为: {item['ratio']}, 订单数目: {item['count']}")
            # JSON文件保存到商品目录
            results_file = rf"{product_dir}\buy_c_results.json"
            # 追加写入 JSON 文件
            append_to_json(results_file, results_buy)
            
            # 截取 sell-c 区域
            screenshot = pyautogui.screenshot(region=region2)
            screenshot.save(rf"{directory}\sell-c.png")
            # 执行分割和识别
            results_sell = split_and_recognize(rf"{directory}\sell-c.png")
            # 输出识别结果
            for idx, item in enumerate(results_sell, 1):
                print(rf"{name}的c购买比例为: {item['ratio']}, 订单数目: {item['count']}")
            # JSON文件保存到商品目录
            results_file = rf"{product_dir}\sell_c_results.json"
            # 追加写入 JSON 文件
            append_to_json(results_file, results_sell)
        
        # 清理旧截图，只保留最近10次
        clean_old_screenshots(product_dir, keep_count=10)
        
    finally:
        # 确保释放 Alt 键
        pyautogui.keyUp('alt')


def append_to_json(file_path, data):
    """
    追加数据到 JSON 文件中，如果文件不存在，则创建文件。
    同时在数据中添加时间戳，便于区分每次写入的数据。

    参数:
        file_path (str): JSON 文件的路径。
        data (dict): 需要追加的数据。
    """
    # 在数据中加入时间戳
    now = datetime.datetime.now()
    adjusted_minute = (now.minute // 10) * 10  # 取当前分钟的整10分钟值
    current_time = now.replace(minute=adjusted_minute, second=0, microsecond=0).strftime("%Y-%m-%d_%H-%M")
    data_with_timestamp = {
        "timestamp": current_time,
        "data": data
    }
    # 如果文件不存在，创建文件
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([data_with_timestamp], f, ensure_ascii=False, indent=4)
    else:
        with open(file_path, 'r+', encoding='utf-8') as f:
            # 读取已有的数据
            existing_data = json.load(f)
            # 追加新的数据
            existing_data.append(data_with_timestamp)
            # 返回文件指针到文件开头
            f.seek(0)
            # 写入更新后的数据
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
需要_坐标=(572,335)
拥有_坐标=(1178,335)
确认_坐标=(950,281)  #倒是可以找到一个通用的坐标
比例_坐标=(867,261)
购买比例_区域=(743,362,247,178)    #左上角：(557,282)  右下角：（741，412）
竞价比例_区域=(745,606 ,249,170)    #745,606    994,776
def 全程处理(name, curr):
    time.sleep(3)
    move_and_click(*需要_坐标)
    search_keyword(name)
    move_and_click(*确认_坐标)
    move_and_click(*拥有_坐标)
    search_keyword(curr)
    move_and_click(*确认_坐标)
    pyautogui.moveTo(1067, 260, duration=0.05)  # 有点奇怪，不知道为什么有的时候他不显示价格，所以要移动出去一点然后再移动回来
    if curr == "神圣石":
        time.sleep(1)
        move_and_screenshot(*比例_坐标, 购买比例_区域, 竞价比例_区域, name, 'd')
    elif curr == "混沌石":
        time.sleep(1)
        move_and_screenshot(*比例_坐标, 购买比例_区域, 竞价比例_区域, name, 'c')
# 定时调用全程处理
def schedule_task():
    while True:
        # 每次调用时传入需要的参数
        # 全程处理("贪婪之破空精华", "神圣石")
        全程处理("divi", "混沌石")  # 文件名不能是中文的
        全程处理("Deafening Essence of Hatred", "混沌石")   #文件名不能是中文的
        全程处理("Deafening Essence of Hatred", "神圣石")  # 文件名不能是中文的
        # 每隔 10 分钟执行一次
        time.sleep(600)  # 600秒 = 10分钟
# 启动定时任务
schedule_task()
# POE 物品价格统计系统

## 项目简介
通过OCR手段实现POE国服的物品价格获取，包含了OCR识别及数据网页部署两部分代码。

## 项目地址
GitHub仓库: [poe--Goethe-Faust-OCR](https://github.com/liyh1999/poe--Goethe-Faust-OCR)

## 功能特点

### 1. OCR识别功能
- 自动截取游戏内交易界面
- 通过坐标匹配识别物品价格信息
- 支持多种物品类型和货币类型
- 定期自动执行截图和识别任务

### 2. 数据网页展示
- 直观显示物品价格趋势图
- 支持查看历史价格数据和原始比例
- 可切换不同货币类型查看（混沌石、神圣石）
- 显示历史截图，方便验证数据准确性
- 支持中文名称显示
- 自动刷新功能

## 项目结构

```
├── Market price statistics/   # 存储统计数据的目录
│   └── [物品名称]/           # 各物品的数据目录
│       ├── [时间戳]/         # 历史截图目录
│       ├── buy_c_results.json  # 购买-混沌石数据
│       ├── sell_c_results.json # 出售-混沌石数据
│       ├── buy_d_results.json  # 购买-神圣石数据
│       └── sell_d_results.json # 出售-神圣石数据
├── templates/                 # HTML模板目录
│   ├── index.html             # 物品列表页面
│   └── item_detail.html       # 物品详情页面
├── app.py                     # Flask应用主文件
├── name_mapping.json          # 中英文名称映射文件
├── 坐标匹配与检查.py           # 坐标匹配和检查脚本
└── 截屏.py                    # 自动截屏脚本
```

## 技术栈

- **后端**: Python, Flask
- **前端**: HTML, CSS (Bootstrap), JavaScript, Chart.js
- **数据处理**: Pandas, Matplotlib
- **图像处理**: PIL (Pillow)
- **OCR技术**: 基于坐标匹配的OCR识别

## 安装和使用

### 1. 安装依赖

```bash
pip install flask pandas matplotlib pillow
```

### 2. 配置名称映射

编辑 `name_mapping.json` 文件，设置物品和货币的中英文名称映射：

```json
{
  "items": {
    "Deafening Essence of Hatred": "贪婪之破空精华",
    "divi": "神圣石"
  },
  "currencies": {
    "chaos": "混沌石",
    "divi": "神圣石"
  }
}
```

### 3. 运行截图和识别任务

执行 `截屏.py` 脚本开始自动截图和数据识别：

```bash
python 截屏.py
```

### 4. 启动网页服务

执行 `app.py` 启动Flask网页服务：

```bash
python app.py
```

然后在浏览器中访问 `http://localhost:5000` 查看物品价格统计信息。

## 数据格式说明

### 价格数据格式

每个物品的价格数据存储在JSON文件中，格式如下：

```json
[
  {
    "timestamp": "2025-11-06_07-00",
    "data": [
      {
        "ratio": "1:30",
        "count": "20"
      },
      {
        "ratio": "1:31",
        "count": "15"
      }
    ]
  }
]
```

## 常见问题

### Q: 数据显示为空怎么办？
A: 检查截图脚本是否正常运行，以及游戏界面是否在正确的交易页面。

### Q: 如何添加新的物品监控？
A: 修改 `截屏.py` 脚本，添加新的物品配置和坐标信息。

### Q: 网页数据多久更新一次？
A: 网页默认每分钟自动刷新一次，截图和数据识别的频率可在 `截屏.py` 中配置。

## 许可证

MIT License
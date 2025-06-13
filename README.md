# 期刊爬虫系统使用说明

## 文件说明

### craw.py
- **功能**：爬取知网期刊内容
- **依赖**：需要`lists.xlsx`期刊列表文件
- **特点**：
  - 自动根据`lists.xlsx`搜索期刊
  - 爬取近一年左右的文献标题和摘要
  - 自动保存到CSV文件
  - 支持断点续爬（通过进度文件记录）

### sh_try.py
- **功能**：监控和重启爬虫进程
- **依赖**：需要`craw.py`作为子进程
- **特点**：
  - 作为守护进程监控`craw.py`
  - 子进程异常退出后自动重启
  - 主进程退出时自动终止子进程

## 配置说明

### craw.py 配置项

```python
# 日志文件路径
LOG_FILE = 'journal_crawler.log'

# 进度文件路径
PROGRESS_FILE = 'progress.txt'

# 期刊列表Excel文件路径
JOURNAL_LIST_FILE = './lists.xlsx'

# 输出文件目录
OUTPUT_DIR = 'F:\\top\\'
```

### sh_try.py 配置项

```python
# 打开文件并打印内容
file_path = 'progress.txt'  # 进度文件路径

# conda环境配置（如需）
# conda_env_name = 'your_conda_env'  # 替换为实际的环境名

program_name = './craw.py'  # 要监控的程序名
time_interval = 180  # 检查间隔（秒），默认3分钟
```

## 使用注意事项

### 期刊列表文件
- **建议使用`lists.xlsx`格式**  
- **去除期刊名前的特殊符号和数字**  
- **可替换为其他Excel文件**，但需保持相同格式  

### 验证码问题
- **程序未充分测试验证码处理**  
- **遇到验证码时建议**：  
  - 更换网络/IP  
  - 调整爬取频率  
  - 手动处理验证码  

### 运行建议
- **先单独测试`craw.py`**确保基本功能正常  
- **再使用`sh_try.py`**进行守护运行  
- **调试时可注释无头模式选项**  

### 进程管理
- **关闭`sh_try.py`时会自动终止子进程**  
- **子进程异常退出后约3分钟会自动重启**  

## 文件结构

项目目录/
│── craw.py                # 主爬虫程序
│── sh_try.py              # 进程监控程序
│── lists.xlsx             # 期刊列表文件
│── journal_crawler.log    # 日志文件（运行时生成）
│── progress.txt           # 进度文件（运行时生成）
└── F:/top/                # 输出目录（根据配置）
    ├── 期刊1.csv
    ├── 期刊2.csv
    └── ...

<!-- 建议提供记录运行情况 -->
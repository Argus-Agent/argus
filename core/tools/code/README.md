# Code执行模块

这是一个多语言代码执行模块，支持Python、Bash和PowerShell代码的异步执行。

## 功能概述

该模块提供了一个统一的接口来执行不同编程语言的代码，并通过队列返回执行结果。支持代码中断、执行时间监控等功能。

## 架构设计

### 核心组件

- **Code类**: 主要的代码执行管理器，负责语言选择和执行调度
- **BaseLanguage类**: 所有语言实现的抽象基类
- **PythonLanguage类**: Python代码执行器，基于Jupyter内核
- **BashLanguage类**: Bash/Shell代码执行器，基于subprocess
- **PowerShellLanguage类**: PowerShell代码执行器，基于subprocess

### 消息系统

所有执行结果通过`queue.Queue`对象返回，消息格式为字典：

```python
{
    "type": "消息类型",
    "content": "消息内容"
}
```

## run()返回的消息格式

- **`text`**: 纯文本输出，包括标准输出、错误输出、执行结果等
- **`image/png`**: PNG格式的图片数据（base64编码）
- **`image/jpeg`**: JPEG格式的图片数据（base64编码）
- **`html`**: HTML格式的内容
- **`text/plain`**: 纯文本内容
- **`application/javascript`**: JavaScript代码
- **`error`**: 模块的错误信息，不包含代码运行的错误

## 使用方法

### 基本用法

```python
from core.tools.code import Code

# 创建代码执行器
code_executor = Code()

# 执行Python代码
result_queue = code_executor.run("python", "print('Hello, World!')")

# 执行Bash代码
result_queue = code_executor.run("bash", "ls -la")

# 执行PowerShell代码
result_queue = code_executor.run("powershell", "Get-ChildItem")

# 获取执行结果
while not result_queue.empty():
    message = result_queue.get()
    print(f"{message['type']}: {message['content']}")
```

### 支持的语言

- Python: `python`
- Bash: `bash`, `sh`
- PowerShell: `powershell`, `pwsh`

### 中断执行

```python
# 中断当前正在执行的代码
result_queue = code_executor.interrupt()
```

### 监控执行状态

```python
# 检查是否有代码正在运行
is_running = code_executor.is_running()

# 获取已运行时间
elapsed_time = code_executor.get_elapsed_time()
```

## 各语言实现详情

### Python实现 (PythonLanguage)

- **技术**: 基于Jupyter内核和jupyter_client
- **特性**: 
  - 支持matplotlib内联绘图
  - 支持图片、HTML、JavaScript等多种输出格式
  - 完整的Python语法支持
  - 自动添加`%matplotlib inline`以支持可视化
- **依赖**: jupyter_client, ipython kernel

### Bash实现 (BashLanguage)

- **技术**: 基于subprocess.Popen
- **特性**:
  - 检测bash是否可用
  - 实时输出流
  - 支持信号中断
- **可用性检查**: `shutil.which("bash")`

### PowerShell实现 (PowerShellLanguage)

- **技术**: 基于subprocess.Popen
- **特性**:
  - 优先使用pwsh (PowerShell Core)，回退到powershell
  - 跨平台支持
  - 无配置文件执行 (`-NoProfile`)
- **可用性检查**: `shutil.which("powershell") or shutil.which("pwsh")`

## 错误处理

### 模块级错误

- 不支持的语言
- 系统环境问题
- 内核启动失败

### 代码执行错误

- 语法错误
- 运行时错误
- 依赖缺失

## 线程安全

- 每次代码执行都在独立的线程中运行
- 使用队列进行线程间通信
- 支持优雅的中断机制

## 性能考虑

- Python内核会重复启动和停止，适合短时间执行
- Bash和PowerShell为每次执行创建新进程
- 所有语言都支持实时输出，不会阻塞主线程

## 依赖要求

### Python环境
- Python 3.7+
- jupyter_client
- IPython kernel

### 系统环境
- Bash: Git Bash, WSL, 或Linux/macOS环境
- PowerShell: Windows PowerShell 5.1+ 或 PowerShell Core 6.0+

## 示例代码

```python
# 完整示例
from core.computer.code import Code
import time

def execute_code_example():
    executor = Code()
    
    # Python可视化示例
    print("执行Python代码...")
    result = executor.run("python", """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 4))
plt.plot(x, y)
plt.title('正弦波形')
plt.xlabel('x')
plt.ylabel('sin(x)')
plt.grid(True)
plt.show()
""")
    
    # 读取结果
    while not result.empty() or executor.is_running():
        if not result.empty():
            msg = result.get()
            print(f"收到消息: {msg['type']}")
            if msg['type'].startswith('image/'):
                print(f"图片数据: {len(msg['content'])} 字节")
            else:
                print(f"内容: {msg['content'][:100]}...")
        time.sleep(0.1)
    
    print("Python执行完成")

if __name__ == "__main__":
    execute_code_example()
```

## 注意事项

1. **Python内核**: 每次执行都会重新启动内核，状态不会保留
2. **安全性**: 该模块设计用于受控环境，避免执行不受信任的代码
3. **资源管理**: 长时间运行可能产生大量进程，建议监控资源使用
4. **平台兼容性**: 某些功能在不同操作系统上表现可能不同

## 未来改进

- [ ] 支持更多编程语言 (Node.js, Ruby等)
- [ ] Python内核持久化，避免重复启动
- [ ] 代码执行超时设置
- [ ] 更细粒度的权限控制
- [ ] 代码执行历史记录
- [ ] 性能监控和分析

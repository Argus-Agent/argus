# Screen 模块测试
这个目录包含了 `computer.screen.Screen` 模块的测试代码，用于测试截图功能并展示图片。

## 文件说明

- `test_screen.py` - 主测试文件，包含完整的测试套件
- `run_test.py` - 快速测试脚本
- `view_images.py` - 图片查看脚本，用于查看生成的截图
- `start.py` - 一键开始脚本，运行测试并查看结果
- `README.md` - 本说明文件

## 测试功能

### 基础测试
- 测试不同格式的截图（PNG、JPEG）
- 测试不同缩放比例的截图
- 测试错误处理（不支持的格式）
- 自动保存截图文件到当前目录

### 交互式测试
- 用户可以自定义截图参数
- 支持自定义缩放因子、图片格式和质量

## 运行方法

### 🚀 推荐方式：一键开始
```bash
python start.py
```
这将自动运行测试并为您提供查看选项。

### 方法1: 快速测试
```bash
python run_test.py
```

### 方法2: 完整测试
```bash
python test_screen.py
```

### 方法3: 查看生成的截图
```bash
python view_images.py
```

## 依赖要求

确保已安装以下Python包：
- Pillow (PIL)
- base64 (内置)
- io (内置)

如果未安装Pillow：
```bash
pip install Pillow
```

## 输出文件

测试运行后会在当前目录生成以下文件：
- `test_screenshot_1.png` - PNG格式50%缩放测试
- `test_screenshot_2.jpeg` - JPEG格式原始大小测试  
- `test_screenshot_3.png` - PNG格式30%缩放测试
- `interactive_test.*` - 交互式测试生成的文件（如果运行）

## 测试结果

测试会显示：
- ✓ 截图成功的消息
- 图片格式和Base64长度
- 图片尺寸、模式和文件大小
- 保存的文件路径
- 错误处理结果

## 注意事项

1. 截图功能需要图形界面环境
2. 测试会捕获当前屏幕内容
3. 生成的图片文件会保存在当前测试目录
4. 如需测试特定功能，可以修改 `test_screen.py` 中的测试用例

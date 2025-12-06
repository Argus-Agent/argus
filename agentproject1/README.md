# GUI Agent Framework

一个基于分层架构的GUI Agent框架，支持Flet UI界面。

## 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 运行应用：`python main.py`
3. 在输入框中输入"获取当前时间"测试功能

## 项目结构
- `app/` - 应用组装和依赖注入
- `presentation/` - UI展示层
- `core/` - Agent核心逻辑
- `capabilities/` - 感知、推理、行动能力
- `interfaces/` - 消息和协议接口
- `utils/` - 工具函数
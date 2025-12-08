# Agent4 - Liquid (智能桌面助理)

专为 Windows 设计的现代化智能代理，拥有苹果液态风格 (Liquid Style) 的悬浮界面，基于 UI-TARS 视觉大模型，支持完全的操作可视化。

## ⭐ 核心特性

### 🎨 Liquid UI (液态灵动界面)
- **异形悬浮**: 真正的无边框圆角设计，像灵动岛一样悬浮在桌面
- **极简风格**: 苹果风磨砂白配色，平时极小占用
- **视觉反馈**: 实时在屏幕上绘制点击波纹和操作路径 (Vision Overlay)

### 🤖 智能双核驱动
- **GUI Engine**: 基于 **UI-TARS 1.5** 视觉大模型，像人一样看屏幕操作
- **Smart Router**: 智能判断任务类型，自动切换 GUI/Code 模式
- **Human-in-the-loop**: 遇到困难自动呼叫人类介入 (含"我已协助完成"功能)

### 📦 核心组件

**Interface**
- **Liquid Bar** (`core/ui/app.py`): 主控悬浮条
- **Visualizer** (`core/ui/visualizer.py`): 全屏操作可视化层

**Agents**
- **GUIAgent**: 视觉驱动的自动化 (UI-TARS)
- **CodeAgent**: 代码执行与数据处理
- **SmartRouter**: 任务调度中枢

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
# 确保安装了 CustomTkinter 和 PyWin32
pip install customtkinter pywin32 pillow
```

### 2. 配置环境变量
复制 `.env.example` 为 `.env` 并配置：
```env
GUIAgent_MODEL=ui-tars-7b
GUIAgent_API_KEY=your_key
GUIAgent_API_BASE=http://localhost:8000/v1
```

### 3. 启动
**直接启动 (推荐)**:
```bash
python main.py
```
这将启动 **Liquid Bar** 悬浮窗。

**命令行模式**:
```bash
python main.py --task "打开记事本并输入Hello"
```

## 📊 项目结构

```
agent4/
├── core/
│   ├── agents/         # 智能体核心 (GUI/Code/Router)
│   ├── tools/          # 5大工具集 (Mouse/Keyboard/Screen...)
│   └── ui/             # 界面层
│       ├── app.py      # Liquid Bar 主程序
│       └── visualizer.py # 屏幕可视化
├── scripts/            # 辅助脚本
├── tests/              # 测试用例
├── main.py             # 通用入口
└── requirements.txt
```

## 🔧 高级功能

### 视觉操作反馈 (Vision Overlay)
Agent 在操作鼠标时，屏幕上会出现高亮波纹指示点击位置。这由底层的 `visualizer.py` 实现，支持**点击穿透**，完全不影响您的正常操作。

### 智能介入
当 Agent 无法完成任务时，Liquid Bar 会变色并请求帮助。您可以：
1. 点击 **"我已协助完成"** -> Agent 继续后续步骤
2. 修改指令 -> Agent 重试
3. 跳过当前步骤

---
*Agent4 Liquid - 让 AI 操作看得见、摸得着*

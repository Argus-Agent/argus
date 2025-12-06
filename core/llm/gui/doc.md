本教程指导你使用具备GUI任务处理能力模型，在计算机、移动设备等真实 GUI 环境中完成自动化任务（如界面点击、模式设置等）。模型支持图文结合的多轮交互，精准解析 GUI 操作指令并生成可执行的动作逻辑。 

<span id="ea8acb31"></span>
# 快速开始
以“将图像设置为Palette - Based模式”任务为例，演示单轮 GUI 任务流程。
![Image](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/ae7d606574e24c7a98a4eb9b934e2757~tplv-goo7wpa0wc-image.image =689x)
正式开始前需安装对应的SDK。
```Bash
pip install pillow numpy matplotlib
pip install volcengine-python-sdk[ark]
```

<span id="2bd4e181"></span>
## 步骤1：配置 API 与工具函数
```Python
import os
# 通过 pip install volcengine-python-sdk[ark] 安装方舟SDK
from volcenginesdkarkruntime import Ark
import base64

# 初始化Ark客户端，从环境变量中读取您的API Key
client = Ark(
    api_key=os.getenv('ARK_API_KEY'),
    )

# 图片转 Base64 工具函数
def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')
```

<span id="c85d406b"></span>
## 步骤2：构造对话消息（系统提示 + 图片）
其中 prompt 提示词模板见 [系统提示设计](/docs/82379/1584296#be30d2ab)。
```Python
from prompt import COMPUTER_USE_DOUBAO
# 系统提示模板（指定任务与语言）
instruction = "Could you help me set the image to Palette-Based?"
language = "Chinese"
system_prompt = COMPUTER_USE_DOUBAO.format(instruction=instruction, language=language)

# 编码目标截图
image_path = "image.png"
image_format = image_path.split('.')[-1]  # 提取图片格式（如png）
base64_image = encode_image(image_path)

# 构造messages（用户角色，包含文本提示和图片）
messages = [
    {
        "role": "user",
        "content": system_prompt
    },
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{image_format};base64,{base64_image}"
                }
            }
        ]
    }
]
```

<span id="69d721cd"></span>
## 步骤3：调用模型推理
```Python
def inference(messages):
    response = client.chat.completions.create(
        # 按需替换 model id
        model="doubao-1-5-ui-tars-250428",
        messages=messages,
        temperature=0.0,  # 固定温度保证输出稳定
        stream=True       # 流式获取响应（可选）
    )
    # 流式响应拼接
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            full_response += chunk.choices[0].delta.content
    return full_response

response = inference(messages)
print(response)
```

模型会返回GUI 任务处理的思考过程和动作指令如下：
```Plain Text
1. 首先分析当前界面：屏幕上显示GIMP的Preferences窗口，遮挡了主界面操作。要设置图像为Palette - Based，需先关闭Preferences窗口，再通过Image菜单操作。
2. 下一步逻辑：关闭Preferences窗口，点击其右上角的关闭按钮（×），以便后续访问Image菜单。
3. 目标元素：Preferences窗口右上角的关闭按钮，位置在窗口右上角，呈×形状。

Action: click(point='<point>450 416</point>')
```

<span id="697b77a8"></span>
## 步骤4：解析动作指令
模型返回的坐标为相对坐标，即将图片宽高归一化至1000后，对应点的坐标。要将这些值按照图像实际宽高进行比例换算，公式如下：
```Plain Text
X绝对坐标 = X相对坐标/1000 × 图像宽度 
Y绝对坐标 = Y相对坐标/1000 × 图像高度 
```

示例代码
```Python
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import re

image = Image.open(image_path)
original_width, original_height = image.size
# 解析坐标（示例：提取action中的坐标）
match = re.search(r'<point>(\d+)\s+(\d+)</point>', response)
if match:
    x = int(int(match.group(1))/1000*original_width)  # 提取第一个数字并转为绝对坐标
    y = int(int(match.group(2))/1000*original_height)  # 提取第二个数字并转为绝对坐标
    action_point = (x, y)    # 生成整数元组
else:
    raise ValueError(f"Failed to parse coordinates from response. Raw response: {response}")

print(action_point)  # 应输出类似(450, 416)的整数元组
# 在原图上标记动作位置
image = Image.open(image_path)
draw = ImageDraw.Draw(image)
draw.ellipse((action_point[0]-5, action_point[1]-5, action_point[0]+5, action_point[1]+5), fill="red")


# 展示标记后的图片
plt.imshow(image)
plt.axis("off")
plt.show()
```

<span id="9896cd57"></span>
# 使用说明
<span id="be30d2ab"></span>
## 系统提示设计
使用 [系统提示模板](/docs/82379/1536429#00d8bbfd)明确任务（`Instruction`）和语言（`Language`），请勿更改其中内容，避免影响模型输出效果。
将提示词模板复制至 prompt.py 并存放在主脚本目录下：

* 通过`import  COMPUTER_USE_DOUBAO from prompt`导入。
* 通过`system_prompt = COMPUTER_USE_DOUBAO.format(instruction=instruction, language=language)`方式使用提示词模板及传入提示词配置。

具体使用示例见[步骤2：构造对话消息（系统提示 + 图片）](/docs/82379/1584296#c85d406b)。
<span id="7a07477f"></span>
## 多轮对话管理
多轮任务最多保留最近5张截图（含当前）和历史响应，`messages`结构示例（以8轮为例）： 
```Python
messages = [
    # 第1轮：系统提示
    {"role": "user", "content": "初始系统提示"},
    # 第1轮响应
    {"role": "assistant", "content": "第1轮模型输出"},
    # 第2轮响应
    {"role": "assistant", "content": "第2轮模型输出"},
    # 第3轮响应
    {"role": "assistant", "content": "第3轮模型输出"},
    # 第4轮：用户上传第4轮截图
    {"role": "user", "content": [{"type": "image_url", "image_url": "..."}]},
    # 第4轮响应
    {"role": "assistant", "content": "第4轮模型输出"},
    # ... 最多保留5轮截图对应的消息 ...
    # 第7轮：用户上传第4轮截图
    {"role": "user", "content": [{"type": "image_url", "image_url": "..."}]},
    # 第7轮响应
    {"role": "assistant", "content": "第7轮模型输出"},
    # 第8轮：用户上传第N张截图
    {"role": "user", "content": [{"type": "image_url", "image_url": "..."}]},
]
```

示例代码
```Python
import os
# 通过 pip install volcengine-python-sdk[ark] 安装方舟SDK
from volcenginesdkarkruntime import Ark
import base64
from prompt import COMPUTER_USE_DOUBAO

# 初始化Ark客户端，从环境变量中读取您的API Key
client = Ark(
    api_key=os.getenv('ARK_API_KEY'),
    )

# 图片转 Base64 工具函数
def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

instruction = "Could you help me set the image to Palette-Based?"
language = "Chinese"
system_prompt = COMPUTER_USE_DOUBAO.format(instruction=instruction, language=language)

image_4turn_path = "samples/image_4_turn.png"
image_5turn_path = "samples/image_5_turn.png"
image_6turn_path = "samples/image_6_turn.png"
image_7turn_path = "samples/image_7_turn.png"
image_8turn_path = "samples/image_8_turn.png"

base64_image_4turn = encode_image(image_4turn_path)
base64_image_5turn = encode_image(image_5turn_path)
base64_image_6turn = encode_image(image_6turn_path)
base64_image_7turn = encode_image(image_7turn_path)
base64_image_8turn = encode_image(image_8turn_path)
image_format = image_path.split('.')[-1]
assert image_format in ['jpg', 'jpeg', 'png', 'webp']

messages = [
    {
        "role": "user",
        "content": system_prompt
    },
    {
        "role": "assistant",
        "content": "Thought: 我看到屏幕上弹出了一个颜色配置文件转换的对话框，要继续操作的话得先处理掉它。对话框右下角有个\"Convert\"按钮，我需要点击它来确认这个转换操作。\nAction: click(point='<point>607 647</point>')"
    },
    {
        "role": "assistant",
        "content": "Thought: 看到这张复古电视机的照片，我需要把它设置成基于调色板的方式。让我先点击顶部菜单栏的\"Tools\"选项，这样就能找到相关的颜色设置选项了。\nAction: click(point='<point>220 71</point>')"
    },
    {
        "role": "assistant",
        "content": "Thought: 刚才点开了Tools菜单，但发现这不是正确的路径。要设置图片为基于调色板的方式，我需要先关闭当前打开的Tools菜单，然后重新寻找正确的颜色设置选项。让我点击一下Tools按钮把它关掉。\nAction: click(point='<point>220 71</point>')"
    },
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{image_format};base64,{base64_image_4turn}"
                }
            }
        ]
    },
    {
        "role": "assistant",
        "content": "Thought: 刚才在Tools菜单里没找到想要的选项，让我换个思路。我注意到顶部菜单栏有个\"Colors\"选项，这应该就是处理颜色设置的地方。我需要点击它来继续寻找将图片设置为基于调色板方式的选项。\nAction: click(point='<point>192 71</point>')"
    },
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{image_format};base64,{base64_image_5turn}"
                }
            }
        ]
    },
    {
        "role": "assistant",
        "content": "Thought: 我在Colors菜单里仔细浏览了一遍，发现这里并没有直接设置调色板的选项。看来得换个思路了 - 先把这个菜单关掉，然后去Edit菜单看看，那里应该能找到更多关于图像处理的选项。毕竟要实现基于调色板的设置，可能需要通过其他路径来实现。\nAction: click(point='<point>192 71</point>')"
    },
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{image_format};base64,{base64_image_6turn}"
                }
            }
        ]
    },
    {
        "role": "assistant",
        "content": "Thought: 我在Colors菜单里没找到想要的选项，让我换个思路。我注意到顶部菜单栏有个\"Edit\"选项，这应该就是处理颜色设置的地方。我需要点击它来继续寻找将图片设置为基于调色板方式的选项。\nAction: click(point='<point>65 71</point>')"
    },
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{image_format};base64,{base64_image_7turn}"
                }
            }
        ]
    },
    {
        "role": "assistant",
        "content": "Thought: 我在Edit菜单里发现了Preferences选项，这正是我需要的。通过这个选项，我应该能找到调整图片颜色模式的设置。让我点击它进入设置界面，这样就能把图片转换成基于调色板的方式了。\nAction: click(point='<point>96 602</point>')"
    },
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{image_format};base64,{base64_image_8turn}"
                }
            }
        ]
    }
]

response = inference(messages)
print(response)
```


<span id="a54aac62"></span>
## 响应解析与执行
模型输出的`Action`包含GUI操作类型（如`click`/`type`）和坐标，需： 

* 用正则或工具类（如[parse_action_to_structure_output](https://github.com/bytedance/UI-TARS/blob/main/codes/ui_tars/action_parser.py)）提取坐标。 
* 转换 相对坐标 → 绝对像素坐标（需已知截图原始分辨率）。 
* 调用自动化工具（如PyAutoGUI）执行操作： 

```Python
import pyautogui
from ui_tars.action_parser import parse_action_to_structure_output, parsing_response_to_pyautogui_code

# 解析模型输出为坐标字典
parsed_dict = parse_action_to_structure_output(response, image_width, image_height, model_type="doubao")
# 转换为PyAutoGUI可执行代码
py_code = parsing_response_to_pyautogui_code(parsed_dict, image_height, image_width)
print(py_code)  # 输出：pyautogui.click(x=450, y=417)
```

<span id="612dbea7"></span>
## **环境一致性**

* 截图分辨率与实际操作界面一致（模型输出坐标基于输入图像尺寸）。若GUI界面分辨率与截图不一致，需按比例转换坐标（如截图分辨率1920×1080，实际界面2560×1440，则坐标×(2560/1920)）。
* 建议使用固定窗口布局（如最大化窗口）避免元素位置偏移。

<span id="bef6afe5"></span>
## 其他说明

* **多轮上下文管理**：最多保留5张截图（含当前），避免上下文过长导致混淆。 
* **系统提示精准性**：明确任务目标（如“点击右上角关闭按钮”）和操作环境（如“Windows系统资源管理器”）。 
* **动作验证**：通过可视化标记（如红色圆点）确认解析的坐标是否在目标控件上，避免误操作。 
* **模型推理随机性**：**temperature** 请设置为 `0` ，**top_p** 请设置为 `0.7`，无随机性的推理参数，以提高模型输出准确性。

<span id="b355e37f"></span>

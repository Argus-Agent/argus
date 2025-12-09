import PyInstaller.__main__
import shutil
import os
import customtkinter

# 获取 customtkinter 的库路径，用于添加数据文件
ctk_path = os.path.dirname(customtkinter.__file__)

print("Starting build process...")

# PyInstaller 参数
params = [
    'main.py',
    '--name=GUI_Agent',
    '--onefile',
    '--windowed',
    '--noconfirm',
    '--add-data', f'{ctk_path};customtkinter',  # 添加 customtkinter 的资源文件
    '--add-data', 'core;core',                  # 添加 core 模块
    '--hidden-import', 'PIL',
    '--hidden-import', 'win32gui',
    '--hidden-import', 'win32con',
    '--hidden-import', 'win32api',
    '--hidden-import', 'customtkinter',
    # 常用库的隐式依赖，防止打包遗漏
    '--hidden-import', 'litellm',
    '--hidden-import', 'tiktoken',
    '--hidden-import', 'pydantic',
]

# 执行打包
PyInstaller.__main__.run(params)

# # 复制 .env.example 到 dist 目录
# if os.path.exists('.env.example'):
#     dist_dir = os.path.join(os.getcwd(), 'dist')
#     if not os.path.exists(dist_dir):
#         os.makedirs(dist_dir)
    
#     shutil.copy('.env.example', os.path.join(dist_dir, '.env'))
#     print("Copied .env.example to dist/.env")

print("Build complete!")

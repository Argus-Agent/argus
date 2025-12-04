#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速运行Screen测试
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from test_screen import test_screenshot_and_display

if __name__ == "__main__":
    print("开始运行Screen模块快速测试...")
    test_screenshot_and_display()

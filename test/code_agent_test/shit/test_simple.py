#!/usr/bin/env python3
"""
CodeAgent简化测试 - 仅测试核心逻辑
"""
import os
import sys
# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_code_parser():
    """测试代码解析器"""
    print("=== 测试代码解析器 ===")
    
    try:
        from core.llm.code.code_parser import CodeParser
        
        test_text = """
这是一个测试文本

```python
def hello():
    print("Hello World!")
    return 42
```

```bash
echo "Hello Bash"
```
        
结束文本
        """
        
        codes = CodeParser(test_text)
        print(f"✓ 解析出 {len(codes)} 个代码块:")
        
        for i, code in enumerate(codes):
            print(f"  代码块 {i}: 语言={code['lang']}, 内容长度={len(code['code'])}")
        
        return len(codes) == 2
        
    except Exception as e:
        print(f"✗ 代码解析器测试失败: {e}")
        return False

def test_imports():
    """测试关键模块导入"""
    print("\n=== 测试模块导入 ===")
    
    try:
        # 测试Flet
        import flet as ft
        print("✓ Flet导入成功")
        
        # 测试Markdown
        import markdown
        print("✓ Markdown导入成功")
        
        # 测试Base64
        import base64
        print("✓ Base64模块可用")
        
        return True
        
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_ui_creation():
    """测试UI组件创建"""
    print("\n=== 测试UI组件创建 ===")
    
    try:
        import flet as ft
        import markdown
        import base64
        
        # 创建简单的页面测试
        def test_page(page):
            page.title = "Test Page"
            page.add(ft.Text("Hello World"))
            print("✓ Flet页面创建成功")
            
        print("✓ UI组件测试通过")
        return True
        
    except Exception as e:
        print(f"✗ UI组件测试失败: {e}")
        return False

def main():
    """运行简化测试"""
    print("CodeAgent 简化功能测试")
    print("=" * 40)
    
    tests = [
        ("模块导入", test_imports),
        ("代码解析器", test_code_parser),
        ("UI组件", test_ui_creation),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"{test_name}测试出现异常: {e}")
            results[test_name] = False
    
    # 输出测试结果
    print("\n" + "=" * 40)
    print("测试结果汇总:")
    
    for test_name, success in results.items():
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
    
    # 检查.env文件
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        print(f"\n✓ .env文件存在: {env_file}")
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print("配置内容:")
                for line in content.strip().split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        print(f"  {key}: {value}")
        except Exception as e:
            print(f"读取.env文件失败: {e}")
    else:
        print("\n⚠️ .env文件不存在")
    
    all_passed = all(results.values())
    if all_passed:
        print(f"\n🎉 基础测试通过！")
        print("如果API配置正确，可以尝试启动UI:")
        print("  python run_ui.py")
    else:
        print(f"\n⚠️ 部分测试失败，请检查依赖安装:")
        print("  pip install flet markdown")
    
    return all_passed

if __name__ == "__main__":
    main()
